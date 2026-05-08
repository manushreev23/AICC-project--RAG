"""
audio_module.py
----------------
A modular Streamlit-friendly module for audio transcription,
summarization, and Retrieval-Augmented Generation (RAG) chat.

Stack:
- Whisper (local speech-to-text)
- Sentence Transformers (local embeddings)
- FAISS vector database
- Ollama (phi3)
- LangChain

Public Functions:
    transcribe_audio()
    summarize_audio()
    create_vectorstore()
    audio_chat()
"""

from __future__ import annotations

import os
import tempfile
from typing import List, Optional, Tuple

SUPPORTED_AUDIO_EXTENSIONS = {".mp3", ".wav", ".m4a", ".mp4"}

# -----------------------------------------------------------------------------
# Default Models
# -----------------------------------------------------------------------------
DEFAULT_WHISPER_MODEL = os.environ.get("WHISPER_MODEL", "base")

DEFAULT_EMBEDDING_MODEL = os.environ.get(
    "EMBEDDING_MODEL",
    "sentence-transformers/all-MiniLM-L6-v2",
)

DEFAULT_OLLAMA_MODEL = os.environ.get(
    "OLLAMA_MODEL",
    "phi3",
)

DEFAULT_OLLAMA_BASE_URL = os.environ.get(
    "OLLAMA_BASE_URL",
    "http://localhost:11434",
)

# -----------------------------------------------------------------------------
# Caches
# -----------------------------------------------------------------------------
_whisper_model_cache = {}
_embeddings_cache = {}

# -----------------------------------------------------------------------------
# Load Whisper Model
# -----------------------------------------------------------------------------
def _get_whisper_model(model_name: str = DEFAULT_WHISPER_MODEL):

    if model_name in _whisper_model_cache:
        return _whisper_model_cache[model_name]

    try:
        import whisper
    except ImportError as e:
        raise ImportError(
            "Install Whisper using:\n"
            "pip install openai-whisper"
        ) from e

    model = whisper.load_model(model_name)

    _whisper_model_cache[model_name] = model

    return model


# -----------------------------------------------------------------------------
# Load Embedding Model
# -----------------------------------------------------------------------------
def _get_embeddings(
    model_name: str = DEFAULT_EMBEDDING_MODEL,
):

    if model_name in _embeddings_cache:
        return _embeddings_cache[model_name]

    try:
        from langchain_huggingface import HuggingFaceEmbeddings

    except ImportError:
        from langchain_community.embeddings import (
            HuggingFaceEmbeddings,
        )

    embeddings = HuggingFaceEmbeddings(
        model_name=model_name,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )

    _embeddings_cache[model_name] = embeddings

    return embeddings


# -----------------------------------------------------------------------------
# Load Ollama
# -----------------------------------------------------------------------------
def _get_ollama_llm(
    model_name: str = DEFAULT_OLLAMA_MODEL,
    base_url: str = DEFAULT_OLLAMA_BASE_URL,
    temperature: float = 0.2,
):

    try:
        from langchain_ollama import ChatOllama

    except ImportError:
        from langchain_community.chat_models import ChatOllama

    return ChatOllama(
        model=model_name,
        base_url=base_url,
        temperature=temperature,
    )


# -----------------------------------------------------------------------------
# Save Uploaded File
# -----------------------------------------------------------------------------
def save_uploaded_file(uploaded_file):

    suffix = os.path.splitext(uploaded_file.name)[1].lower()

    if suffix not in SUPPORTED_AUDIO_EXTENSIONS:
        raise ValueError(
            f"Unsupported audio format: {suffix}"
        )

    temp_file = tempfile.NamedTemporaryFile(
        delete=False,
        suffix=suffix,
    )

    temp_file.write(uploaded_file.getbuffer())

    temp_file.flush()
    temp_file.close()

    return temp_file.name


# -----------------------------------------------------------------------------
# Transcription
# -----------------------------------------------------------------------------
def transcribe_audio(
    file_path: str,
    whisper_model_name: str = DEFAULT_WHISPER_MODEL,
) -> str:

    if not os.path.isfile(file_path):
        raise FileNotFoundError(
            f"File not found: {file_path}"
        )

    ext = os.path.splitext(file_path)[1].lower()

    if ext not in SUPPORTED_AUDIO_EXTENSIONS:
        raise ValueError(
            f"Unsupported format: {ext}"
        )

    model = _get_whisper_model(whisper_model_name)

    try:
        result = model.transcribe(
            file_path,
            fp16=False,
        )

    except Exception as e:
        raise RuntimeError(
            f"Whisper transcription failed: {e}"
        )

    text = result.get("text", "").strip()

    return text


