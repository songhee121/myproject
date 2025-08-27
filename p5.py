import streamlit as st
from st_audiorec import st_audiorec
from MYLLM import save_uploadedfile

st.markdown("🎤 녹음 및 파일로 저장하기")

# 녹음
audio_data = st_audiorec()

if audio_data:
    st.audio(audio_data, format="audio/wav")
    filename = st.text_input("저장할 파일 이름(확장자 제외): ", "my_record")

    if filename:
        save_uploadedfile("audio", audio_data, st)
        st.download_button(
            label="파일 다운로드",
            data=audio_data,
            file_name=filename,
            mime=f"audio/wav"
        )