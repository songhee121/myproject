import streamlit as st

from MyLLM import save_carpturefile, encode_image, openAiModel, progressBar, makeAudio

# Sidebar
st.sidebar.markdown("직접 사진을 촬영하여 관련된 정보를 살펴봅니다.")

# Page
st.title("찍어서 살펴보기")

picture = st.camera_input("Take a picture")
if picture:
    st.info("이미지를 캡쳐 했습니다.")
    save_carpturefile("capture", picture, "capturetemp.png", st)
    text = st.text_area(label="질문입력:",  placeholder="질문을 입력 하세요")

    if st.button("SEND"):
        base64img = encode_image("capture/capturetemp.png")
        model = openAiModel()
        my_bar = progressBar("Operation in progress. Please wait.")
        response = model.chat.completions.create(
            model='gpt-4o',
            messages=[
                {"role": "system", "content": "당신은 꼼꼼한 선생님입니다. 사진에 보이는 내용을 적절히 해석하여 도움이 될 만한 지식을 상세히 제공합니다."},
                {"role": "user", "content": [
                    {"type": "text", "text": text},
                    {"type": "image_url", "image_url": {
                        "url": f"data:image/jpg;base64,{base64img}"}
                     }
                ]}
            ],
            temperature=0.0,
        )
        my_bar.empty()

        # 결과를 출력하고
        # 음성으로 안내한다
        st.info(response.choices[0].message.content)
        makeAudio(response.choices[0].message.content, "img_capture_result.mp3")
        st.audio("audio/img_capture_result.mp3", autoplay=True, width=1)