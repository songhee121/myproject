import streamlit as st
from langchain.chains.conversation.base import ConversationChain
from langchain.memory import ConversationBufferMemory
from streamlit_chat import message
from MyLCH import getOpenAI  # 사용자의 LLM 래퍼

st.markdown("# 채팅하기")
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

# 현재 모드 저장 (None, 'research', 'debate')
if 'mode' not in st.session_state:
    st.session_state['mode'] = None

# --- 세션 초기화(메모리 리셋) 버튼 ---
if st.sidebar.button("대화 초기화 (메모리 삭제)"):
    st.session_state['memory'] = ConversationBufferMemory(return_messages=True)
    st.session_state['conv_chain'] = ConversationChain(
        llm=getOpenAI(),
        memory=st.session_state['memory'],
        verbose=False
    )
    st.session_state['chat_past'] = ["안녕하세요!"]
    st.session_state['chat_generated'] = ["안녕하세요! 어떤 주제로 이야기를 해볼까요?"]
    st.session_state['mode'] = None
    st.success("대화와 메모리가 초기화되었습니다.")

# --- 모드 정의(시스템/진행 지침) ---
MODE_INSTRUCTIONS = {
    'research': '''주제별 연구 모드 시작
역할: AI는 연구 파트너로서 사용자가 제시한 주제를 다각도에서 깊게 파고듭니다.

동작 방식:
  1) 주제 정의: 사용자가 주제를 입력하면 먼저 핵심 개념과 범위를 정의합니다.
  2) 쟁점 분해: 관련 하위질문(리서치 질문)을 만들고 우선순위를 제안합니다.
  3) 조사/가설: 필요한 배경 지식, 가능한 가설, 검증 방법(실험/데이터/문헌) 등을 제안합니다.
  4) 상호 소통: 사용자가 답변하면 추가 실험이나 자료 요청, 세부 질문을 통해 점진적으로 깊이를 더합니다.
  5) 산출물 제안: 요약, 문헌 목록, 연구 계획(아웃라인), 실험 설계, 다음 단계 체크리스트 등 산출물을 제공합니다.

목표: 단순 토론을 넘어서 실제 연구처럼 체계적으로 주제를 파고들며 상호작용합니다.''',

    'debate': '''주제 토론 모드 시작
역할: AI는 토론 진행자이자 참여자로서 균형 잡힌 관점을 제공하고, 찬성/반대 포인트를 제시하고 심화 질문을 던집니다.

동작 방식:
  - 사용자가 토론할 주제를 제공하면, 먼저 주제 정의와 쟁점을 정리한 뒤 토론을 시작합니다.
  - AI는 양쪽 관점을 모두 소개하고, 핵심 논거와 근거를 요청합니다.
  - 필요 시 토론 규칙(발언 순서, 타임박스)을 제안해 토론을 구조화합니다.'''
}

# --- 모드 버튼(입력란 바로 위에 배치) ---
st.markdown("**모드 선택 — 빠른 시작 버튼**")
col1, col2, col3 = st.columns([1,1,2])
with col1:
    if st.button("주제별 연구"):
        # 모드 설정 및 메모리에 모드 지침 저장
        st.session_state['mode'] = 'research'
        instr = MODE_INSTRUCTIONS['research']
        # 메모리에 모드 설정을 기록(나중에 체인이 참조할 수 있도록)
        st.session_state['memory'].save_context({"mode_set": "research"}, {"assistant": instr})
        # 사용자와 봇 히스토리에도 가시적으로 추가
        st.session_state['chat_past'].append("[모드 선택] 주제별 연구")
        st.session_state['chat_generated'].append("주제별 연구 모드로 전환했습니다. 연구할 주제를 입력해주세요.")
with col2:
    if st.button("주제 토론"):
        st.session_state['mode'] = 'debate'
        instr = MODE_INSTRUCTIONS['debate']
        st.session_state['memory'].save_context({"mode_set": "debate"}, {"assistant": instr})
        st.session_state['chat_past'].append("[모드 선택] 주제 토론")
        st.session_state['chat_generated'].append("주제 토론 모드로 전환했습니다. 토론할 주제를 입력해주세요.")
with col3:
    if st.session_state['mode']:
        display_map = {
            'research': '주제별 연구',
            'debate': '주제 토론'
        }
        st.write(f"현재 모드: **{ display_map.get(st.session_state['mode'], st.session_state['mode']) }**")
        if st.button("모드 해제"):
            st.session_state['mode'] = None
            # 모드 해제는 단순 상태 변경; 필요시 메모리 재설정 또는 모드 해제 기록
            st.session_state['chat_past'].append("[모드 해제]")
            st.session_state['chat_generated'].append("모드를 해제했습니다. 일반 대화로 돌아갑니다.")

# --- 채팅 함수(세션 내 체인 사용, 메모리에 자동 저장) ---
def conversational_chat(user_query: str) -> str:
    chain: ConversationChain = st.session_state['conv_chain']
    try:
        # 모드가 설정된 경우, 간단한 프롬프트 어프로치로 체인에 모드 상태를 반영할 수 있도록 메모리에 저장
        if st.session_state['mode'] == 'research':
            # 연구 모드일 때: 사용자가 주제를 처음 제시하면 체인에게 연구자 관점에서 접근하라고 알려줌
            # 메모리에 현재 모드 정보를 저장하면 이후 대화에서 참조될 수 있음
            st.session_state['memory'].save_context({"user": user_query}, {"assistant": "사용자가 주제를 제시함. 연구자 관점에서 응답할 것."})
        elif st.session_state['mode'] == 'debate':
            st.session_state['memory'].save_context({"user": user_query}, {"assistant": "사용자가 토론 주제를 제시함. 토론자 및 진행자 관점에서 응답할 것."})

        # 기본적으로 체인에 유저 입력을 넣어 예측
        response = chain.predict(input=user_query)
    except Exception as e:
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

# 추가 팁 표시
st.sidebar.markdown("---")
st.sidebar.info("모드를 선택하면 AI가 해당 역할로 대화를 이어갑니다. 모드를 해제하려면 '모드 해제' 버튼을 누르세요.")