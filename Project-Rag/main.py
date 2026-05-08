# ============================================================
# IMPORTS
# ============================================================

import streamlit as st

# PDF RAG
from backend.pdf_rag.app import render_document_rag

# PPT GENERATOR
from backend.pdf_to_ppt.app import render_ppt_generator

from backend.yt_rag.app import render_youtube_rag
from backend.audio_to_chat.app import render_audio_rag


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Enterprise RAG AI Platform",
    page_icon="🚀",
    layout="wide"
)


# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown(
    """
    <style>

    .stApp{
        background: linear-gradient(
            135deg,
            #0f172a,
            #111827,
            #1e293b
        );

        color:white;
    }

    /* FIXED TABS */
    .stTabs{
        position: sticky;
        top: 0;
        z-index: 999;
        background: #0f172a;
        padding-top: 6px;
        padding-bottom: 6px;
    }

    .stTabs [data-baseweb="tab-list"]{
        gap: 12px;
    }

    .stTabs [data-baseweb="tab"]{
        background: rgba(255,255,255,0.05);
        border-radius: 12px;
        padding: 10px 18px;
        color: white;
        font-weight: 600;
    }

    .stTabs [aria-selected="true"]{
        background: linear-gradient(
            135deg,
            #2563eb,
            #7c3aed
        );
    }

    </style>
    """,
    unsafe_allow_html=True
)


# ============================================================
# HEADER
# ============================================================

st.markdown(
    """
    <div style="
        padding:30px;
        border-radius:24px;
        background:rgba(255,255,255,0.04);
        border:1px solid rgba(255,255,255,0.08);
        margin-bottom:20px;
    ">

    <h1 style="
        font-size:48px;
        font-weight:800;
        background: linear-gradient(90deg,#60a5fa,#c084fc);
        -webkit-background-clip:text;
        -webkit-text-fill-color:transparent;
        margin-bottom:10px;
    ">
        🚀 Enterprise Multi-Modal RAG Platform
    </h1>

    <p style="
        color:#cbd5e1;
        font-size:18px;
    ">
        AI-powered PDF Q&A, YouTube Q&A, Audio Intelligence,
        Document Search, and AI Presentation Generation Platform.
    </p>

    </div>
    """,
    unsafe_allow_html=True
)


# ============================================================
# TABS
# ============================================================

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "💬 AI Chat",
    "📄 PDF Q&A",
    "🎥 YouTube Q&A",
    "🎤 Audio Q&A",
    "📁 Documents",
    "📊 PPT Generator"
])


# ============================================================
# TAB 1 - AI CHAT
# ============================================================

with tab1:

    st.subheader("💬 AI Chat Assistant")

    st.info("General AI chatbot workspace")


# ============================================================
# TAB 2 - PDF RAG
# ============================================================

with tab2:

    render_document_rag()


# ============================================================
# TAB 3 - YOUTUBE
# ============================================================

with tab3:

    
    render_youtube_rag()


# ============================================================
# TAB 4 - AUDIO
# ============================================================

with tab4:

    st.subheader("🎤 Audio File Q&A")

    st.info("Audio transcription + RAG module")
    render_audio_rag()


# ============================================================
# TAB 5 - DOCUMENTS
# ============================================================

with tab5:

    st.subheader("📁 Document Workspace")

    st.info("Multi-document management system")


# ============================================================
# TAB 6 - PPT GENERATOR
# ============================================================

with tab6:

    render_ppt_generator()


# ============================================================
# FOOTER
# ============================================================

st.markdown("---")

st.caption(
    "Enterprise AI Platform • Multi-Modal RAG • NVIDIA AI • FAISS • Streamlit"
)