import streamlit as st
import datetime
from langchain.chat_models import ChatOpenAI
from langchain.schema import Document
from langchain.vectorstores import FAISS
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.chains import RetrievalQA

# --- LangChain 초기화 ---
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
embeddings = OpenAIEmbeddings()

# 세션 상태 초기화
if "vectorstore" not in st.session_state:
    st.session_state.vectorstore = None
if "docs" not in st.session_state:
    st.session_state.docs = []

# --- Streamlit UI ---
st.title("📅 달력에 메모하기")

# 오늘 날짜
today = datetime.date.today()
date = st.date_input("날짜 선택", today)

# 메모 입력
memo = st.text_area("메모 입력")
if st.button("저장"):
    if memo.strip():
        doc = Document(page_content=memo, metadata={"date": str(date)})
        st.session_state.docs.append(doc)
        st.session_state.vectorstore = FAISS.from_documents(st.session_state.docs, embeddings)
        st.success(f"{date} 메모 저장 완료!")

# 전체 메모 보기
st.subheader("📂 전체 메모")
if st.session_state.docs:
    for i, d in enumerate(st.session_state.docs):
        col1, col2 = st.columns([8, 1])
        with col1:
            st.markdown(f"**{d.metadata['date']}** : {d.page_content}")
        with col2:
            if st.button("🗑️", key=f"delete_{i}"):
                # 삭제: 해당 문서 제거 후 vectorstore 재생성
                st.session_state.docs.pop(i)
                if st.session_state.docs:
                    st.session_state.vectorstore = FAISS.from_documents(st.session_state.docs, embeddings)
                else:
                    st.session_state.vectorstore = None
                st.rerun()   # ✅ 최신 Streamlit에서는 st.experimental_rerun() 대신 st.rerun() 사용
else:
    st.info("아직 저장된 메모가 없습니다.")

from langchain_core.prompts import PromptTemplate

# AI에게 질문
st.subheader("❓ AI에게 질문하기")
question = st.text_input("질문을 입력하세요")
if st.button("질문하기"):
    if question.strip():
        if not st.session_state.docs:
            st.warning("먼저 메모를 저장해주세요.")
        else:
            # 모든 메모를 하나의 텍스트로 합치기
            all_memos = "\n".join(
                [f"- {d.metadata['date']}: {d.page_content}" for d in st.session_state.docs]
            )

            # 프롬프트 템플릿 (예시코드(page7.py) 참고해서 설계)
            qa_template = PromptTemplate(
                input_variables=["memos", "question"],
                template=(
                    "당신은 개인 비서입니다. 아래 달력 메모 내용을 참고하여 사용자의 질문에 답하세요.\n\n"
                    "메모 목록:\n{memos}\n\n"
                    "질문: {question}\n\n"
                    "규칙:\n"
                    "- 반드시 메모 내용과 개수를 바탕으로 답하세요.\n"
                    "- 메모에 없는 정보는 추측하지 말고 '메모에 해당 내용이 없습니다'라고 답하세요.\n"
                    "- 한국어로 답변하세요.\n\n"
                    "답변:"
                )
            )

            prompt = qa_template.format(memos=all_memos, question=question)

            try:
                answer = llm.predict(prompt)
                st.write(answer)
            except Exception as e:
                st.error(f"질문 처리 중 오류 발생: {e}")