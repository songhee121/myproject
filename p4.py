import streamlit as st
from langchain_core.prompts import PromptTemplate
from MyLCH import getOpenAI

import requests
from bs4 import BeautifulSoup

st.markdown("# 설명문 보기")
st.sidebar.markdown("주제를 정하면 설명문을 작성하여 보여줍니다. 주제에 대해 정확히 알아가는 데 도움이 될 수 있습니다.")

# 입력 영역
input_text = st.text_area(
    label="주제 입력",
    label_visibility='visible',
    placeholder="설명할 주제를 입력하세요 (예: 양자 컴퓨팅의 기본 개념)",
    key="input_text"
)

# 옵션
col1, col2 = st.columns([1, 2])   # 왼쪽(설명 수준), 오른쪽(체크박스 영역)

with col1:
    depth = st.selectbox("설명 수준", ["간단", "중간", "상세"], index=1)

with col2:
    c1, c2 = st.columns(2)
    with c1:
        include_outline = st.checkbox("목차(아웃라인) 포함", value=True)
        # 기존의 '참고문헌/검색 쿼리 제안 포함' 체크박스 제거
        use_reference = st.checkbox("참고문헌 사용 (URL 입력)", value=False)
    with c2:
        include_examples = st.checkbox("실용적 예시 포함", value=True)
        include_next_steps = st.checkbox("다음 학습/연구 단계 제안", value=True)

# 참고문헌 URL 입력란 (체크하면 나타남)
ref_url = ""
if use_reference:
    ref_url = st.text_input("참고문헌 URL을 입력하세요 (예: https://example.com/article)", value="", placeholder="https://")

st.markdown("---")

# 프롬프트 템플릿 (기본)
query_template = '''당신은 해당 분야의 친절한 전문가입니다.
사용자가 지정한 주제에 대해 다음 요구사항을 충족하는 한국어 설명을 작성하세요.

요구사항:
- 주제: {topic}
- 설명 수준: {depth} (간단=한눈에 이해 가능한 요약, 중간=핵심 원리와 예시 포함, 상세=심화된 기술적 설명 및 응용 포함)
- 목차 포함 여부: {outline}
- 실용적 예시 포함 여부: {examples}
- 다음 학습/연구 단계 제안 포함 여부: {next_steps}

출력 형식 안내:
- Markdown 형식으로 출력하고, 각 섹션은 명확한 헤더(##)로 구분하세요.
- 가능한 경우 간단한 정의, 핵심 개념 정리(용어 설명), 실용적 예시(있다면 코드 스니펫 또는 실습 아이디어), 그리고 요약을 포함하세요.
- 요청된 항목(목차, 다음 단계)은 체크리스트 또는 번호 목록으로 제공하세요.

{reference_instruction}

자, 지금부터 위 규칙에 따라 작성하세요.
'''

prompt = PromptTemplate(
    input_variables=["topic", "depth", "outline", "examples", "next_steps", "reference_instruction"],
    template=query_template,
)

# --- helper: URL에서 텍스트 추출 시도 ---
def fetch_text_from_url(url: str, max_chars: int = 30000):
    try:
        headers = {"User-Agent": "Mozilla/5.0 (compatible; StreamlitApp/1.0)"}
        resp = requests.get(url, timeout=10, headers=headers)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        # 스크립트/스타일 제거
        for s in soup(["script", "style", "noscript"]):
            s.decompose()
        article = soup.find("article")
        if article:
            text = article.get_text(separator="\n")
        else:
            # 본문이 없으면 전체 텍스트(간단 정리)
            text = soup.get_text(separator="\n")
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        text = "\n".join(lines)
        if len(text) > max_chars:
            text = text[:max_chars] + "\n...[본문 생략: 길이 제한]..."
        return text
    except Exception as e:
        # 실패 시 None 반환 (프롬프트에 URL만 전달)
        return None

# 생성 버튼 (설명은 버튼을 눌렀을 때만 생성됨)
generate = st.button("설명 생성", key="generate_btn")

