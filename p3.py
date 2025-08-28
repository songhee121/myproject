# app.py
import os
from pathlib import Path
import uuid
import re
import streamlit as st

from openai import OpenAI  # openai>=1.0.0
from MyLCH import getOpenAI  # 기존 프로젝트의 LLM 래퍼 (요약용)

# ---------- 설정 ----------
st.markdown("# 녹음 내용 요약하기")
st.sidebar.markdown("녹음 내용을 글자로 전사하고 이를 요약할 수 있습니다.")

# OpenAI API 키 확인
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    st.error("환경변수 OPENAI_API_KEY가 설정되어 있지 않습니다. 먼저 API 키를 설정해주세요.")
    st.stop()

# OpenAI v1 클라이언트 생성
client = OpenAI(api_key=OPENAI_API_KEY)

# 저장 디렉터리
AUDIO_DIR = Path("audio")
AUDIO_DIR.mkdir(parents=True, exist_ok=True)

# ---------- 유틸 함수 ----------
def save_uploaded_file(uploaded_file) -> Path:
    """
    업로드된 파일을 FinalProject/audio에 고유 이름으로 저장하고 Path 반환
    """
    orig_name = uploaded_file.name
    unique_name = f"{Path(orig_name).stem}_{uuid.uuid4().hex}{Path(orig_name).suffix}"
    save_path = AUDIO_DIR / unique_name
    with open(save_path, "wb") as f:
        f.write(uploaded_file.read())
    return save_path

def transcribe_file_with_openai(path: Path) -> str | None:
    """
    OpenAI v1 client 를 사용한 Whisper 전사.
    성공 시 전사 텍스트 반환, 실패 시 None.
    """
    try:
        with open(path, "rb") as f:
            resp = client.audio.transcriptions.create(
                file=f,
                model="whisper-1"
            )
        # 응답에서 텍스트 획득 (dict 또는 객체 형태 가능)
        transcript = None
        if isinstance(resp, dict) and "text" in resp:
            transcript = resp["text"]
        else:
            transcript = getattr(resp, "text", None)
        return transcript
    except Exception as e:
        st.error(f"전사 중 오류 발생: {e}")
        return None

def split_into_sentences(text: str) -> list[str]:
    """
    간단한 문장 분리기.
    영어/한국어/일본어 등에서 기본 문장부호로 분리.
    (정교한 분할이 필요하면 별도 라이브러리 사용 권장)
    """
    if not text:
        return []
    # 연속 공백 제거
    text = re.sub(r'\s+', ' ', text).strip()

    # 분할 패턴: 영어/일본어/중국어/한글 문장종결부호 + 공백
    # 또한 한국어 종결형태(다.|요.|습니다.|습니까.) 뒤 공백도 고려
    pattern = r'(?<=[\.\?\!。！？\?])\s+|(?<=다\.)\s+|(?<=요\.)\s+|(?<=습니다\.)\s+|(?<=습니까\.)\s+'
    parts = re.split(pattern, text)
    # trim and remove empty
    sentences = [p.strip() for p in parts if p and p.strip()]
    return sentences

def call_llm_for_summary(llm, prompt: str) -> str | None:
    """
    프로젝트의 getOpenAI()로 얻은 LLM 래퍼를 여러 방식으로 호출해 요약 텍스트를 얻음.
    """
    try:
        # 먼저 predict 시도
        if hasattr(llm, "predict"):
            return llm.predict(prompt)
    except Exception:
        pass
    try:
        # __call__ 시도
        return llm(prompt)
    except Exception:
        pass
    try:
        # generate/generate_text 등 기타 메서드 시도 (fallback)
        if hasattr(llm, "generate"):
            return llm.generate(prompt)
    except Exception:
        pass
    return None

# ---------- 세션 상태 초기화 ----------
if 'saved_audio_path' not in st.session_state:
    st.session_state['saved_audio_path'] = None
