import streamlit as st

from MyLCH import getOpenAI, makeAudio, progressBar, getGenAI

import streamlit as st

# 페이지 설정
st.set_page_config(
    page_title="공부 어플",
    page_icon="📚",
    layout="wide"
)

# CSS 스타일
st.markdown("""
    <style>
    /* 메인 배경 */
    .stApp {
        background: linear-gradient(135deg, #E0F7FA, #FFFFFF);
    }

    /* 헤더 텍스트 */
    .big-title {
        font-size: 48px;
        font-weight: 800;
        color: #00796B;
        text-align: center;
        margin-top: 20px;
    }

    .sub-title {
        font-size: 20px;
        text-align: center;
        color: #555;
        margin-bottom: 40px;
    }

    /* 카드 스타일 */
    .feature-card {
        background-color: white;
        padding: 20px;
        border-radius: 20px;
        box-shadow: 2px 2px 15px rgba(0,0,0,0.1);
        text-align: center;
    }
    </style>
""", unsafe_allow_html=True)

# 메인 타이틀
st.markdown('<p class="big-title">📚 AI 학습 메이트</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">집중력 올려주는 기능들을 한 곳에서</p>', unsafe_allow_html=True)

# 기능 카드 나열
col1, col2, col3 = st.columns(3)
st.write("")
col4, col5, col6 = st.columns(3)
st.write("")
col7, col8 = st.columns(2)
with col1:
    st.markdown('<div class="feature-card">📖<br><b>개념 학습</b><br>어려운 개념을 쉽게 정리해 드려요</div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="feature-card">🙋<br><b>질의 응답</b><br>자료를 기반으로 AI에게 바로 물어보세요</div>', unsafe_allow_html=True)

with col3:
    st.markdown('<div class="feature-card">🎙️<br><b>녹음 요약</b><br>길게 들은 강의, 핵심만 간단히 정리</div>', unsafe_allow_html=True)

with col4:
    st.markdown('<div class="feature-card">🎧<br><b>설명문 보기</b><br>교재와 설명문을 한눈에 확인</div>', unsafe_allow_html=True)

with col5:
    st.markdown('<div class="feature-card">📝<br><b>채팅하기</b><br>궁금한 점은 바로 대화로 해결</div>', unsafe_allow_html=True)

with col6:
    st.markdown('<div class="feature-card">📊<br><b>찍어서 살펴보기</b><br>사진으로 찍은 자료도 분석해 드려요</div>', unsafe_allow_html=True)

with col7:
    st.markdown('<div class="feature-card">🧭<br><b>스터디 플래너</b><br>나만의 학습 계획을 손쉽게 관리</div>', unsafe_allow_html=True)

with col8:
    st.markdown('<div class="feature-card">📆️<br><b>달력에 메모하기</b><br>날짜별로 중요한 메모를 정리해 보세요</div>', unsafe_allow_html=True)