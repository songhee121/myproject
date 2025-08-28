import base64
import time
import urllib

import google.generativeai as genai
from dotenv import load_dotenv
import os
import streamlit as st
from openai import OpenAI

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
#GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]

def openAiModel():
    client = OpenAI(api_key=OPENAI_API_KEY)
    return client

def makeMsg(system,user ):
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]
    return messages

def openAiModelArg(model, msgs):
    print(model)
    print(msgs)
    client = OpenAI(api_key=OPENAI_API_KEY)
    response = client.chat.completions.create(
        model=model,
        messages=msgs
    )
    return response.choices[0].message.content


def geminiModel():
    genai.configure(api_key=GOOGLE_API_KEY)
    model = genai.GenerativeModel("gemini-2.0-flash")
    return model

def geminiTxt(txt):
    model = geminiModel()
    response = model.generate_content(txt)
    return response.text

def save_carpturefile(directory, picture, name, st):
    if picture is not None:
        if not os.path.exists(directory):
            os.makedirs(directory)
        # 2. 파일 저장 (이름 변경 없이 저장)
        with open(os.path.join(directory, name), 'wb') as file:
            file.write(picture.getvalue())
        # 3. 저장 완료 메시지 출력
        st.success(f'저장 완료: {directory}에 {name} 저장되었습니다.')

def save_uploadedfile(directory, file, st):
    # 1. 디렉토리가 없으면 생성
    if not os.path.exists(directory):
        os.makedirs(directory)
    # 2. 파일 저장 (이름 변경 없이 저장)
    with open(os.path.join(directory, file.name), 'wb') as f:
        f.write(file.getbuffer())
    # 3. 저장 완료 메시지 출력
    st.success(f'저장 완료: {directory}에 {file.name} 저장되었습니다.')


def progressBar(txt):
    # Progress Bar Start -----------------------------------------
    progress_text = txt
    my_bar = st.progress(0, text=progress_text)
    for percent_complete in range(100):
        time.sleep(0.08)
        my_bar.progress(percent_complete + 1, text=progress_text)
    time.sleep(1)
    return my_bar
    # Progress Bar End -----------------------------------------

def makeAudio(text, name):
    if not os.path.exists("audio"):
        os.makedirs("audio")
    model = openAiModel()
    response = model.audio.speech.create(
        model="tts-1",
        input=text,
        #["alloy", "echo", "fable", "onyx", "nova", "shimmer"],
        voice="echo",
        response_format="mp3",
        speed=1.2,
    )
    response.stream_to_file("audio/"+name)


def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

def makeImage(prompt, name):
    if not os.path.exists("img"):
        os.makedirs("img")
    openModel = openAiModel()
    response = openModel.images.generate(
        model="dall-e-3",
        prompt=prompt,
        size="1024x1024",
        quality="standard",
        n=1,
    )
    image_url = response.data[0].url
    print(image_url)
    imgName = "img/"+name
    urllib.request.urlretrieve(image_url,  imgName)

def makeImages(prompt, name, num):
    if not os.path.exists("img"):
        os.makedirs("img")
    openModel = openAiModel()
    response = openModel.images.generate(
        model="dall-e-2",
        prompt=prompt,
        size="1024x1024",
        n=num,
    )
    for n,data in enumerate(response.data):
        print(n)
        print(data.url)
        imgname = f"img/{name.split('.')[0]}_{n}.png"
        urllib.request.urlretrieve(data.url, imgname)

def cloneImage(imgName, num):
    if not os.path.exists("img"):
        os.makedirs("img")
    openModel = openAiModel()
    response = openModel.images.create_variation(
        model="dall-e-2",
        image=open("img/"+imgName, "rb"),
        n=num,
        size="1024x1024"
    )
    for n,data in enumerate(response.data):
        print(n)
        print(data.url)
        name = f"img/{imgName.split('.')[0]}_clone_{n}.png"
        urllib.request.urlretrieve(data.url, name)