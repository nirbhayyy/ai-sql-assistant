from langchain_community.embeddings import HuggingFaceBgeEmbeddings
from langchain_community.vectorstores import faiss
from splitter import chunks

embedding=HuggingFaceBgeEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

vector_db=faiss.FAISS.from_documents(chunks,embedding)

vector_db.save_local('RAG/faiss_index')

print('done embedding')