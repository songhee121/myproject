
import streamlit as st

Main_page = st.Page("main.py", title= "Main Page", icon= "📖")
page_1 = st.Page("p1.py", title="page 1", icon="📖")
page_2 = st.Page("p2.py", title="개념 학습하기", icon="📖")
page_3 = st.Page("p3.py", title="학습자료로 질문하기", icon="🙋")
page_4 = st.Page("p4.py", title="녹음 내용 요약하기", icon="🎙️")
page_5 = st.Page("p5.py", title="녹음 및 파일로 저장하기", icon="🎤 ")
page_8 = st.Page("p8.py", title="채팅하기", icon="💬")

page = st.navigation([Main_page, page_1, page_2, page_3, page_4, page_5, page_8])

page.run()
