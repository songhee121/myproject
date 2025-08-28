import streamlit as st
from PyPDF2 import PdfReader
from langchain.chains.question_answering import load_qa_chain
from langchain_community.callbacks import get_openai_callback
from MyLCH import process_text, getOpenAI

import json, re, ast

st.set_page_config(layout="wide")
st.markdown("# 개념 학습하기")
st.sidebar.markdown("요약 및 문제출제로 개념을 익히세요")

# ------------------------
# 세션 상태 초기화
# ------------------------
if 'mcq_questions' not in st.session_state:
    st.session_state['mcq_questions'] = None
if 'mcq_user_answers' not in st.session_state:
    st.session_state['mcq_user_answers'] = {}
if 'mcq_requested_n' not in st.session_state:
    st.session_state['mcq_requested_n'] = 3
if 'mcq_difficulty' not in st.session_state:
    st.session_state['mcq_difficulty'] = 'medium'

if 'summary_sentences' not in st.session_state:
    st.session_state['summary_sentences'] = 3
if 'summary_text' not in st.session_state:
    st.session_state['summary_text'] = None

if 'uploaded_pdf_name' not in st.session_state:
    st.session_state['uploaded_pdf_name'] = None

# 리셋 함수
def reset_on_new_upload():
    st.session_state['mcq_questions'] = None
    st.session_state['mcq_user_answers'] = {}
    st.session_state['summary_text'] = None

# ------------------------
# PDF 업로드
# ------------------------
pdf = st.file_uploader('PDF파일을 업로드해주세요', type='pdf')

current_pdf_name = getattr(pdf, "name", None)
if current_pdf_name != st.session_state['uploaded_pdf_name']:
    st.session_state['uploaded_pdf_name'] = current_pdf_name
    if current_pdf_name is not None:
        reset_on_new_upload()

if pdf is None:
    st.info("먼저 PDF 파일을 업로드하세요.")
    st.stop()

# ------------------------
# PDF에서 텍스트 및 전처리
# ------------------------
pdf_reader = PdfReader(pdf)
text = ""
for page in pdf_reader.pages:
    page_text = page.extract_text()
    if page_text:
        text += page_text

# 사용자 정의 전처리 함수
documents = process_text(text)

# ------------------------
# 유틸: 문제 생성 함수 (JSON 파싱 포함)
# ------------------------
def generate_mcq_from_llm(n, difficulty, choices_count=4):
    """
    LLM에 질의하여 문제를 생성하고, 파싱된 문제 리스트를 반환.
    실패 시 None 반환.
    """
    query = (
        f"업로드된 PDF 내용을 바탕으로 **객관식(선다형) {n}문항**을 만들어주세요. "
        f"난이도는 '{difficulty}'로 해주세요. (easy/medium/hard의 의미에 맞게 출제)\n"
        "응답은 반드시 **JSON 배열** 형식으로만 출력하세요. 배열의 각 원소는 다음 필드를 가져야 합니다:\n\n"
        " - question: (문항 text, 한국어)\n"
        f" - choices: (선택지 리스트, 길이 {choices_count}, 한국어)\n"
        " - answer: (정답 인덱스: 0부터 시작하는 정수)\n"
        " - explanation: (정답 해설/설명, 한국어)\n\n"
        "예시 출력 형식:\n"
        '[{"question":"...","choices":["A","B","C","D"],"answer":1,"explanation":"..."}, ...]\n\n'
        "위 규격을 정확히 지켜서 유효한 JSON만 출력해주세요."
    )

    try:
        docs = documents.similarity_search("핵심 개념 요약")
        llm = getOpenAI()
        chain = load_qa_chain(llm, chain_type='stuff')
        with get_openai_callback() as cb:
            raw = chain.run(input_documents=docs, question=query)
    except Exception as e:
        st.error(f"LLM 호출 중 오류가 발생했습니다: {e}")
        return None

    # JSON 추출 시도
    json_text = None
    m1 = re.search(r'(\[.*\])', raw, re.DOTALL)
    if m1:
        json_text = m1.group(1)
    else:
        m2 = re.search(r'(\{.*\})', raw, re.DOTALL)
        if m2:
            json_text = "[" + m2.group(1) + "]"

    questions = None
    if json_text:
        try:
            questions = json.loads(json_text)
        except Exception:
            try:
                questions = ast.literal_eval(json_text)
            except Exception:
                questions = None

    if questions is None:
        st.warning("LLM이 출력한 JSON을 자동 파싱하지 못했습니다. 원본 응답을 아래에서 확인하세요.")
        st.subheader("원본 응답 (LLM)")
        st.write(raw)
        st.error("자동 파싱 실패: 올바른 JSON 형식으로 재생성하거나 포맷을 확인하세요.")
        return None

    # 유효성 검사 및 n에 맞춰 자르기/경고
    if not isinstance(questions, list):
        st.error("LLM 출력이 리스트(배열)가 아닙니다.")
        return None

    if len(questions) > n:
        st.warning(f"LLM이 {len(questions)}문항을 생성했습니다. 요청한 {n}문항만 사용합니다.")
        questions = questions[:n]
    if len(questions) < n:
        st.warning(f"LLM이 {len(questions)}문항만 생성했습니다. 요청한 {n}문항보다 적습니다. 생성된 만큼만 표시합니다.")

    # 각 문항 검사
    for idx, q in enumerate(questions):
        if not all(k in q for k in ("question","choices","answer","explanation")):
            st.error(f"{idx+1}번 문항에 필수 필드가 없습니다.")
            return None
        if not isinstance(q['choices'], list) or len(q['choices']) != choices_count:
            st.error(f"{idx+1}번 문항의 선택지가 {choices_count}개가 아닙니다.")
            return None

    return questions

