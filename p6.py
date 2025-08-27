import streamlit as st
import pandas as pd
from langchain.agents import AgentType
from langchain_experimental.agents.agent_toolkits import create_pandas_dataframe_agent

from MyLCH import getOpenAI

st.markdown("Page6")
st.sidebar.markdown("Clicked Page6")

df = pd.read_csv('data/booksv_02.csv')

agent = create_pandas_dataframe_agent(
    getOpenAI(),
    df,             #데이터가 담긴 곳
    verbose=False,  #추론 과정을 출력하지 않음
    agent_type=AgentType.OPENAI_FUNCTIONS,
    allow_dangerous_code=True,
)
input_text = st.text_area(label="질문 입력", label_visibility='collapsed',
                          placeholder="질문 입력...")
if st.button("SEND"):
    if input_text:
        st.info(agent.run(input_text))
    else:
        st.info("질문 입력")