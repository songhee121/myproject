import os
import streamlit as st
from st_audiorec import st_audiorec

def save_uploadedfile(directory, data, filename, st):
    # 1. 디렉토리가 없으면 생성
    if not os.path.exists(directory):
        os.makedirs(directory)
    # 2. 파일 저장
    with open(os.path.join(directory, filename), 'wb') as f:
        f.write(data)
    # 3. 저장 완료 메시지 출력
    st.success(f'저장 완료: {directory}에 {filename}이 저장되었습니다.')

st.markdown("🎤 녹음 및 파일로 저장하기")

# 녹음
audio_data = st_audiorec()

if audio_data:
    filename = st.text_input("저장할 파일 이름: ", "my_record")
    filetype = st.selectbox("파일 타입 선택:", ["wav", "mp3", "m4a", "ogg", "webm"])

    if filename and filetype :
        filename= f"{filename}.{filetype}"
        save_uploadedfile("audio", audio_data, filename, st)
        st.download_button(
            label="파일 다운로드",
            data=audio_data,
            file_name=filename,
            mime="audio/wav"
        )