import streamlit as st
from langchain.chains.question_answering import load_qa_chain
from langchain_community.document_loaders import TextLoader
from langchain_community.vectorstores import Chroma

from MyLCH import getOpenAI, split_docs, getOpenAIEmbeddings

st.markdown("Page7")
st.sidebar.markdown("Clicked Page7")

documents = TextLoader("data/AI.txt").load()
# docs 변수에 분할 문서를 저장
docs = split_docs(documents)
embeddings = getOpenAIEmbeddings()
db = Chroma.from_documents(docs, embeddings, persist_directory="data")
chain = load_qa_chain(getOpenAI(), chain_type="stuff",verbose=True)


input_text = st.text_area(label="질문 입력", label_visibility='collapsed',
                          placeholder="질문 입력...")
if st.button("SEND"):
    if input_text:
        matching_docs = db.similarity_search(input_text)
        answer = chain.run(input_documents=matching_docs, question=input_text)
        st.info(answer)
    else:
        st.info("질문 입력")