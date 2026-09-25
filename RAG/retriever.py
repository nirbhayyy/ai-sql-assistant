
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings

embadding=HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

db=FAISS.load_local(
    "RAG/faiss_index",
    embadding,
    allow_dangerous_deserialization=True
)
def retrieve_schema(query ):
    docs=db.similarity_search(query,k=2)
    return docs


if __name__=='__main__':
    q=input('ASK :')
    result=retrieve_schema(q)

    for i,doc in enumerate(result,1):
        print("=" * 40)
        print(f"Result {i}")
        print(doc.page_content)