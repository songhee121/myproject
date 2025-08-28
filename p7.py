# study_planner_from_pdf_updated.py
import streamlit as st
import tempfile
import json
import re
from datetime import datetime, timedelta, date
import math
import pandas as pd

# PDF loader (langchain community)
try:
    from langchain_community.document_loaders import PyPDFLoader
except Exception:
    PyPDFLoader = None

from langchain_core.prompts import PromptTemplate
from MyLCH import getOpenAI

st.title("스터디 플래너")
st.sidebar.markdown("학습자료 PDF를 업로드하면 스터디 플랜을 설계하여 표로 보여줍니다.")

# --- 레이아웃: 왼쪽 업로드/문서, 오른쪽 설정/생성/결과 ---
col_left, col_right = st.columns([1, 1.2])

with col_left:
    st.subheader("1) PDF 업로드")
    uploaded_file = st.file_uploader("PDF 파일을 업로드하세요", type=["pdf"])
    full_text = None
    num_pages = 0
    if uploaded_file:
        if PyPDFLoader is None:
            st.error("PyPDFLoader가 설치되어 있지 않습니다. 'langchain-community'를 설치하세요.")
        else:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                tmp.write(uploaded_file.getvalue())
                tmp_path = tmp.name
            try:
                loader = PyPDFLoader(tmp_path)
                pages = loader.load()
                num_pages = len(pages)
                # 문서 전체를 그대로 사용(내부적으로 필요시 요약은 조용히 수행)
                full_text = "\n\n".join([p.page_content for p in pages])
                st.success(f"문서 로드 완료 — {num_pages} 페이지")

            except Exception as e:
                st.error(f"PDF 로드 실패: {e}")
    else:
        st.info("먼저 PDF를 업로드하세요.")

with col_right:
    st.subheader("2) 스케줄 / 플랜 설정 (메인 화면)")
    # 시작/종료 및 플랜 유형
    start_date = st.date_input("학습 시작일", value=date.today())
    end_date = st.date_input("학습 종료일", value=date.today() + timedelta(weeks=4))
    # 플랜 보기 유형은 시작일과 종료일 다음 위치
    plan_view = st.selectbox("플랜 보기 유형", ["일간", "주간"], index=0)

    # plan_view에 따른 추가 입력
    if plan_view == "일간":
        st.markdown("**일간 플랜 입력**")
        daily_study_minutes = st.number_input("당일 공부 시간(분)", min_value=5, max_value=24*60, value=60)
        # for downstream usage we'll set variables uniformly
        sessions_per_week = None
        per_session_minutes = daily_study_minutes
    else:  # 주간
        st.markdown("**주간 플랜 입력**")
        study_days_per_week = st.number_input("주당 공부하는 일 수", min_value=1, max_value=7, value=3)
        daily_study_minutes = st.number_input("일당 스터디 시간(분)", min_value=5, max_value=24*60, value=60)
        sessions_per_week = int(study_days_per_week)
        per_session_minutes = int(daily_study_minutes)

    depth = st.selectbox("설명 수준", ["간단", "중간", "상세"], index=1)

    st.markdown("---")
    generate = st.button("스터디 플랜 생성")

# ---------------- Helper functions ----------------
def extract_json_from_text(text):
    """
    LLM의 응답에서 JSON 객체를 추출해 파싱 시도.
    """
    m = re.search(r'\{.*\}', text, flags=re.S)
    if m:
        candidate = m.group(0)
        try:
            return json.loads(candidate)
        except Exception:
            candidate2 = candidate.replace("'", "\"")
            try:
                return json.loads(candidate2)
            except Exception:
                return None
    m2 = re.search(r'\[.*\]', text, flags=re.S)
    if m2:
        try:
            return json.loads(m2.group(0))
        except Exception:
            return None
    return None

