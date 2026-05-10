"""
backend/pdf_to_ppt/app.py
------------------------------------------------
Reusable Streamlit PPT Generator Module

This file keeps ALL original functionality intact.
Only wrapped inside a reusable function so it can
be called from main.py inside tab6.
"""

from __future__ import annotations

import os
import time
from pathlib import Path

import streamlit as st

from backend.pdf_to_ppt.modules.pdf_extractor import extract_pdf

from backend.pdf_to_ppt.modules.rag_retriever import RAGRetriever

from backend.pdf_to_ppt.modules.summarizer import (
    summarize_sections,
    summarize_text,
    build_intro,
    build_conclusion,
)

from backend.pdf_to_ppt.modules.image_handler import (
    save_pdf_images,
    get_image_for_slide,
    fetch_unsplash_image,
)

from backend.pdf_to_ppt.modules.ppt_generator import (
    generate_presentation
)


# ============================================================
# MAIN FUNCTION
# ============================================================

def render_ppt_generator():

    # ============================================================
    # CSS
    # ============================================================

    st.markdown(
        """
        <style>

        .ppt-container {
            background: rgba(255,255,255,0.04);
            padding: 25px;
            border-radius: 24px;
            border: 1px solid rgba(255,255,255,0.08);
            backdrop-filter: blur(12px);
        }

        .ppt-title {
            font-size: 42px;
            font-weight: 800;
            background: linear-gradient(90deg,#60a5fa,#c084fc);
            -webkit-background-clip: text;
            
        }

        .ppt-subtitle {
            color: #cbd5e1;
            font-size: 16px;
            margin-top: 8px;
        }

        </style>
        """,
        unsafe_allow_html=True,
    )

    # ============================================================
    # HEADER
    # ============================================================

    st.markdown(
        """
        <div class="ppt-container">

        <div class="ppt-title">
            📊 AI Presentation Generator
        </div>

        <div class="ppt-subtitle">
            Generate enterprise-grade PowerPoint presentations
            using Retrieval-Augmented Generation (RAG),
            FAISS retrieval, summarization, and AI slide generation.
        </div>

        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("<br>", unsafe_allow_html=True)

    # ============================================================
    # SETTINGS
    # ============================================================

    left, right = st.columns([1.2, 1])

    with left:

        st.subheader("📂 Upload PDF")

        uploaded_pdf = st.file_uploader(
            "Upload PDF",
            type=["pdf"],
            accept_multiple_files=False,
            key="pdf_uploader"
        )

        topic = st.text_input(
            "🎯 Topic from the PDF",
            placeholder="e.g. Machine Learning",
            key="topic_input",
        )

        st.markdown("<br>", unsafe_allow_html=True)

        

        go = st.button(
            "🚀 Generate Presentation",
            type="primary",
            key="generate_btn",
            use_container_width=True
        )

    # ============================================================
    # RIGHT SIDE
    # ============================================================

    with right:
        
        st.subheader("⚙️ PPT Settings")

        bullets_per_section = st.slider(
            "Bullets per slide",
            3,
            7,
            5,
            key="bullets_slider"
        )

        min_slides = st.slider(
            "Min slides",
            5,
            10,
            6,
            key="min_slides"
        )

        max_slides = st.slider(
            "Max slides",
            min_slides,
            15,
            max(min_slides, 10),
            key="max_slides"
        )

        use_web_images = st.checkbox(
            "Fetch web images when PDF has none",
            value=True,
            key="use_web"
        )

        top_k_chunks = st.slider(
            "RAG top-k chunks",
            10,
            40,
            20,
            key="top_k"
        )

        st.markdown("<br>", unsafe_allow_html=True)

        



       
        
    # ============================================================
    # PIPELINE
    # ============================================================

    def _run_pipeline(pdf_bytes: bytes, user_topic: str) -> str:

        out_dir = (
            Path(__file__).parent / "output"
        )

        out_dir.mkdir(exist_ok=True)

        progress = st.progress(0, text="Starting...")

        # ============================================================
        # 1. EXTRACT
        # ============================================================

        progress.progress(
            10,
            text="Extracting text and images from PDF..."
        )

        extracted = extract_pdf(pdf_bytes)

        if not extracted["pages"]:
            raise RuntimeError(
                "Could not extract any readable content from this PDF."
            )

        st.success(
            f"Extracted {len(extracted['pages'])} content pages, "
            f"{len(extracted['outline'])} headings, "
            f"{len(extracted['images'])} images."
        )

        # ============================================================
        # 2. BUILD RETRIEVER
        # ============================================================

        progress.progress(
            30,
            text="Building embeddings + FAISS index..."
        )

        retriever = RAGRetriever()

        n_chunks = retriever.build(
            extracted["pages"],
            extracted["outline"]
        )

        if n_chunks == 0:
            raise RuntimeError(
                "No text chunks could be built for retrieval."
            )

        # ============================================================
        # 3. RETRIEVE
        # ============================================================

        progress.progress(
            55,
            text=f"Retrieving content for topic: {user_topic}..."
        )

        grouped = retriever.retrieve_by_section(
            user_topic,
            top_k=top_k_chunks
        )

        if not grouped:

            loose = retriever.retrieve(
                user_topic,
                top_k=top_k_chunks,
                min_score=0.0
            )

            if loose:

                grouped = {}

                for h in loose:
                    grouped.setdefault(
                        h["section"],
                        []
                    ).append(h)

        if not grouped:
            raise RuntimeError(
                f"No relevant content found for '{user_topic}'. "
                "Try a broader topic name."
            )

        # ============================================================
        # 4. SUMMARIZE
        # ============================================================

        progress.progress(
            70,
            text="Summarizing topic-wise..."
        )

        section_bullets = summarize_sections(
            grouped,
            bullets_per_section=bullets_per_section
        )

        all_text = " ".join(
            c["text"]
            for chunks in grouped.values()
            for c in chunks
        )

        overall_bullets = summarize_text(
            all_text,
            max_bullets=4
        )

        intro = build_intro(
            user_topic,
            overall_bullets
        )

        conclusion = build_conclusion(
            user_topic,
            section_bullets
        )

        # ============================================================
        # 5. IMAGES
        # ============================================================

        progress.progress(
            82,
            text="Collecting images..."
        )

        pdf_images = save_pdf_images(
            extracted["images"]
        )

        used_paths: set = set()

        section_images: dict = {}

        if use_web_images or not pdf_images:

            p_intro = get_image_for_slide(
                user_topic,
                pdf_images,
                used_paths=used_paths
            )

            if p_intro:
                section_images["__intro__"] = p_intro

            p_concl = (
                fetch_unsplash_image(
                    f"{user_topic} learning"
                )
                if use_web_images else None
            )

            if p_concl:
                section_images["__conclusion__"] = p_concl

        for section in section_bullets.keys():

            query = f"{section} {user_topic}"

            path = None

            if pdf_images:
                path = get_image_for_slide(
                    query,
                    pdf_images,
                    used_paths=used_paths
                )

            if not path and use_web_images:
                path = fetch_unsplash_image(query)

            if path:
                section_images[section] = path

        # ============================================================
        # 6. GENERATE PPT
        # ============================================================

        progress.progress(
            92,
            text="Building PowerPoint..."
        )

        safe_name = "".join(
            c if c.isalnum() else "_"
            for c in user_topic
        ).strip("_") or "topic"

        output_path = str(
            out_dir /
            f"{safe_name}_{int(time.time())}.pptx"
        )

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

        progress.progress(
            100,
            text="Done!"
        )

        return output_path

    # ============================================================
    # GENERATE BUTTON LOGIC
    # ============================================================

    if go:

        if not uploaded_pdf:
            st.error("Please upload a PDF first.")

        elif not topic.strip():
            st.error("Please enter the topic name.")

        else:
            try:

                with st.spinner(
                    "Running the RAG pipeline..."
                ):

                    pdf_bytes = uploaded_pdf.read()

                    pptx_path = _run_pipeline(
                        pdf_bytes,
                        topic.strip()
                    )

                st.success(
                    "Presentation generated!"
                )

                with open(pptx_path, "rb") as f:

                    st.download_button(
                        label="⬇️ Download PPTX",
                        data=f.read(),
                        file_name=os.path.basename(pptx_path),
                        mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                        key="download_btn",
                    )

                st.info(
                    f"Saved locally to: `{pptx_path}`"
                )

            except Exception as e:
                st.exception(e)

    st.markdown("---")

    st.caption(
        "The `/modules` folder is reusable across projects."
    )