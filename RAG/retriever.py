from langchain_community.embeddings import HuggingFaceBgeEmbeddings
from langchain_community.vectorstores import FAISS

embadding=HuggingFaceBgeEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

db=FAISS.load_local(
    "RAG/faiss_index",
    embadding,
    allow_dangerous_deserialization=True
)

query=input(" ask :")

doc=db.similarity_search(query,k=2)

for i,d in enumerate(doc,1):
    
        print('='*60)
        print(f" result : {doc}")
        print(d.page_content)