# ------------------------
# 상단: 요약 설정(문장 수) 및 문제 설정(문항 수, 난이도)
# ------------------------
st.header("설정")

with st.form("settings_form", clear_on_submit=False):
    col_a, col_b = st.columns(2)

    with col_a:
        st.subheader("요약 설정")
        m = st.number_input("요약 문장 수 (줄 수)", min_value=1, max_value=10, value=st.session_state['summary_sentences'], step=1, key="ui_summary_sentences")
        st.write("요약을 만들려면 아래 '요약 생성' 버튼을 누르세요.")
        summary_submit = st.form_submit_button("요약 생성")

    with col_b:
        st.subheader("문제 출제 설정")
        n = st.number_input("생성할 객관식 문항 수 (n)", min_value=1, max_value=10, value=st.session_state['mcq_requested_n'], step=1, key="ui_mcq_n")
        difficulty = st.selectbox("난이도", options=["easy", "medium", "hard"], index=["easy","medium","hard"].index(st.session_state['mcq_difficulty']), key="ui_mcq_diff")
        st.write("설정을 마친 뒤 아래 '문제 생성' 버튼을 누르면 바로 문제가 출제됩니다.")
        # 이 버튼을 누르면 즉시 문제를 생성하도록 동작함
        create_mcq = st.form_submit_button("문제 생성")

    # 폼 제출 시 세션에 설정 저장
    st.session_state['summary_sentences'] = m
    st.session_state['mcq_requested_n'] = n
    st.session_state['mcq_difficulty'] = difficulty

# ------------------------
# 요약 생성 처리 (요약 생성 버튼 클릭 시)
# ------------------------
if 'summary_text' not in st.session_state:
    st.session_state['summary_text'] = None

if summary_submit:
    m = st.session_state['summary_sentences']
    summary_query = f"업로드된 PDF 파일의 핵심 내용을 {m}문장으로 간결하게 요약해주세요."
    with st.spinner("요약 생성 중..."):
        try:
            docs = documents.similarity_search(summary_query)
            llm = getOpenAI()
            chain = load_qa_chain(llm, chain_type='stuff')
            with get_openai_callback() as cb:
                response = chain.run(input_documents=docs, question=summary_query)
            st.session_state['summary_text'] = response
            st.success("요약이 생성되었습니다.")
        except Exception as e:
            st.error(f"요약 생성 중 오류 발생: {e}")

# 요약 보여주기 (이미 생성되어 있으면)
if st.session_state.get('summary_text'):
    st.subheader(f"--요약 ({st.session_state['summary_sentences']}문장)--")
    st.write(st.session_state['summary_text'])

# ------------------------
# 문제 생성: 폼 내 '문제 생성' 버튼 클릭 시 즉시 실행
# ------------------------
if create_mcq:
    n = st.session_state['mcq_requested_n']
    difficulty = st.session_state['mcq_difficulty']
    with st.spinner("문제 생성 중..."):
        questions = generate_mcq_from_llm(n=n, difficulty=difficulty, choices_count=4)
        if questions:
            st.session_state['mcq_questions'] = questions
            st.session_state['mcq_user_answers'] = {}
            st.success("문제가 생성되어 아래에 표시됩니다.")

# ------------------------
# 생성된 문제 표시 및 채점
# ------------------------
if st.session_state.get('mcq_questions'):
    st.subheader(f"--생성된 객관식 문제 ({len(st.session_state['mcq_questions'])}문항)--")
    questions = st.session_state['mcq_questions']

    for i, q in enumerate(questions):
        st.markdown(f"**문제 {i+1}.** {q['question']}")
        choices = q['choices']
        labelled = [f"{chr(65 + j)}. {choices[j]}" for j in range(len(choices))]
        key = f"mcq_select_{i}"
        default_index = st.session_state['mcq_user_answers'].get(key, None)
        try:
            radio_index = default_index if default_index is not None else 0
            selected = st.radio("", labelled, index=radio_index, key=key)
        except Exception:
            selected = st.radio("", labelled, key=key)
        selected_index = labelled.index(selected)
        st.session_state['mcq_user_answers'][key] = selected_index
        st.markdown("---")

    if st.button("제출 및 채점"):
        total = len(questions)
        correct_count = 0
        st.subheader("채점 결과")
        for i, q in enumerate(questions):
            user_idx = st.session_state['mcq_user_answers'].get(f"mcq_select_{i}", None)
            try:
                correct_idx = int(q['answer'])
            except Exception:
                st.error(f"{i+1}번 문항의 정답 인덱스가 올바르지 않습니다: {q.get('answer')}")
                continue

            choices = q['choices']
            user_text = choices[user_idx] if (user_idx is not None and 0 <= user_idx < len(choices)) else "선택 없음"
            correct_text = choices[correct_idx] if 0 <= correct_idx < len(choices) else "정답 데이터 오류"
            if user_idx == correct_idx:
                correct_count += 1
                st.success(f"문제 {i+1}: 정답 ({chr(65+correct_idx)}). {correct_text}")
            else:
                user_letter = chr(65+user_idx) if user_idx is not None else '-'
                st.error(f"문제 {i+1}: 오답 — 선택: {user_letter} {user_text} / 정답: {chr(65+correct_idx)} {correct_text}")
            st.markdown(f"**해설:** {q.get('explanation','(해설 없음)')}")
            st.markdown("---")
        st.info(f"총점: {correct_count} / {total}")

# ------------------------
# 파일 다운로드 / 초기화 섹션 (선택사항)
# ------------------------
st.write("")
if st.button("문제와 요약 초기화"):
    reset_on_new_upload()
    st.session_state['summary_text'] = None
    st.success("요약과 문제가 초기화되었습니다.")