if generate:
    topic = st.session_state.get('input_text', '').strip()
    if not topic:
        st.info("먼저 설명할 주제를 입력하세요.")
    else:
        llm = getOpenAI()
        # 참고문헌이 있으면 시도해서 본문 가져오기
        reference_instr = "참고문헌을 사용하지 않습니다."
        if use_reference and ref_url:
            st.info("참고문헌에서 내용을 가져오는 중입니다...")
            fetched = fetch_text_from_url(ref_url)
            if fetched:
                # 프롬프트에 참고문헌 내용을 포함시키기 (LLM이 반드시 참고하도록 명시)
                reference_instr = ("아래 '참고문헌(추출된 본문)'을 반드시 참고하여, 해당 내용이 설명에 반영되도록 하세요.\n\n"
                                   "=== 참고문헌(추출된 본문 시작) ===\n"
                                   f"{fetched}\n"
                                   "=== 참고문헌(추출된 본문 끝) ===\n"
                                   f"원문 출처: {ref_url}\n"
                                   "위 출처의 사실과 주장에 충실하되, 필요하면 정리·요약하여 제시하세요.")
            else:
                # 본문 추출 실패 — URL만 프롬프트에 전달
                reference_instr = (f"참고문헌 본문을 자동으로 가져오지 못했습니다. 아래 URL을 참고문헌으로 사용하되, 모델이 자체적으로 해당 URL을 탐색/참조할 수 없을 수 있음을 염두에 두세요.\n"
                                   f"참고문헌 URL: {ref_url}\n"
                                   "가능하면 URL의 핵심 내용을 간단히 반영하여 설명을 구성하세요.")
        elif use_reference and not ref_url:
            st.warning("참고문헌 사용이 선택되었지만 URL이 비어 있습니다. URL을 입력하거나 참고문헌 사용을 해제하세요.")
            st.session_state['last_response'] = None

        # 템플릿에 값 채우기
        prompt_text = prompt.format(
            topic=topic,
            depth=depth,
            outline="예" if include_outline else "아니오",
            examples="예" if include_examples else "아니오",
            next_steps="예" if include_next_steps else "아니오",
            reference_instruction=reference_instr
        )

        # LLM 호출
        try:
            with st.spinner("설명 생성 중..."):
                response = llm.predict(prompt_text)
                # 새 설명이 생성되면 이전 요약/체크리스트 초기화
                st.session_state['last_response'] = response
                st.session_state.pop('summary', None)
                st.session_state.pop('checklist', None)
        except Exception as e:
            st.error(f"LLM 호출 중 오류가 발생했습니다: {e}")
            st.session_state['last_response'] = None

# 생성된 설명이 세션에 저장되어 있으면 표시
if st.session_state.get('last_response'):
    response = st.session_state['last_response']
    st.write(response)

    # 간단 요약 및 다음 단계 버튼
    st.markdown("---")
    st.markdown("### 빠른 액션")

    # -- 요약 생성 버튼 (결과는 session_state['summary']에 저장) --
    if st.button("요약 추출 (150자 이내)", key="summary_btn"):
        try:
            llm = getOpenAI()
            summary_prompt = f"다음 내용을 150자 이내로 한국어로 요약하세요:\n\n{response}"
            summary = llm.predict(summary_prompt)
            st.session_state['summary'] = summary
        except Exception as e:
            st.error(f"요약 중 오류: {e}")

    # -- 체크리스트 생성 버튼 (결과는 session_state['checklist']에 저장) --
    if st.button("학습 체크리스트 생성", key="checklist_btn"):
        try:
            llm = getOpenAI()
            checklist_prompt = f"다음 설명을 바탕으로 실제로 따라할 수 있는 학습 체크리스트(5단계 이내)를 한국어로 작성하세요:\n\n{response}"
            checklist = llm.predict(checklist_prompt)
            st.session_state['checklist'] = checklist
        except Exception as e:
            st.error(f"체크리스트 생성 중 오류: {e}")

    # -- 저장된 요약/체크리스트를 둘 다 보여줌 --
    if st.session_state.get('summary'):
        st.markdown("#### 요약 (150자 이내)")
        st.write(st.session_state['summary'])

    if st.session_state.get('checklist'):
        st.markdown("#### 학습 체크리스트")
        st.write(st.session_state['checklist'])

else:
    st.info("주제와 옵션을 입력한 뒤 '설명 생성' 버튼을 누르세요.")