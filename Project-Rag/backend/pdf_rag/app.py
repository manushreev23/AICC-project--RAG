"""
backend/document_rag/app.py
----------------------------------------------------
Professional Multi-Document RAG Assistant

Supported Files:
- PDF
- DOCX
- TXT
- PPT / PPTX
"""

from __future__ import annotations

import os
import tempfile
import streamlit as st

from backend.pdf_rag.modules.pdf import (
    build_vector_store,
    ask_pdf,
)


# ============================================================
# MAIN FUNCTION
# ============================================================

def render_document_rag():

    # ============================================================
    # SESSION STATE
    # ============================================================

    if "doc_chat_history" not in st.session_state:
        st.session_state.doc_chat_history = []

    if "doc_vectorstore" not in st.session_state:
        st.session_state.doc_vectorstore = None

    if "doc_loaded" not in st.session_state:
        st.session_state.doc_loaded = False

    if "doc_name" not in st.session_state:
        st.session_state.doc_name = ""

    # ============================================================
    # CSS
    # ============================================================

    st.markdown(
        """
        <style>

        .doc-container{
            background: rgba(255,255,255,0.04);
            padding: 28px;
            border-radius: 24px;
            border: 1px solid rgba(255,255,255,0.08);
            backdrop-filter: blur(12px);
        }

        .doc-title{
            font-size:42px;
            font-weight:800;
            background: linear-gradient(
                90deg,
                #22c55e,
                #14b8a6
            );

            -webkit-background-clip:text;
            -webkit-text-fill-color:transparent;
        }

        .doc-subtitle{
            color:#cbd5e1;
            margin-top:10px;
            font-size:16px;
        }

        .chat-user{
            background:#16a34a;
            padding:14px;
            border-radius:14px;
            margin-top:16px;
            color:white;
        }

        .chat-bot{
            background:rgba(255,255,255,0.05);
            padding:16px;
            border-radius:14px;
            margin-top:10px;
            border:1px solid rgba(255,255,255,0.08);
            color:white;
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
        <div class="doc-container">

        <div class="doc-title">
            📁 Enterprise Document RAG Assistant
        </div>

        <div class="doc-subtitle">
            Upload documents and interact intelligently using
            NVIDIA AI, FAISS vector search,
            semantic embeddings, and Retrieval-Augmented Generation.
        </div>

        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("<br>", unsafe_allow_html=True)

    # ============================================================
    # LAYOUT
    # ============================================================

    left, right = st.columns([1.2, 1])

    # ============================================================
    # LEFT
    # ============================================================

    with left:

        st.subheader("📂 Upload Document")

        uploaded_file = st.file_uploader(
            "Supported: PDF, DOCX, TXT, PPT, PPTX",
            type=["pdf", "docx", "txt", "ppt", "pptx"],
            accept_multiple_files=False,
            key="doc_upload"
        )

        st.markdown("<br>", unsafe_allow_html=True)

        process_btn = st.button(
            "⚡ Process Document",
            use_container_width=True,
            key="process_doc"
        )

        st.markdown("<br>", unsafe_allow_html=True)

        st.subheader("🔍 Ask Questions")

        question = st.text_input(
            "Ask anything from the document",
            placeholder="Explain the architecture discussed...",
            key="doc_question"
        )

        st.markdown("<br>", unsafe_allow_html=True)

        b1, b2 = st.columns([4, 1])

        with b1:

            ask_btn = st.button(
                "🚀 Ask AI",
                type="primary",
                use_container_width=True,
                key="doc_ask"
            )

        with b2:

            clear_btn = st.button(
                "🗑️ Clear",
                use_container_width=True,
                key="doc_clear"
            )

    # ============================================================
    # RIGHT
    # ============================================================

    with right:

        st.subheader("🧠 Pipeline")

        st.markdown(
            """
            ✅ Multi-Document Parsing            ✅ Recursive Chunking

            ✅ NVIDIA Embeddings            ✅ FAISS Vector Store

            ✅ Semantic Retrieval            ✅ NVIDIA AI Responses
            """
        )

        st.markdown("<br>", unsafe_allow_html=True)

        st.subheader("⚡ Supported Formats")

        st.markdown(
            """
            📄 PDF Documents            📝 DOCX Files

            📃 TXT Files            📊 PPT / PPTX Files

            🔍 Semantic Search            💬 Persistent Chat
            """
        )

    # ============================================================
    # PROCESS DOCUMENT
    # ============================================================

    if process_btn:

        if not uploaded_file:

            st.error(
                "Please upload a document."
            )

        else:

            try:

                with st.spinner(
                    "Processing document..."
                ):

                    # ============================================================
                    # SAVE TEMP FILE
                    # ============================================================

                    suffix = os.path.splitext(
                        uploaded_file.name
                    )[1]

                    with tempfile.NamedTemporaryFile(
                        delete=False,
                        suffix=suffix
                    ) as tmp_file:

                        tmp_file.write(
                            uploaded_file.read()
                        )

                        temp_path = tmp_file.name

                    # ============================================================
                    # BUILD VECTORSTORE
                    # ============================================================

                    vectorstore = build_vector_store(
                        temp_path
                    )

                    st.session_state.doc_vectorstore = vectorstore
                    st.session_state.doc_loaded = True
                    st.session_state.doc_name = uploaded_file.name

                st.success(
                    "Document processed successfully!"
                )

            except Exception as e:
                st.exception(e)

    # ============================================================
    # CLEAR CHAT
    # ============================================================

    if clear_btn:

        st.session_state.doc_chat_history = []

        st.rerun()

    # ============================================================
    # SHOW FILE INFO
    # ============================================================

    if st.session_state.doc_loaded:

        st.info(
            f"Loaded Document: "
            f"{st.session_state.doc_name}"
        )

    # ============================================================
    # ASK QUESTIONS
    # ============================================================

    if ask_btn:

        if not st.session_state.doc_loaded:

            st.error(
                "Please process a document first."
            )

        elif not question.strip():

            st.error(
                "Please enter a question."
            )

        else:

            try:

                with st.spinner(
                    "Searching document..."
                ):

                    answer, docs = ask_pdf(
                        st.session_state.doc_vectorstore,
                        question
                    )

                # ============================================================
                # SAVE CHAT
                # ============================================================

                st.session_state.doc_chat_history.append({

                    "question": question,
                    "answer": answer,
                    "docs": docs

                })

            except Exception as e:
                st.exception(e)

    # ============================================================
    # DISPLAY CHAT HISTORY
    # ============================================================

    if st.session_state.doc_chat_history:

        st.markdown("<br>", unsafe_allow_html=True)

        st.subheader("💬 Chat History")

    for idx, chat in enumerate(
        st.session_state.doc_chat_history
    ):

        # ============================================================
        # USER
        # ============================================================

        st.markdown(
            f"""
            <div class="chat-user">
                <b>Question:</b><br><br>
                {chat["question"]}
            </div>
            """,
            unsafe_allow_html=True,
        )

        # ============================================================
        # BOT
        # ============================================================

        st.markdown(
            f"""
            <div class="chat-bot">
                <b>AI Answer:</b><br><br>
                {chat["answer"]}
            </div>
            """,
            unsafe_allow_html=True,
        )

        # ============================================================
        # SOURCES
        # ============================================================

        with st.expander(
            f"📚 Retrieved Context #{idx+1}"
        ):

            for i, doc in enumerate(chat["docs"]):

                st.markdown(
                    f"""
                    ### Chunk {i+1}

                    {doc.page_content[:1200]}
                    """
                )

    st.markdown("---")

    st.caption(
        "Powered by NVIDIA AI, LangChain, and FAISS."
    )