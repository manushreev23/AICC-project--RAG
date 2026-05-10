# OmniRAG — AI-Powered Multi-Modal RAG Platform

## Overview

OmniRAG is an AI-powered Multi-Modal Retrieval-Augmented Generation (RAG) platform designed to intelligently retrieve, process, and answer questions from multiple data sources including PDFs, documents, YouTube videos, audio files, and presentations.

The system uses semantic search, vector embeddings, FAISS vector databases, and Large Language Models (LLMs) to generate context-aware and accurate responses.

The platform also supports automatic PowerPoint presentation generation from uploaded PDF documents.

---

# Features

## AI Chat Assistant

* Conversational AI chatbot
* Context-aware responses
* Persistent chat history
* NVIDIA LLM integration

## PDF Question Answering

* Upload PDF documents
* Semantic retrieval
* Context-based question answering

## YouTube Video Q&A

* Extract video transcripts
* Ask questions from video content
* Intelligent transcript retrieval

## Audio File Q&A

* Speech-to-text transcription using Whisper
* AI-powered audio understanding
* Transcript-based semantic search

## Multi-Document Q&A

Supports:

* PDF
* DOCX
* TXT
* PPT/PPTX

## PPT Generator

* Generate professional PowerPoint presentations from PDFs
* Topic-wise summarization
* Automatic slide generation

---

# System Architecture

The project follows a Retrieval-Augmented Generation (RAG) architecture.

## Workflow

### 1. User Upload/Input

Users upload:

* PDFs
* Documents
* Audio files
* YouTube URLs

### 2. Data Extraction

The system extracts content using:

* PyPDFLoader
* Whisper
* YouTube Transcript API
* Document loaders

### 3. Text Chunking

Text is split using:

* RecursiveCharacterTextSplitter

### 4. Embedding Generation

Embeddings are generated using:

* NVIDIA Embeddings
* Sentence Transformers

### 5. Vector Database

Embeddings are stored in:

* FAISS Vector Store

### 6. Retrieval

Relevant chunks are retrieved using:

* Semantic similarity search

### 7. Response Generation

LLMs generate context-aware responses using:

* NVIDIA Chat Models
* Ollama Phi3

---

# Technologies Used

| Category            | Technologies                             |
| ------------------- | ---------------------------------------- |
| Frontend            | Streamlit                                |
| Backend             | Python                                   |
| AI Framework        | LangChain                                |
| Vector Database     | FAISS                                    |
| Embeddings          | NVIDIA Embeddings, Sentence Transformers |
| LLMs                | NVIDIA Chat Models, Ollama Phi3          |
| Speech-to-Text      | Whisper                                  |
| PDF Processing      | PyPDFLoader                              |
| Document Processing | Docx2txtLoader                           |
| PPT Generation      | python-pptx                              |

---

# Project Structure

```bash
project/
│
├── main.py
│
├── backend/
│
│   ├── chatbot/
│   │   ├── app.py
│   │   └── modules/
│   │       └── chat.py
│   │
│   ├── pdf_rag/
│   │   ├── app.py
│   │   └── modules/
│   │       └── pdf.py
│   │
│   ├── yt_rag/
│   │   ├── app.py
│   │   └── modules/
│   │       └── yt_rag.py
│   │
│   ├── audio_to_chat/
│   │   ├── app.py
│   │   └── modules/
│   │       └── audio_to_chat.py
│   │
│   └── pdf_to_ppt/
│       ├── app.py
│       └── modules/
│
├── requirements.txt
│
└── README.md
```

---

# Installation

## Clone Repository

```bash
git clone <repository-url>
cd project-name
```

---

# Create Virtual Environment

## Windows

```bash
python -m venv venv
venv\Scripts\activate
```

## Linux / Mac

```bash
python3 -m venv venv
source venv/bin/activate
```

---

# Install Dependencies

```bash
pip install -r requirements.txt
```

---

# Environment Variables

Create a `.env` file:

```env
NVIDIA_API_KEY=your_api_key
NVIDIA_API_KEY_2=your_api_key
NVIDIA_API_KEY_3=your_api_key
```

---

# Run the Application

```bash
streamlit run main.py
```

---

# Streamlit Tabs

The application contains:

| Tab              | Description                       |
| ---------------- | --------------------------------- |
| 💬 AI Chat       | Conversational AI Assistant       |
| 📄 PDF Q&A       | Ask questions from PDFs           |
| 🎥 YouTube Q&A   | Query YouTube transcripts         |
| 🎤 Audio Q&A     | Audio transcription + Q&A         |
| 📁 Documents     | Multi-document semantic retrieval |
| 📊 PPT Generator | Generate PPT from PDFs            |

---

# Advantages

* Multi-modal data understanding
* Semantic search capability
* Reduced hallucination using RAG
* Context-aware responses
* Professional UI
* Modular architecture
* Scalable design

---

# Limitations

* Large files may increase processing time
* Requires API keys for NVIDIA models
* Audio transcription depends on audio quality
* YouTube videos without transcripts cannot be processed

---

# Future Enhancements

* OCR support for scanned PDFs
* Multi-language support
* Cloud deployment
* Authentication system
* Advanced vector databases
* Real-time collaboration
* Hybrid search implementation

---

# Screenshots

Add project screenshots here.

---

# Author

Developed as part of an AI-powered Multi-Modal RAG System project.

---

# License

This project is for educational and research purposes.
