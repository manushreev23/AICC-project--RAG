import os 
from dotenv import load_dotenv

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_nvidia_ai_endpoints import NVIDIAEmbeddings, ChatNVIDIA
from langchain_core.prompts import PromptTemplate

from pathlib import Path  # ✅ ADD THIS

# Load .env from app folder
#env_path = Path(__file__).resolve().parent / ".env"
#load_dotenv(env_path)
load_dotenv()
API_KEY = os.getenv("NVIDIA_API_KEY")
API_KEY_2 = os.getenv("NVIDIA_API_KEY_2")
if not API_KEY or not API_KEY_2:
    raise ValueError("❌ API keys not found in .env file")


from langchain_community.document_loaders import (
    PyPDFLoader,
    Docx2txtLoader,
    TextLoader,
    UnstructuredPowerPointLoader
)

import os

def load_document(file_path):
    ext = os.path.splitext(file_path)[1].lower()

    if ext == ".pdf":
        loader = PyPDFLoader(file_path)

    elif ext == ".docx":
        loader = Docx2txtLoader(file_path)

    elif ext == ".txt":
        loader = TextLoader(file_path)

    elif ext in [".ppt", ".pptx"]:
        loader = UnstructuredPowerPointLoader(file_path)

    else:
        raise ValueError(f"Unsupported file type: {ext}")

    documents = loader.load()
    return documents


# ---------------- BUILD VECTOR STORE ----------------
def build_vector_store(file_path):
    documents = load_document(file_path)


    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )
    chunks = splitter.split_documents(documents)

    embeddings = NVIDIAEmbeddings(
        model="nvidia/llama-nemotron-embed-1b-v2",
        api_key=API_KEY_2,
        truncate="NONE"
    )

    vector_store = FAISS.from_documents(chunks, embeddings)

    return vector_store


# ---------------- ASK FUNCTION ----------------
def ask_pdf(vector_store, query):

    retriever = vector_store.as_retriever()

    # LLM (can later move outside if needed)
    
    llm = ChatNVIDIA(
        model="openai/gpt-oss-120b",
        api_key=API_KEY
    )
    

    prompt = PromptTemplate(
        input_variables=["context", "question"],
        template="""
You are an AI assistant.

Answer ONLY using the context below.
If the answer is not in the context, say "I don't know".

Context:
{context}

Question:
{question}

Answer:
"""
    )

    # ✅ Updated retrieval method
    docs = retriever.invoke(query)

    context = " ".join([doc.page_content for doc in docs])

    final_prompt = prompt.format(context=context, question=query)

    response = llm.invoke(final_prompt)

    return response.content, docs


# db = build_vector_store("HMAC.pdf")
'''db = build_vector_store("sample.docx")
# or
db = build_vector_store("slides.pptx")
# or
db = build_vector_store("notes.txt")
# or
db = build_vector_store("file.pdf")
db = build_vector_store("notes.txt")
answer, docs = ask_pdf(db, "Explain the main topic")
print(answer)
#answer, docs = ask_pdf(db, "What is HMAC?")
#print(answer)'''