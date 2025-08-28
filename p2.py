import streamlit as st

from MyLCH import get_pdf_text, get_text_chunks, get_vectorstore, get_conversation_chain

st.markdown("# 학습자료로 질문하기")
st.sidebar.markdown("다양한 형식의 학습 자료를 업로드한 후 이에 대해 질문할 수 있습니다.")

user_uploads = st.file_uploader("파일을 업로드해주세요", accept_multiple_files=True)
if user_uploads is not None:
    if st.button("Upload"):
        with st.spinner("처리중.."):
            # PDF 텍스트 가져오기
            raw_text = get_pdf_text(user_uploads)
            # 텍스트에서 청크 검색
            text_chunks = get_text_chunks(raw_text)
            # PDF 텍스트 저장을 위해 FAISS 벡터 저장소 만들기
            vectorstore = get_vectorstore(text_chunks)
            # 대화 체인 만들기
            st.session_state.conversation = get_conversation_chain(vectorstore)


# In[12]:


if user_query := st.chat_input("질문을 입력해주세요~"):
    # 대화 체인을 사용하여 사용자의 메시지를 처리
    if 'conversation' in st.session_state:
        result = st.session_state.conversation({
            "question": user_query,
            "chat_history": st.session_state.get('chat_history', [])
        })
        response = result["answer"]
    else:
        response = "먼저 문서를 업로드해주세요."
    with st.chat_message("assistant"):
        st.write(response)