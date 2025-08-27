import streamlit as st
from PIL import Image
from MYLLM import progress_bar, makeImage

#Side Bar
st.sidebar.markdown("Clicked Page 11")

#Page
st.title("Page 11")

text=st.text_area(label="질문입력: ",
                  placeholder="질문을 입력 하세요.")
name=st.text_input(label="이미지 이름: ",
                  placeholder="이미지 이름을 입력 하세요.")
if st.button("SEND"): #버튼 클릭시
    if text and name: #텍스트 존재시
        st.info(text)
        makeImage(text, name)
        my_bar=progress_bar("processing. . .")
        my_bar.empty()

        with open('img/'+name, "rb")as file:
            st.download_button(
                label="파일 다운로드",
                data=file,
                file_name='img/'+name,
                mime="image/jpg"
            )
        img=Image.open('img/'+name)
        st.image(img)

    else:
        st.info("다시 입력 하세요.")