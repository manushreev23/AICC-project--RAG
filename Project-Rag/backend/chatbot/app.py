import streamlit as st
from backend.chatbot.modules.chat import (
    initialize_messages,
    chat_step,
)

# =========================================================
# PAGE CONFIG
# =========================================================
st.set_page_config(page_title="AI Chatbot", layout="wide")


# =========================================================
# CSS
# =========================================================
def load_css():
    st.markdown("""
    <style>
     
    .chat-main-container {
        background: rgba(255,255,255,0.04);
            padding: 28px;
            border-radius: 24px;
            border: 1px solid rgba(255,255,255,0.08);
            backdrop-filter: blur(12px);
    }

    .chat-title {
        font-size:42px;
            font-weight:800;
            background: linear-gradient(
                90deg,
                #22c55e,
                #14b8a6
            );

            -webkit-background-clip:text;
           
    }

    .chat-subtitle {
        color:#cbd5e1;
            margin-top:10px;
            font-size:16px;
    }

    .user-message {
        background: #00a693;
        color: white;
        padding: 14px;
        border-radius: 16px;
        margin: 10px 0 10px 25%;
        border: 1px solid #e2e8f0;
    }

    .assistant-message {
        background: #004953;
        padding: 14px;
        border-radius: 16px;
        margin: 10px 25% 10px 0;
        border: 1px solid #e2e8f0;
    }
    </style>
    """, unsafe_allow_html=True)


# =========================================================
# HEADER
# =========================================================
def render_header():
     st.markdown(
        """
        <div class="chat-main-container">
        <div class="chat-title">💬 AI Chat Assistant</div>
          <div class="chat-subtitle">
        Intelligent conversational AI powered by NVIDIA
        </div>

        </div>
        """,
        unsafe_allow_html=True,
    )
    


# =========================================================
# CHAT DISPLAY
# =========================================================
def render_chat(messages):
    for msg in messages:
        if msg["role"] == "system":
            continue

        if msg["role"] == "user":
            st.markdown(
                f'<div class="user-message"><b></b>{msg["content"]}</div>',
                unsafe_allow_html=True
            )

        elif msg["role"] == "assistant":
            st.markdown(
                f'<div class="assistant-message"><b></b>{msg["content"]}</div>',
                unsafe_allow_html=True
            )


# =========================================================
# MAIN CHATBOT FUNCTION
# =========================================================
def render_chatbot():

    load_css()

    # Session init
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = initialize_messages()

    

    render_header()

    # Clear button
    col1, col2 = st.columns([8, 1])
    with col2:
        if st.button("🗑️"):
            st.session_state.chat_messages = initialize_messages()
            st.rerun()

    # Chat history
    render_chat(st.session_state.chat_messages)

    # Input
    user_input = st.chat_input("Ask something...")

    if user_input:
        with st.spinner("Thinking..."):
            response, updated_messages = chat_step(
                st.session_state.chat_messages,
                user_input
            )

            st.session_state.chat_messages = updated_messages

        st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)