if 'transcript_text' not in st.session_state:
    st.session_state['transcript_text'] = None
if 'sentences' not in st.session_state:
    st.session_state['sentences'] = []
if 'summary_text' not in st.session_state:
    st.session_state['summary_text'] = None

# ---------- UI: 파일 업로드 ----------
st.subheader("1) MP3 파일 업로드")
uploaded = st.file_uploader("오디오 파일 업로드 (.mp3, .wav, .m4a, .ogg, .webm 가능)", type=['mp3', 'wav', 'm4a', 'ogg', 'webm'])

if uploaded:
    # 저장 (한 번만 저장되도록)
    if st.session_state['saved_audio_path'] is None or uploaded.name not in str(st.session_state['saved_audio_path']):
        saved_path = save_uploaded_file(uploaded)
        st.session_state['saved_audio_path'] = str(saved_path)
        st.success(f"파일을 저장했습니다: {saved_path}")
    else:
        saved_path = Path(st.session_state['saved_audio_path'])
    # 플레이어 표시
    try:
        with open(saved_path, "rb") as f:
            st.audio(f.read(), format=f"audio/{saved_path.suffix.lstrip('.')}")
    except Exception:
        st.info(f"저장된 파일: {saved_path}")

# ---------- UI: 전사 버튼 ----------
st.subheader("2) 글자로 추출")
col1, col2 = st.columns([1,1])

with col1:
    if st.button("추출하기"):
        if not st.session_state.get('saved_audio_path'):
            st.error("먼저 오디오 파일을 업로드하세요.")
        else:
            chosen_path = Path(st.session_state['saved_audio_path'])
            st.info(f"전사 시작: {chosen_path}")
            transcript = transcribe_file_with_openai(chosen_path)
            if transcript is None:
                st.error("전사에 실패했습니다.")
            else:
                st.session_state['transcript_text'] = transcript
                sentences = split_into_sentences(transcript)
                st.session_state['sentences'] = sentences
                st.success("전사 및 문장화 완료.")

with col2:
    if st.button("추출내용 초기화"):
        st.session_state['transcript_text'] = None
        st.session_state['sentences'] = []
        st.success("전사 결과를 초기화했습니다.")

# ---------- 전사/문장화 결과 출력 ----------
if st.session_state.get('transcript_text'):
    st.subheader("전사 원문")
    st.write(st.session_state['transcript_text'])

if st.session_state.get('sentences'):
    st.subheader("문장 단위 전사 결과")
    for i, s in enumerate(st.session_state['sentences'], start=1):
        st.markdown(f"{i}. {s}")

# ---------- 요약 UI ----------
st.subheader("3) 요약")
summary_sentences = st.number_input("요약을 몇 문장으로 만들까요?", min_value=1, max_value=10, value=3, step=1)

if st.button("요약 생성"):
    if not st.session_state.get('transcript_text'):
        st.error("먼저 전사(문장화)를 실행하세요.")
    else:
        # LLM 호출
        st.info("요약 생성 중...")
        try:
            llm = getOpenAI()
        except Exception as e:
            st.error(f"getOpenAI() 호출 실패: {e}")
            llm = None

        if llm is None:
            st.error("LLM이 준비되지 않았습니다.")
        else:
            prompt = (
                f"아래는 음성 전사 텍스트입니다. 한국어로 핵심을 추려서 "
                f"간결하게 {summary_sentences}문장으로 요약해 주세요.\n\n"
                f"{st.session_state['transcript_text']}"
            )
            summary = call_llm_for_summary(llm, prompt)
            if summary:
                st.session_state['summary_text'] = summary
                st.success("요약 생성 완료.")
            else:
                st.error("LLM 호출로 요약을 생성하지 못했습니다.")

if st.session_state.get('summary_text'):
    st.subheader(f"요약 ({summary_sentences}문장 요청)")
    st.write(st.session_state['summary_text'])