# -----------------------------------------------------------------------------
# Create Vectorstore
# -----------------------------------------------------------------------------
def create_vectorstore(
    transcript: str,
    chunk_size: int = 800,
    chunk_overlap: int = 120,
    embedding_model_name: str = DEFAULT_EMBEDDING_MODEL,
):

    if not transcript.strip():
        raise ValueError(
            "Transcript is empty."
        )

    from langchain_text_splitters import RecursiveCharacterTextSplitter

    from langchain_community.vectorstores import FAISS

    from langchain_core.documents import Document

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
    )

    chunks = splitter.split_text(transcript)

    docs = [
        Document(
            page_content=chunk,
            metadata={"chunk_id": i},
        )
        for i, chunk in enumerate(chunks)
    ]

    embeddings = _get_embeddings(
        embedding_model_name
    )

    vectorstore = FAISS.from_documents(
        docs,
        embeddings,
    )

    return vectorstore


# -----------------------------------------------------------------------------
# Summary Prompt
# -----------------------------------------------------------------------------
_SUMMARY_PROMPT = """
You are a concise assistant.

Summarize the following audio transcript.

Guidelines:
- Capture the main topic
- Mention key points
- Mention decisions and action items
- Keep summary short
- Do not invent information

Transcript:
{transcript}

Summary:
"""


# -----------------------------------------------------------------------------
# Summarization
# -----------------------------------------------------------------------------
def summarize_audio(
    transcript: str,
    model_name: str = DEFAULT_OLLAMA_MODEL,
    base_url: str = DEFAULT_OLLAMA_BASE_URL,
) -> str:

    if not transcript.strip():
        raise ValueError(
            "Transcript is empty."
        )

    llm = _get_ollama_llm(
        model_name=model_name,
        base_url=base_url,
        temperature=0.2,
    )

    try:

        # Small Transcript
        if len(transcript) <= 6000:

            from langchain_core.prompts import (
                ChatPromptTemplate,
            )

            prompt = ChatPromptTemplate.from_template(
                _SUMMARY_PROMPT
            )

            chain = prompt | llm

            response = chain.invoke(
                {"transcript": transcript}
            )

            return getattr(
                response,
                "content",
                str(response),
            ).strip()

        # Large Transcript
        from langchain.chains.summarize import (
            load_summarize_chain,
        )

        from langchain_text_splitters import RecursiveCharacterTextSplitter

        from langchain_core.documents import Document

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=3000,
            chunk_overlap=200,
        )

        docs = [
            Document(page_content=chunk)
            for chunk in splitter.split_text(
                transcript
            )
        ]

        chain = load_summarize_chain(
            llm,
            chain_type="map_reduce",
        )

        result = chain.invoke(
            {"input_documents": docs}
        )

        return result.get(
            "output_text",
            "",
        ).strip()

    except Exception as e:
        raise RuntimeError(
            f"Summarization failed: {e}"
        )


# -----------------------------------------------------------------------------
# Chat Prompt
# -----------------------------------------------------------------------------
_CHAT_SYSTEM_PROMPT = """
You are an assistant that answers questions
strictly using the provided transcript context.

Rules:
- Use ONLY the context
- If answer is missing, say:
  "I couldn't find that in the audio."
- Be concise

Context:
{context}
"""

_CHAT_USER_PROMPT = """
Question:
{question}
"""


# -----------------------------------------------------------------------------
# Audio Chat
# -----------------------------------------------------------------------------
def audio_chat(
    question: str,
    vectorstore,
    chat_history: Optional[
        List[Tuple[str, str]]
    ] = None,
    k: int = 4,
    model_name: str = DEFAULT_OLLAMA_MODEL,
    base_url: str = DEFAULT_OLLAMA_BASE_URL,
) -> str:

    if not question.strip():
        raise ValueError(
            "Question cannot be empty."
        )

    if vectorstore is None:
        raise ValueError(
            "Vectorstore not initialized."
        )

    try:

        retriever = vectorstore.as_retriever(
            search_kwargs={"k": k}
        )

        try:
            relevant_docs = retriever.invoke(
                question
            )

        except AttributeError:
            relevant_docs = (
                retriever.get_relevant_documents(
                    question
                )
            )

        context = "\n\n---\n\n".join(
            d.page_content
            for d in relevant_docs
        )

        if not context:
            context = "(no context)"

        from langchain_core.messages import (
            SystemMessage,
            HumanMessage,
            AIMessage,
        )

        messages = [
            SystemMessage(
                content=_CHAT_SYSTEM_PROMPT.format(
                    context=context
                )
            )
        ]

        # Chat History
        if chat_history:

            for user_msg, assistant_msg in chat_history[-6:]:

                messages.append(
                    HumanMessage(
                        content=user_msg
                    )
                )

                messages.append(
                    AIMessage(
                        content=assistant_msg
                    )
                )

        messages.append(
            HumanMessage(
                content=_CHAT_USER_PROMPT.format(
                    question=question
                )
            )
        )

        llm = _get_ollama_llm(
            model_name=model_name,
            base_url=base_url,
            temperature=0.1,
        )

        response = llm.invoke(messages)

        return getattr(
            response,
            "content",
            str(response),
        ).strip()

    except Exception as e:
        raise RuntimeError(
            f"Chat failed: {e}"
        )