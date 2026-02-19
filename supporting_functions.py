from dotenv import load_dotenv
import re
import streamlit as st

from langchain_community.document_loaders import YoutubeLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_mistralai import MistralAIEmbeddings
from langchain_chroma import Chroma
from langchain_mistralai import ChatMistralAI
from langchain_core.prompts import ChatPromptTemplate
load_dotenv()

llm= ChatMistralAI(
    model="mistral-small-2506",
    #temperature=0.2
)


def fatch_transcript(url):
    urls = YoutubeLoader.from_youtube_url(url,language='hi'or'en')
    content = urls.load()[0].page_content
    text_splitter = RecursiveCharacterTextSplitter(chunk_size = 1000,chunk_overlap = 200)
    text_split = text_splitter.split_text(content)
    prompt=ChatPromptTemplate.from_template("""
        You are an expert translator with deep cultural and linguistic knowledge.
        I will provide you with a transcript. Your task is to translate it into English with absolute accuracy, preserving:
        - Full meaning and context (no omissions, no additions).
        - Tone and style (formal/informal, emotional/neutral as in original).
        - Nuances, idioms, and cultural expressions (adapt appropriately while keeping intent).
        - Speaker’s voice (same perspective, no rewriting into third-person).
        Do not summarize or simplify. The translation should read naturally in the target language but stay as close as possible to the original intent.

        Transcript:{transcript}
        """)
    #Runnable chain
    chain = prompt|llm
    #Run chain
    response = chain.invoke(text_split)
    return response.content


# function to get important topics
def get_important_topics(transcript):
    try:
        prompt = ChatPromptTemplate.from_template("""
               You are an assistant that extracts the 5 most important topics discussed in a video transcript or summary.

               Rules:
               - Summarize into exactly 5 major points.
               - Each point should represent a key topic or concept, not small details.
               - Keep wording concise and focused on the technical content.
               - Do not phrase them as questions or opinions.
               - Output should be a numbered list.
               - show only points that are discussed in the transcript.
               Here is the transcript:
               {transcript}
               """)

        # Runnable chain
        chain = prompt | llm

        # Run chain
        response = chain.invoke({"transcript": transcript})

        return response.content

    except Exception as e:
        st.error(f"Error fething video {e}")



# FUNCTION TO GET NOTES FROM THE VIDEO
def generate_notes(transcript):
    try:
        prompt = ChatPromptTemplate.from_template("""
                You are an AI note-taker. Your task is to read the following YouTube video transcript 
                and produce well-structured, concise notes.

                ⚡ Requirements:
                - Present the output as **bulleted points**, grouped into clear sections.
                - Highlight key takeaways, important facts, and examples.
                - Use **short, clear sentences** (no long paragraphs).
                - If the transcript includes multiple themes, organize them under **subheadings**.
                - Do not add information that is not present in the transcript.

                Here is the transcript:
                {transcript}
                """)

        # Runnable chain
        chain = prompt | llm

        # Run chain
        response = chain.invoke({"transcript": transcript})

        return response.content

    except Exception as e:
        st.error(f"Error fething video {e}")




# FUNCTION TO CREATE CHUNKS
def create_chunks(transcript):
    text_splitters= RecursiveCharacterTextSplitter(chunk_size=10000,chunk_overlap=1000)
    doc= text_splitters.split_text(transcript)
    return doc


# function to create embedding and store it into an vector space.
def create_vector_store(text):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size = 1000,
        chunk_overlap = 200
        )
    text_split = text_splitter.split_text(text)

    embedding= MistralAIEmbeddings(model="mistral-embed")

    vector_store = Chroma.from_texts(texts=text_split,embedding=embedding)
    return vector_store


#RAG FUNCTION
def rag_answer(question, vectorstore):
    results= vectorstore.similarity_search(question,k=4)
    context_text = "\n".join([i.page_content for i in results])

    prompt = ChatPromptTemplate.from_template("""
                You are a kind, polite, and precise assistant.
                - Begin with a warm and respectful greeting (avoid repeating greetings every turn).
                - Understand the user’s intent even with typos or grammatical mistakes.
                - Answer ONLY using the retrieved context.
                - If answer not in context, say:
                  "I couldn’t find that information in the database. Could you please rephrase or ask something else?"
                - Keep answers clear, concise, and friendly.

                Context:
                {context}

                User Question:
                {question}

                Answer:
                """)

    #chain
    chain = prompt|llm
    response= chain.invoke({"context":context_text,"question":question})

    return response.content




