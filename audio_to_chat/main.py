import streamlit as st
import audio_module as am

# -----------------------------------------------------------------------------
# Page config
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Smart Document Analyzer",
    page_icon="🎧",
    layout="wide",
)

# -----------------------------------------------------------------------------
# Initialize session state
# -----------------------------------------------------------------------------
def init_session_state():
    defaults = {
        "audio_transcript": "",
        "audio_summary": "",
        "audio_vectorstore": None,
        "audio_chat_history": [],
        "audio_file_path": None,
        "audio_file_name": None,
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


init_session_state()

# -----------------------------------------------------------------------------
# Sidebar
# -----------------------------------------------------------------------------
with st.sidebar:
    st.title("⚙️ Settings")

    st.subheader("Models")

    whisper_model = st.selectbox(
        "Whisper Model",
        ["tiny", "base", "small", "medium"],
        index=1,
    )

    ollama_model = st.text_input(
        "Ollama Model",
        value=am.DEFAULT_OLLAMA_MODEL,
    )

    ollama_base_url = st.text_input(
        "Ollama Base URL",
        value=am.DEFAULT_OLLAMA_BASE_URL,
    )

    st.divider()

    st.subheader("🎧 Upload Audio")

    uploaded_audio = st.file_uploader(
        "Upload Audio File",
        type=["mp3", "wav", "m4a", "mp4"],
        accept_multiple_files=False,
    )

    # Save uploaded file
    if (
        uploaded_audio is not None
        and uploaded_audio.name != st.session_state.audio_file_name
    ):
        try:
            path = am.save_uploaded_file(uploaded_audio)

            st.session_state.audio_file_path = path
            st.session_state.audio_file_name = uploaded_audio.name
            st.session_state.audio_transcript = ""
            st.session_state.audio_summary = ""
            st.session_state.audio_vectorstore = None
            st.session_state.audio_chat_history = []

            st.success(f"Loaded: {uploaded_audio.name}")

        except Exception as e:
            st.error(f"Error uploading file: {e}")

    if st.session_state.audio_file_name:
        st.caption(f"Current File: {st.session_state.audio_file_name}")

    # Clear session
    if st.button("🧹 Clear Session", use_container_width=True):

        st.session_state.audio_transcript = ""
        st.session_state.audio_summary = ""
        st.session_state.audio_vectorstore = None
        st.session_state.audio_chat_history = []
        st.session_state.audio_file_path = None
        st.session_state.audio_file_name = None

        st.rerun()

# -----------------------------------------------------------------------------
# Main UI
# -----------------------------------------------------------------------------
st.title("📚 Smart Document Analyzer")

st.caption(
    "PDF • YouTube • Documents • Audio Q&A using Whisper + Ollama + FAISS"
)

tabs = st.tabs(
    [
        "🎧 Audio Q&A",
        "📄 PDF",
        "▶️ YouTube",
        "📝 Documents",
    ]
)

# -----------------------------------------------------------------------------
# AUDIO TAB
# -----------------------------------------------------------------------------
with tabs[0]:

    st.subheader("🎧 Audio Q&A and Summarization")

    if not st.session_state.audio_file_path:
        st.info("Upload an audio file from the sidebar.")
    else:

        col1, col2 = st.columns(2)

        # ---------------------------------------------------------------------
        # TRANSCRIBE
        # ---------------------------------------------------------------------
        with col1:

            if st.button(
                "🎙️ Transcribe Audio",
                use_container_width=True,
                type="primary",
            ):

                with st.spinner("Transcribing audio..."):

                    try:
                        transcript = am.transcribe_audio(
                            st.session_state.audio_file_path,
                            whisper_model_name=whisper_model,
                        )

                        if transcript.strip() == "":
                            st.error("Empty transcript returned.")
                        else:
                            st.session_state.audio_transcript = transcript

                            # Create vectorstore
                            st.session_state.audio_vectorstore = (
                                am.create_vectorstore(transcript)
                            )

                            st.success("Transcription completed.")

                    except Exception as e:
                        st.error(f"Transcription failed: {e}")

        # ---------------------------------------------------------------------
        # SUMMARIZE
        # ---------------------------------------------------------------------
        with col2:

            if st.button(
                "📝 Summarize Audio",
                use_container_width=True,
                disabled=not bool(st.session_state.audio_transcript),
            ):

                with st.spinner("Generating summary..."):

                    try:
                        summary = am.summarize_audio(
                            st.session_state.audio_transcript,
                            model_name=ollama_model,
                            base_url=ollama_base_url,
                        )

                        st.session_state.audio_summary = summary

                        st.success("Summary generated.")

                    except Exception as e:
                        st.error(f"Summarization failed: {e}")

        # ---------------------------------------------------------------------
        # TRANSCRIPT
        # ---------------------------------------------------------------------
        if st.session_state.audio_transcript:

            with st.expander("📜 Transcript"):

                st.write(st.session_state.audio_transcript)

        # ---------------------------------------------------------------------
        # SUMMARY
        # ---------------------------------------------------------------------
        if st.session_state.audio_summary:

            st.markdown("## Summary")

            st.write(st.session_state.audio_summary)

            st.download_button(
                label="⬇️ Download Summary",
                data=st.session_state.audio_summary,
                file_name="audio_summary.txt",
                mime="text/plain",
            )

        st.divider()

        # ---------------------------------------------------------------------
        # CHAT SECTION
        # ---------------------------------------------------------------------
        st.markdown("## 💬 Chat with Audio")

        # Show previous chat
        for user_msg, assistant_msg in st.session_state.audio_chat_history:

            with st.chat_message("user"):
                st.write(user_msg)

            with st.chat_message("assistant"):
                st.write(assistant_msg)

        question = st.chat_input(
            "Ask something about the audio...",
            disabled=(st.session_state.audio_vectorstore is None),
        )

        if question:

            with st.chat_message("user"):
                st.write(question)

            with st.chat_message("assistant"):

                with st.spinner("Thinking..."):

                    try:
                        answer = am.audio_chat(
                            question=question,
                            vectorstore=st.session_state.audio_vectorstore,
                            chat_history=st.session_state.audio_chat_history,
                            model_name=ollama_model,
                            base_url=ollama_base_url,
                        )

                    except Exception as e:
                        answer = f"Error: {e}"

                st.write(answer)

            st.session_state.audio_chat_history.append(
                (question, answer)
            )

# -----------------------------------------------------------------------------
# OTHER TABS
# -----------------------------------------------------------------------------
with tabs[1]:
    st.info("PDF Analyzer Module")

with tabs[2]:
    st.info("YouTube Summarizer Module")

with tabs[3]:
    st.info("Document Summarization Module")