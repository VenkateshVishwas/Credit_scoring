from typing import List
import os
import faiss
import pickle
from langchain.text_splitter import CharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import FAISS
from langchain.docstore.document import Document


VECTOR_STORE_PATH = "app/vectorstore/store.faiss"
EMBEDDINGS_PICKLE = "app/vectorstore/index.pkl"
embedding_model = OpenAIEmbeddings()


def processAndStoreFiles(file_contents: List[str], file_names: List[str]):
    text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=100)

    docs = [Document(page_content=text, metadata={"source": name})
            for text, name in zip(file_contents, file_names)]

    all_chunks = text_splitter.split_documents(docs)

    vector_db = FAISS.from_documents(all_chunks, embedding_model)
    vector_db.save_local(VECTOR_STORE_PATH)

    with open(EMBEDDINGS_PICKLE, "wb") as f:
        pickle.dump(vector_db.index, f)

    return {"message": "Files processed and vector store updated"}


def getRelevantChunks(query: str, k: int = 3) -> List[str]:
    vector_db = FAISS.load_local(VECTOR_STORE_PATH, embedding_model)
    results = vector_db.similarity_search(query, k=k)
    return [doc.page_content for doc in results]
