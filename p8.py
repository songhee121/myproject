import streamlit as st
from langchain.chains.conversation.base import ConversationChain
from langchain.memory import ConversationBufferMemory
from streamlit_chat import message
from MyLCH import getOpenAI  # 사용자의 LLM 래퍼

st.markdown("채팅하기")
st.sidebar.markdown("학습한 내용을 주제로 토론/토의하며 지식을 확장해요")

# --- 세션 상태 초기화(일관된 키 사용) ---
if 'memory' not in st.session_state:
    st.session_state['memory'] = ConversationBufferMemory(return_messages=True)

if 'conv_chain' not in st.session_state:
    # LLM 객체는 세션 안에 보관(같은 프로세스 내에서만 유효)
    st.session_state['conv_chain'] = ConversationChain(
        llm=getOpenAI(),
        memory=st.session_state['memory'],
        verbose=False
    )

if 'chat_past' not in st.session_state:
    st.session_state['chat_past'] = ["안녕하세요!"]  # 사용자 발화(초기값은 대화 시작 프롬프트와 맞추기 위함)

if 'chat_generated' not in st.session_state:
    st.session_state['chat_generated'] = ["안녕하세요! 어떤 주제로 이야기를 해볼까요?"]  # 봇 응답

# --- 초기화(메모리 리셋) 버튼 ---
if st.sidebar.button("대화 초기화 (메모리 삭제)"):
    st.session_state['memory'] = ConversationBufferMemory(return_messages=True)
    st.session_state['conv_chain'] = ConversationChain(
        llm=getOpenAI(),
        memory=st.session_state['memory'],
        verbose=False
    )
    st.session_state['chat_past'] = ["안녕하세요!"]
    st.session_state['chat_generated'] = ["안녕하세요! 어떤 주제로 이야기를 해볼까요?"]
    st.success("대화와 메모리가 초기화되었습니다.")

# --- 채팅 함수(세션 내 체인 사용, 메모리에 자동 저장) ---
def conversational_chat(user_query: str) -> str:
    chain: ConversationChain = st.session_state['conv_chain']
    # chain.predict는 memory에 대화를 저장해줍니다.
    try:
        response = chain.predict(input=user_query)
    except Exception as e:
        # LLM 호출 실패시 예외 처리
        response = f"오류가 발생했습니다: {e}"
    # 세션 채팅 히스토리 갱신
    st.session_state['chat_past'].append(user_query)
    st.session_state['chat_generated'].append(response)
    return response

# --- UI: 입력 폼 ---
response_container = st.container()
container = st.container()

with container:
    with st.form(key='Conv_Question', clear_on_submit=True):
        user_input = st.text_input("Query:", placeholder="무엇이든 물어보세요 🙂", key='input')
        submit_button = st.form_submit_button(label='Send')

    if submit_button and user_input:
        with st.spinner("응답 생성 중..."):
            conversational_chat(user_input)

# --- 대화 출력(저장된 세션 히스토리 사용) ---
if st.session_state['chat_generated']:
    with response_container:
        # chat_past와 chat_generated의 길이가 같은지 안전 검사
        n = min(len(st.session_state['chat_past']), len(st.session_state['chat_generated']))
        for i in range(n):
            # 사용자 메시지
            message(st.session_state['chat_past'][i],
                    is_user=True,
                    key=f"user_{i}",
                    avatar_style="fun-emoji",
                    seed="Nala")
            # 봇 메시지
            message(st.session_state['chat_generated'][i],
                    key=f"bot_{i}",
                    avatar_style="bottts",
                    seed="Fluffy")