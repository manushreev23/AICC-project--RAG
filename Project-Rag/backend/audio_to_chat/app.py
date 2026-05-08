"""
backend/audio_to_chat/app.py
----------------------------------------------------
Professional Audio RAG Streamlit Module
with Persistent Chat History
"""

from __future__ import annotations

import os
import streamlit as st

from backend.audio_to_chat.modules.audio_to_chat import (
    save_uploaded_file,
    transcribe_audio,
    summarize_audio,
    create_vectorstore,
    audio_chat,
)


# ============================================================
# MAIN FUNCTION
# ============================================================

def render_audio_rag():

    # ============================================================
    # SESSION STATE
    # ============================================================

    if "audio_chat_history" not in st.session_state:
        st.session_state.audio_chat_history = []

    if "audio_vectorstore" not in st.session_state:
        st.session_state.audio_vectorstore = None

    if "audio_transcript" not in st.session_state:
        st.session_state.audio_transcript = ""

    if "audio_summary" not in st.session_state:
        st.session_state.audio_summary = ""

    if "audio_loaded" not in st.session_state:
        st.session_state.audio_loaded = False

    # ============================================================
    # CSS
    # ============================================================

    st.markdown(
        """
        <style>

        .audio-container{
            background: rgba(255,255,255,0.04);
            padding: 28px;
            border-radius: 24px;
            border: 1px solid rgba(255,255,255,0.08);
            backdrop-filter: blur(12px);
        }

        .audio-title{
            font-size:42px;
            font-weight:800;
            background: linear-gradient(
                90deg,
                #06b6d4,
                #8b5cf6
            );

            -webkit-background-clip:text;
            -webkit-text-fill-color:transparent;
        }

        .audio-subtitle{
            color:#cbd5e1;
            margin-top:10px;
            font-size:16px;
        }

        .chat-user{
            background:#0891b2;
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
        <div class="audio-container">

        <div class="audio-title">
            🎤 Audio Intelligence Assistant
        </div>

        <div class="audio-subtitle">
            Upload audio files and interact with them using
            Whisper transcription, FAISS vector retrieval,
            semantic embeddings, and AI-powered chat.
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
    # LEFT SIDE
    # ============================================================

    with left:

        st.subheader("🎵 Upload Audio")

        uploaded_audio = st.file_uploader(
            "Upload Audio File",
            type=["mp3", "wav", "m4a", "mp4"],
            accept_multiple_files=False,
            key="audio_upload"
        )

        st.markdown("<br>", unsafe_allow_html=True)

        process_btn = st.button(
            "⚡ Process Audio",
            use_container_width=True,
            key="process_audio"
        )

        st.markdown("<br>", unsafe_allow_html=True)

        st.subheader("🔍 Ask Questions")

        question = st.text_input(
            "Ask anything from the audio",
            placeholder="What are the main points discussed?",
            key="audio_question"
        )

        st.markdown("<br>", unsafe_allow_html=True)

        b1, b2 = st.columns([4, 1])

        with b1:

            ask_btn = st.button(
                "🚀 Ask AI",
                type="primary",
                use_container_width=True,
                key="audio_ask"
            )

        with b2:

            clear_btn = st.button(
                "🗑️ Clear",
                use_container_width=True,
                key="audio_clear"
            )

    # ============================================================
    # RIGHT SIDE
    # ============================================================

    with right:

        st.subheader("🧠 Pipeline")

        st.markdown(
            """
            ✅ Whisper Transcription

            ✅ Text Chunking

            ✅ Sentence Transformers

            ✅ FAISS Vector Search

            ✅ Ollama LLM Chat

            ✅ Context-Aware QA
            """
        )

        st.markdown("<br>", unsafe_allow_html=True)

        st.subheader("⚡ Features")

        st.markdown(
            """
            🔹 Audio Transcription

            🔹 AI Summarization

            🔹 Audio Q&A

            🔹 Semantic Search

            🔹 Persistent Chat History

            🔹 Local AI Processing
            """
        )

    # ============================================================
    # PROCESS AUDIO
    # ============================================================

    if process_btn:

        if not uploaded_audio:

            st.error(
                "Please upload an audio file."
            )

        else:

            try:

                with st.spinner(
                    "Processing audio..."
                ):

                    # ============================================================
                    # SAVE FILE
                    # ============================================================

                    audio_path = save_uploaded_file(
                        uploaded_audio
                    )

                    # ============================================================
                    # TRANSCRIBE
                    # ============================================================

                    transcript = transcribe_audio(
                        audio_path
                    )

                    # ============================================================
                    # SUMMARY
                    # ============================================================

                    summary = summarize_audio(
                        transcript
                    )

                    # ============================================================
                    # VECTORSTORE
                    # ============================================================

                    vectorstore = create_vectorstore(
                        transcript
                    )

                    st.session_state.audio_vectorstore = vectorstore
                    st.session_state.audio_transcript = transcript
                    st.session_state.audio_summary = summary
                    st.session_state.audio_loaded = True

                st.success(
                    "Audio processed successfully!"
                )

                st.audio(uploaded_audio)

            except Exception as e:
                st.exception(e)

    # ============================================================
    # CLEAR CHAT
    # ============================================================

    if clear_btn:

        st.session_state.audio_chat_history = []

        st.rerun()

    # ============================================================
    # SHOW SUMMARY
    # ============================================================

    if st.session_state.audio_summary:

        with st.expander(
            "📝 Audio Summary",
            expanded=True
        ):

            st.write(
                st.session_state.audio_summary
            )

    # ============================================================
    # ASK QUESTIONS
    # ============================================================

    if ask_btn:

        if not st.session_state.audio_loaded:

            st.error(
                "Please process audio first."
            )

        elif not question.strip():

            st.error(
                "Please enter a question."
            )

        else:

            try:

                with st.spinner(
                    "Searching transcript..."
                ):

                    history = [
                        (
                            item["question"],
                            item["answer"]
                        )
                        for item in st.session_state.audio_chat_history
                    ]

                    answer = audio_chat(
                        question=question,
                        vectorstore=st.session_state.audio_vectorstore,
                        chat_history=history,
                    )

                # ============================================================
                # SAVE HISTORY
                # ============================================================

                st.session_state.audio_chat_history.append({

                    "question": question,
                    "answer": answer

                })

            except Exception as e:
                st.exception(e)

    # ============================================================
    # DISPLAY CHAT HISTORY
    # ============================================================

    if st.session_state.audio_chat_history:

        st.markdown("<br>", unsafe_allow_html=True)

        st.subheader("💬 Chat History")

    for chat in st.session_state.audio_chat_history:

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
    # TRANSCRIPT
    # ============================================================

    if st.session_state.audio_transcript:

        with st.expander(
            "📄 Full Transcript"
        ):

            st.write(
                st.session_state.audio_transcript
            )

    st.markdown("---")

    st.caption(
        "Powered by Whisper, FAISS, Sentence Transformers, Ollama, and LangChain."
    )