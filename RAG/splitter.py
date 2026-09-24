from loader import load_schema
from langchain_text_splitters import RecursiveCharacterTextSplitter

docs=load_schema()

splitter=RecursiveCharacterTextSplitter(
    chunk_size=120,
    chunk_overlap=50
)

chunks=splitter.split_documents(docs)
print(f"total chunks {len(chunks)}")

for i,chunk in enumerate(chunks):
    print('='*40)
    print(f'chunk {i+1}')
    print(chunk.page_content)