def generate_dates_by_view(start_date, end_date, plan_view, sessions_per_week=None, study_days_per_week=None):
    """
    plan_view에 따라 각 세션 날짜 목록 반환.
    - 일간: start..end의 모든 날짜 (각 날짜가 하나의 세션)
    - 주간: 전체 기간 동안 주 단위로 study_days_per_week 만큼 스케줄 (평일 우선으로 배치)
    """
    dates = []
    if start_date > end_date:
        return dates
    if plan_view == "일간":
        cur = start_date
        while cur <= end_date:
            dates.append(cur)
            cur += timedelta(days=1)
        return dates
    else:  # 주간
        # 전체 주 수 (partial week도 포함)
        total_days = (end_date - start_date).days + 1
        total_weeks = math.ceil(total_days / 7)
        # For each week, pick study_days_per_week days starting from start_date's weekday
        cur = start_date
        for w in range(total_weeks):
            # pick days in the week: we'll choose earliest available days (Mon-Sun) starting from cur
            picked = 0
            d = cur
            # iterate within this 7-day window
            for i in range(7):
                if d > end_date:
                    break
                if picked < study_days_per_week:
                    dates.append(d)
                    picked += 1
                d += timedelta(days=1)
            cur = cur + timedelta(days=7)
        return dates

def silent_summarize_if_needed(llm_client, full_text, max_chars=12000):
    """
    내부적으로 (화면에 표시하지 않고) 요약해서 리턴.
    - 만약 문서가 max_chars 이하이면 원문 반환.
    - 초과하면 요약 프롬프트를 LLM에 보내 요약을 받고 반환한다. (요약 과정은 화면에 노출 X)
    """
    if not full_text:
        return ""
    if len(full_text) <= max_chars:
        return full_text
    # 요약 프롬프트 (간단하게 중심 내용, 목차 추출)
    sum_prompt = PromptTemplate(
        input_variables=["doc_text"],
        template=(
            "다음 긴 문서를 핵심 항목(한두 문단 요약 + 핵심 섹션 제목 목록)으로 요약하시오. "
            "출력은 요약문(한 문단)과 '-'로 시작하는 섹션명 목록으로 구성하시오.\n\n문서:\n{doc_text}"
        )
    )
    try:
        p = sum_prompt.format(doc_text=full_text)
        summary = llm_client.predict(p)
        # 요약 결과 자체가 LLM에 보낼 적절한 요약 텍스트로 사용
        return summary
    except Exception:
        # 요약 실패 시에도 조용히 원문 일부라도 반환(최악).
        return full_text[:12000]

