from pathlib import Path
from langchain_community.document_loaders import TextLoader

def load_schema():
    path=Path('RAG/schema.sql')
    loder=TextLoader(str(path),encoding='utf-8')
    docs=loder.load()
    return docs

if __name__=="__main__":
    docs=load_schema()

    print(f"documaets : {len(docs)}")
    print(docs[0].page_content)
