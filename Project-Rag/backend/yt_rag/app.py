"""
backend/yt_rag/app.py
----------------------------------------------------
Professional YouTube RAG Streamlit Module
with Persistent Chat History
"""

from __future__ import annotations

import streamlit as st

from backend.yt_rag.modules.yt_rag import (
    extract_video_id,
    get_transcript,
    build_vector_store,
    ask_video,
)


# ============================================================
# MAIN FUNCTION
# ============================================================

def render_youtube_rag():

    # ============================================================
    # SESSION STATE
    # ============================================================

    if "yt_chat_history" not in st.session_state:
        st.session_state.yt_chat_history = []

    if "yt_vector_db" not in st.session_state:
        st.session_state.yt_vector_db = None

    if "yt_video_loaded" not in st.session_state:
        st.session_state.yt_video_loaded = False

    # ============================================================
    # CSS
    # ============================================================

    st.markdown(
        """
        <style>

        .yt-container{
            background: rgba(255,255,255,0.04);
            padding: 28px;
            border-radius: 24px;
            border: 1px solid rgba(255,255,255,0.08);
            backdrop-filter: blur(12px);
        }

        .yt-title{
            font-size:42px;
            font-weight:800;
            background: linear-gradient(
                90deg,
                #ef4444,
                #f97316
            );

            -webkit-background-clip:text;
            
        }

        .yt-subtitle{
            color:#cbd5e1;
            margin-top:10px;
            font-size:16px;
        }

        .chat-user{
            background:#dc2626;
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
        <div class="yt-container">

        <div class="yt-title">
            🎥 YouTube Transcript RAG Assistant
        </div>

        <div class="yt-subtitle">
            Ask intelligent questions from YouTube videos using
            transcript retrieval, NVIDIA embeddings,
            FAISS semantic search, and AI-powered responses.
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

        st.subheader("🔗 YouTube Video")

        youtube_url = st.text_input(
            "Paste YouTube URL",
            placeholder="https://www.youtube.com/watch?v=...",
            key="youtube_url"
        )

        st.markdown("<br>", unsafe_allow_html=True)

        load_btn = st.button(
            "📥 Load Transcript",
            use_container_width=True,
            key="load_yt"
        )

        st.markdown("<br>", unsafe_allow_html=True)

        st.subheader("🔍 Ask Questions")

        query = st.text_input(
            "Ask anything from the video",
            placeholder="What is the main topic discussed?",
            key="yt_query"
        )

        st.markdown("<br>", unsafe_allow_html=True)

        b1, b2 = st.columns([4, 1])

        with b1:

            ask_btn = st.button(
                "🚀 Ask AI",
                type="primary",
                use_container_width=True,
                key="yt_ask"
            )

        with b2:

            clear_btn = st.button(
                "🗑️ Clear",
                use_container_width=True,
                key="yt_clear"
            )

    # ============================================================
    # RIGHT
    # ============================================================

    with right:

        st.subheader("🧠 Pipeline")

        st.markdown(
            """
            ✅ Extract YouTube Transcript\t            ✅ Recursive Chunking

            ✅ NVIDIA Embeddings\t \t\t            ✅ FAISS Semantic Search

            ✅ Context Retrieval\t \t            ✅ AI Answer Generation
            """
        )

        st.markdown("<br>", unsafe_allow_html=True)

        st.subheader("⚡ Features")

        st.markdown(
            """
            🔹 Video Transcript Q&A            🔹 Semantic Video Search

            🔹 AI Video Understanding            🔹 Context-Aware Responses

            🔹 Fast Retrieval Pipeline            🔹 Persistent Chat History
            """
        )

    # ============================================================
    # LOAD VIDEO
    # ============================================================

    if load_btn:

        if not youtube_url.strip():

            st.error("Please enter a YouTube URL.")

        else:

            try:

                with st.spinner(
                    "Fetching transcript and building vector database..."
                ):

                    video_id = extract_video_id(
                        youtube_url
                    )

                    if not video_id:
                        raise ValueError(
                            "Invalid YouTube URL"
                        )

                    transcript = get_transcript(
                        video_id
                    )

                    if not transcript:
                        raise RuntimeError(
                            "Transcript unavailable for this video."
                        )

                    db = build_vector_store(
                        transcript
                    )

                    st.session_state.yt_vector_db = db
                    st.session_state.yt_video_loaded = True

                st.success(
                    "Transcript loaded successfully!"
                )

                st.video(youtube_url)

            except Exception as e:
                st.exception(e)

    # ============================================================
    # CLEAR CHAT
    # ============================================================

    if clear_btn:
        st.session_state.yt_chat_history = []
        st.rerun()

    # ============================================================
    # ASK QUESTION
    # ============================================================

    if ask_btn:

        if not st.session_state.yt_video_loaded:

            st.error(
                "Please load a YouTube transcript first."
            )

        elif not query.strip():

            st.error(
                "Please enter a question."
            )

        else:

            try:

                with st.spinner(
                    "Retrieving transcript context..."
                ):

                    answer, docs = ask_video(
                        st.session_state.yt_vector_db,
                        query
                    )

                # ============================================================
                # SAVE CHAT HISTORY
                # ============================================================

                st.session_state.yt_chat_history.append({

                    "question": query,
                    "answer": answer,
                    "docs": docs

                })

            except Exception as e:
                st.exception(e)

    # ============================================================
    # CHAT HISTORY
    # ============================================================

    if st.session_state.yt_chat_history:

        st.markdown("<br>", unsafe_allow_html=True)

        st.subheader("💬 Chat History")

    for idx, chat in enumerate(
        st.session_state.yt_chat_history
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
            f"📚 Transcript Context #{idx+1}"
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
        "Powered by NVIDIA AI, LangChain, FAISS, and YouTube Transcript API."
    )