# ---------------- Generation logic ----------------
if generate:
    if not full_text:
        st.error("PDF를 먼저 업로드하세요.")
    elif start_date > end_date:
        st.error("학습 시작일이 학습 종료일보다 빠르도록 설정하세요.")
    else:
        llm = getOpenAI()

        # 내부적으로 적절히 요약(사용자에게는 보이지 않음)
        doc_for_prompt = silent_summarize_if_needed(llm, full_text)

        # 날짜 목록 생성 및 세션 수 결정
        if plan_view == "일간":
            dates = generate_dates_by_view(start_date, end_date, "일간")
            total_sessions = len(dates)
            per_session_minutes = int(daily_study_minutes)
        else:  # 주간
            dates = generate_dates_by_view(start_date, end_date, "주간", study_days_per_week=sessions_per_week)
            total_sessions = len(dates)
            per_session_minutes = int(per_session_minutes)  # already set above

        # 프롬프트: LLM에게 start/end, plan_view, 입력한 시간/빈도, 총 세션 수 반영하도록 명확히 지시
        plan_template = PromptTemplate(
            input_variables=["doc_summary", "start_date", "end_date", "plan_view", "total_sessions", "per_session_minutes", "depth"],
            template=(
                "당신은 교육 설계자입니다. 아래 문서 요약을 참고하여, 학습 시작일({start_date})부터 학습 종료일({end_date})까지, "
                "플랜 보기 유형({plan_view})과 아래 지정된 제약을 반영하여 총 {total_sessions}개의 세션(Session)으로 학습 계획을 구성하세요.\n\n"
                "언어는 한국어로 하시오.\n"
                "제약 및 요구사항:\n"
                "- 각 세션의 권장 소요 시간은 약 {per_session_minutes}분입니다.\n"
                "- 플랜 보기 유형이 '일간'이면 하루에 하나의 세션을, '주간'이면 주당 정해진 일수만큼 세션을 분배하세요.\n"
                "- 각 세션에는 session_no, title, objective(학습 목표), tasks(실행 가능한 단계 목록, 최대 5개), estimated_minutes 필드를 포함하세요.\n"
                "- 가능한 경우 각 세션을 해당 날짜(예: 2025-08-30)와 매핑해 출력하세요. (하지만 날짜 매핑은 클라이언트에서 다시 조정해도 됩니다.)\n"
                "- 난이도/설명 수준: {depth}\n"
                "- 출력 형식: JSON object: {{\"sessions\": [ ... ], \"notes\": \"(선택적 메모)\"}}\n\n"
                "문서 요약(혹은 요약된 핵심):\n{doc_summary}\n\n"
                "예시 출력:\n{{\n  \"sessions\": [{{\"session_no\":1, \"title\":\"...\", \"objective\":\"...\", \"tasks\":[\"...\"], \"estimated_minutes\":60}}],\n  \"notes\": \"...\"\n}}\n"
            )
        )

        try:
            plan_prompt = plan_template.format(
                doc_summary=doc_for_prompt,
                start_date=start_date.isoformat(),
                end_date=end_date.isoformat(),
                plan_view=plan_view,
                total_sessions=total_sessions,
                per_session_minutes=per_session_minutes,
                depth=depth
            )
            with st.spinner("스터디 플랜을 생성 중입니다..."):
                plan_text = llm.predict(plan_prompt)
        except Exception as e:
            st.error(f"스터디 플랜 생성 중 오류가 발생했습니다: {e}")
            plan_text = None

        if not plan_text:
            st.error("LLM 응답을 받지 못했습니다.")
        else:
            plan_json = extract_json_from_text(plan_text)
            if plan_json is None:
                # 파싱 실패 시 원문 확인 가능
                st.warning("LLM 응답에서 JSON을 추출하지 못했습니다. 원문을 확인하세요.")
                st.code(plan_text)
            else:
                sessions = plan_json.get("sessions", [])
                # 만약 LLM이 날짜를 주지 않았다면 클라이언트 측 dates로 매핑
                # sessions 길이와 dates 길이가 다르면 가능한 만큼 매핑
                mapped = []
                for idx, s in enumerate(sessions):
                    assigned_date = dates[idx] if idx < len(dates) else None
                    tasks = s.get("tasks", [])
                    if isinstance(tasks, str):
                        tasks = [t.strip() for t in tasks.splitlines() if t.strip()]
                    mapped.append({
                        "date": assigned_date.isoformat() if assigned_date else "",
                        "session_no": s.get("session_no", idx+1),
                        "title": s.get("title", f"Session {idx+1}"),
                        "objective": s.get("objective", ""),
                        "tasks": tasks,
                        "estimated_minutes": s.get("estimated_minutes", per_session_minutes)
                    })

                df = pd.DataFrame(mapped)
                # tasks는 보기 좋게 합치기
                df["tasks"] = df["tasks"].apply(lambda x: " | ".join(x) if isinstance(x, list) else x)

                st.markdown("### 생성된 스터디 플랜 (표)")
                st.dataframe(df)

                # 다운로드
                csv_buf = df.to_csv(index=False)
                st.download_button("표 다운로드 (CSV)", csv_buf.encode("utf-8"), file_name=f"study_plan_{datetime.now().strftime('%Y%m%d_%H%M')}.csv")
                out = {
                    "meta": {
                        "source_filename": uploaded_file.name if uploaded_file else "unknown",
                        "generated_at": datetime.now().isoformat(),
                        "start_date": start_date.isoformat(),
                        "end_date": end_date.isoformat(),
                        "plan_view": plan_view
                    },
                    "plan_json": plan_json,
                    "schedule": mapped
                }