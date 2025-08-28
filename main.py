import streamlit as st

from MyLCH import getOpenAI, makeAudio, progressBar, getGenAI

st.markdown("LangChain Main Page")
st.sidebar.markdown("Clicked Main Page")


text = st.text_area(label="질문입력:",   placeholder="질문을 입력 하세요")
selected_option = st.radio("언어를 선택하세요", ("gpt", "gemini"))

if st.button("SEND"):
    if text:
        st.info(text)
        makeAudio(text, "temp.mp3")
        st.audio("audio/temp.mp3", autoplay=True, width=1)
        llm = None
        if selected_option == 'gpt':
            llm = getOpenAI()
        else:
            llm = getGenAI()
        my_bar = progressBar("Loading .....")
        result = llm.predict(text)
        st.info(result)
        makeAudio(result, "result.mp3")
        st.audio("audio/result.mp3", autoplay=True, width=1)
        my_bar.empty()

    else:
        st.info("질문을 입력하세요")