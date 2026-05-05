"""
app.py
------
Streamlit entry point for the PDF → Topic-Focused PPT RAG pipeline.

Run locally:
    pip install -r requirements.txt
    streamlit run app.py

The modules under ./modules/ are fully self-contained and can be dropped into
any other Streamlit project. Each module documents its own public API.
"""

from __future__ import annotations

import os
import time
from pathlib import Path

import streamlit as st

from modules.pdf_extractor import extract_pdf
from modules.rag_retriever import RAGRetriever
from modules.summarizer import (
    summarize_sections,
    summarize_text,
    build_intro,
    build_conclusion,
)
from modules.image_handler import (
    save_pdf_images,
    get_image_for_slide,
    fetch_unsplash_image,
)
from modules.ppt_generator import generate_presentation


# ------------------------------ Streamlit UI -------------------------------- #

st.set_page_config(
    page_title="PDF → Professional PPT (RAG)",
    page_icon="📘",
    layout="wide",
)

# Lightweight cream-themed CSS for the Streamlit page itself (matches PPT vibe)
st.markdown(
    """
    <style>
      .main, .block-container { background-color: #FFF8E7 !important; }
      h1, h2, h3 { color: #CC7722 !important; font-family: Georgia, serif; }
      .stButton>button {
          background-color: #CC7722; color: white; border: none; border-radius: 6px;
          padding: 0.55rem 1.1rem; font-weight: 600;
      }
      .stButton>button:hover { background-color: #B36A1E; color: white; }
      .stDownloadButton>button {
          background-color: #5B3A1E; color: #FFF8E7; border-radius: 6px;
          padding: 0.55rem 1.2rem; font-weight: 600;
      }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("📘 PDF → Professional PPT")
st.caption(
    "Upload any subject PDF, enter a topic, and generate a classroom-ready "
    "presentation using a local RAG pipeline (no LLM API key required)."
)

with st.sidebar:
    st.header("⚙️ Settings")
    bullets_per_section = st.slider("Bullets per slide", 3, 7, 5, key="bullets_slider")
    min_slides = st.slider("Min slides", 5, 10, 6, key="min_slides")
    max_slides = st.slider("Max slides", min_slides, 15, max(min_slides, 10), key="max_slides")
    use_web_images = st.checkbox(
        "Fetch web images when PDF has none", value=True, key="use_web"
    )
    top_k_chunks = st.slider("RAG top-k chunks", 10, 40, 20, key="top_k")
    st.markdown("---")
    st.markdown(
        "**Pipeline**\n\n"
        "1. Extract PDF text + images\n"
        "2. Filter TOC / headers / footers\n"
        "3. Chunk & embed (MiniLM)\n"
        "4. Retrieve via FAISS\n"
        "5. Summarize (LexRank)\n"
        "6. Build PPT (cream + orange)"
    )


col1, col2 = st.columns([2, 1])
with col1:
    uploaded_pdf = st.file_uploader(
        "Upload PDF", type=["pdf"], accept_multiple_files=False, key="pdf_uploader"
    )
with col2:
    topic = st.text_input(
        "Topic from the PDF",
        placeholder="e.g. Machine Learning, Photosynthesis, DBMS Normalization",
        key="topic_input",
    )

go = st.button("🚀 Generate Presentation", type="primary", key="generate_btn", use_container_width=True)


# ------------------------------ Pipeline ----------------------------------- #

def _run_pipeline(pdf_bytes: bytes, user_topic: str) -> str:
    out_dir = Path(__file__).parent / "output"
    out_dir.mkdir(exist_ok=True)

    progress = st.progress(0, text="Starting...")

    # 1. Extract
    progress.progress(10, text="Extracting text and images from PDF...")
    extracted = extract_pdf(pdf_bytes)
    if not extracted["pages"]:
        raise RuntimeError("Could not extract any readable content from this PDF.")

    st.success(
        f"Extracted {len(extracted['pages'])} content pages, "
        f"{len(extracted['outline'])} headings, "
        f"{len(extracted['images'])} images."
    )

    # 2. Build retriever
    progress.progress(30, text="Building embeddings + FAISS index...")
    retriever = RAGRetriever()
    n_chunks = retriever.build(extracted["pages"], extracted["outline"])
    if n_chunks == 0:
        raise RuntimeError("No text chunks could be built for retrieval.")

    # 3. Retrieve per section
    progress.progress(55, text=f"Retrieving content for topic: {user_topic}...")
    grouped = retriever.retrieve_by_section(user_topic, top_k=top_k_chunks)
    if not grouped:
        # Very permissive retry with a lower threshold via a plain retrieve
        loose = retriever.retrieve(user_topic, top_k=top_k_chunks, min_score=0.0)
        if loose:
            grouped = {}
            for h in loose:
                grouped.setdefault(h["section"], []).append(h)
    if not grouped:
        raise RuntimeError(
            f"No relevant content found for '{user_topic}'. "
            "Try a broader topic name that appears in the PDF."
        )

    # 4. Summarize
    progress.progress(70, text="Summarizing topic-wise and subsection-wise...")
    section_bullets = summarize_sections(grouped, bullets_per_section=bullets_per_section)

    # Build intro / conclusion
    all_text = " ".join(c["text"] for chunks in grouped.values() for c in chunks)
    overall_bullets = summarize_text(all_text, max_bullets=4)
    intro = build_intro(user_topic, overall_bullets)
    conclusion = build_conclusion(user_topic, section_bullets)

    # 5. Images per section
    progress.progress(82, text="Collecting images...")
    pdf_images = save_pdf_images(extracted["images"])
    used_paths: set = set()
    section_images: dict = {}

    if use_web_images or not pdf_images:
        # Intro + conclusion get web images tied to the main topic.
        p_intro = get_image_for_slide(user_topic, pdf_images, used_paths=used_paths)
        if p_intro:
            section_images["__intro__"] = p_intro
        p_concl = fetch_unsplash_image(f"{user_topic} learning") if use_web_images else None
        if p_concl:
            section_images["__conclusion__"] = p_concl

    for section in section_bullets.keys():
        query = f"{section} {user_topic}"
        path = None
        if pdf_images:
            path = get_image_for_slide(query, pdf_images, used_paths=used_paths)
        if not path and use_web_images:
            path = fetch_unsplash_image(query)
        if path:
            section_images[section] = path

    # 6. Generate PPT
    progress.progress(92, text="Building PowerPoint...")
    safe_name = "".join(c if c.isalnum() else "_" for c in user_topic).strip("_") or "topic"
    output_path = str(out_dir / f"{safe_name}_{int(time.time())}.pptx")

    generate_presentation(
        topic=user_topic,
        intro_bullets=intro,
        section_bullets=section_bullets,
        conclusion_bullets=conclusion,
        section_images=section_images,
        output_path=output_path,
        min_slides=min_slides,
        max_slides=max_slides,
    )

    progress.progress(100, text="Done!")
    return output_path


if go:
    if not uploaded_pdf:
        st.error("Please upload a PDF first.")
    elif not topic.strip():
        st.error("Please enter the topic name.")
    else:
        try:
            with st.spinner("Running the RAG pipeline..."):
                pdf_bytes = uploaded_pdf.read()
                pptx_path = _run_pipeline(pdf_bytes, topic.strip())

            st.success("Presentation generated!")
            with open(pptx_path, "rb") as f:
                st.download_button(
                    label="⬇️ Download PPTX",
                    data=f.read(),
                    file_name=os.path.basename(pptx_path),
                    mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                    key="download_btn",
                )
            st.info(f"Saved locally to: `{pptx_path}`")

        except Exception as e:
            st.exception(e)


st.markdown("---")
st.caption(
    "Tip: the `/modules` folder is drop-in compatible with other Streamlit apps. "
    "Each module has its own docstring describing the public API."
)


