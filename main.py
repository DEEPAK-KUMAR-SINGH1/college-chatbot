import time
import re
import streamlit as st
from dotenv import load_dotenv

from langchain_community.document_loaders import YoutubeLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_mistralai import MistralAIEmbeddings
from langchain_chroma import Chroma
from langchain_mistralai import ChatMistralAI
from langchain_core.prompts import ChatPromptTemplate
from typing import TypedDict
from langgraph.graph import StateGraph,START,END

load_dotenv()

llm=ChatMistralAI(model_name='mistral-large-2512')
llm_embeddings = MistralAIEmbeddings(model='mistral-embed')

def fatch_transcript(url):
    urls = YoutubeLoader.from_youtube_url(url,language='hi'or'en')
    content = urls.load()[0].page_content
    text_splitter = RecursiveCharacterTextSplitter(chunk_size = 1000,chunk_overlap = 200)
    text_split = text_splitter.split_text(content)
    
class GraphState(TypedDict):
    question:str
    context:str
    answer:str



workflow = StateGraph(GraphState)

workflow.add_node("retrieve", retrieve)
workflow.add_node("generate", generate)

workflow.set_entry_point("retrieve")
workflow.add_edge("retrieve", "generate")
workflow.add_edge("generate", END)

app = workflow.compile()