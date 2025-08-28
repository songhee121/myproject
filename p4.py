import streamlit as st
from langchain_core.prompts import PromptTemplate

from MyLCH import getOpenAI

st.markdown("# 주제 설명문 보기")
st.sidebar.markdown("주제를 정하면 설명문을 작성하여 보여줍니다. 주제에 대해 정확히 알아가는 데 도움이 될 수 있습니다.")

# 입력 영역
input_text = st.text_area(label="주제 입력", label_visibility='visible',
                          placeholder="설명할 주제를 입력하세요 (예: 양자 컴퓨팅의 기본 개념)", key="input_text")

# 옵션
# 옵션
col1, col2 = st.columns([1,2])   # 왼쪽(설명 수준), 오른쪽(체크박스 영역)

with col1:
    depth = st.selectbox("설명 수준", ["간단", "중간", "상세"], index=1)

with col2:
    c1, c2 = st.columns(2)
    with c1:
        include_outline = st.checkbox("목차(아웃라인) 포함", value=True)
        include_refs = st.checkbox("참고문헌/검색 쿼리 제안 포함", value=True)
    with c2:
        include_examples = st.checkbox("실용적 예시 포함", value=True)
        include_next_steps = st.checkbox("다음 학습/연구 단계 제안", value=True)


st.markdown("---")

# 프롬프트 템플릿
query_template = '''당신은 해당 분야의 친절한 전문가입니다.
사용자가 지정한 주제에 대해 다음 요구사항을 충족하는 한국어 설명을 작성하세요.

요구사항:
- 주제: {topic}
- 설명 수준: {depth} (간단=한눈에 이해 가능한 요약, 중간=핵심 원리와 예시 포함, 상세=심화된 기술적 설명 및 응용 포함)
- 목차 포함 여부: {outline}
- 실용적 예시 포함 여부: {examples}
- 참고문헌/검색 쿼리 제안 포함 여부: {refs}
- 다음 학습/연구 단계 제안 포함 여부: {next_steps}

출력 형식 안내:
- Markdown 형식으로 출력하고, 각 섹션은 명확한 헤더(##)로 구분하세요.
- 가능한 경우 간단한 정의, 핵심 개념 정리(용어 설명), 실용적 예시(있다면 코드 스니펫 또는 실습 아이디어), 그리고 요약을 포함하세요.
- 요청된 항목(목차, 참고문헌, 다음 단계)은 체크리스트 또는 번호 목록으로 제공하세요.

자, 지금부터 위 규칙에 따라 작성하세요.
'''

prompt = PromptTemplate(
    input_variables=["topic", "depth", "outline", "examples", "refs", "next_steps"],
    template=query_template,
)

# 생성 버튼 (설명은 버튼을 눌렀을 때만 생성됨)
generate = st.button("설명 생성")

if generate:
    topic = st.session_state.get('input_text', '').strip()
    if topic:
        llm = getOpenAI()
        # 템플릿에 값 채우기
        prompt_text = prompt.format(
            topic=topic,
            depth=depth,
            outline="예" if include_outline else "아니오",
            examples="예" if include_examples else "아니오",
            refs="예" if include_refs else "아니오",
            next_steps="예" if include_next_steps else "아니오",
        )
        try:
            with st.spinner("설명 생성 중... 잠시만 기다려주세요"):
                response = llm.predict(prompt_text)
                # 결과를 세션에 저장해 재실행 시에도 유지
                st.session_state['last_response'] = response
        except Exception as e:
            st.error(f"LLM 호출 중 오류가 발생했습니다: {e}")
            st.session_state['last_response'] = None
    else:
        st.info("먼저 설명할 주제를 입력하세요.")

# 생성된 설명이 세션에 저장되어 있으면 표시
if st.session_state.get('last_response'):
    response = st.session_state['last_response']
    st.markdown("## 생성된 설명")
    st.write(response)

    # 간단 요약 및 다음 단계 버튼
    st.markdown("---")
    st.markdown("### 빠른 액션")
    if st.button("요약 추출 (150자 이내)"):
        try:
            llm = getOpenAI()
            summary_prompt = f"다음 내용을 150자 이내로 한국어로 요약하세요:\n\n{response}"
            summary = llm.predict(summary_prompt)
            st.write(summary)
        except Exception as e:
            st.error(f"요약 중 오류: {e}")
    if st.button("학습 체크리스트 생성"):
        try:
            llm = getOpenAI()
            checklist_prompt = f"다음 설명을 바탕으로 실제로 따라할 수 있는 학습 체크리스트(5단계 이내)를 한국어로 작성하세요:\n\n{response}"
            checklist = llm.predict(checklist_prompt)
            st.write(checklist)
        except Exception as e:
            st.error(f"체크리스트 생성 중 오류: {e}")
else:
    st.info("주제와 옵션을 입력한 뒤 '설명 생성' 버튼을 누르세요.")