import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI
import json
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS

load_dotenv()
client = OpenAI()

st.set_page_config(
    page_title="German Uni Chatbot",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)


@st.cache_resource
def initialize_vector_store():
    """Loads JSON data, extracts text, and initializes the FAISS vector store."""
    docs = []
    
    # 1. Process univerities.json
    with open('universities.json', 'r', encoding='utf-8') as f:
        unis = json.load(f)
        for uni_id, data in unis.items():
            content = data.get('content', 'No description available.')
            location = data.get('University location', 'No location data.')
            text = f"University Name: {data.get('name')}\nCity: {data.get('city')}\nDetails: {content}\nLocation: {location}"
            docs.append(Document(page_content=text, metadata={"source": "universities", "id": uni_id}))
            
    degree_files = {
        "bachelor": "bachelor_clean.json",
        "master": "master_clean.json",
        "doctorate": "doctorate_clean.json"
    }

    for degree_level, filename in degree_files.items():
        with open(filename, 'r', encoding='utf-8') as f:
            courses = json.load(f)
            for course in courses:
                name = course.get('courseName', 'Unknown Course')
                academy = course.get('academy', 'Unknown University')
                tuition = course.get('tuitionFees', 'Unknown')
                    
                text = f"Degree Level: {degree_level.capitalize()}\nCourse: {name}\nUniversity: {academy}\nTuition: {tuition}"
                    
                docs.append(Document(
                    page_content=text, 
                    metadata={
                        "source": f"{degree_level}_courses", 
                        "course": name,
                        "level": degree_level  
                    }
                ))


    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    vector_store = FAISS.from_documents(docs, embeddings)
    
    return vector_store

def get_response(prompt):
    response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an expert advisor in enrollment for German universities and academic program. Give the user concise and accurate information based on the question. If you don't know the answer, say you don't know."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1
        )
    return response.choices[0].message.content.strip()

def main():
    if "messages" not in st.session_state:
        st.session_state.messages = []
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])
            
    with st.sidebar:
        st.title("German Uni Chatbot")
        if st.button("New chat"):
            st.session_state.messages = []
            st.rerun()
        st.divider()
        
    
    if prompt := st.chat_input("What is up?"):
        st.write("Welcome to the German University Chatbot!")
        st.session_state.messages.append(
            {"role": "user", "content": prompt}
        )

        with st.chat_message("user"):
            st.write(prompt)

        response = get_response(prompt)

        st.session_state.messages.append(
            {"role": "assistant", "content": response}
        )

        with st.chat_message("assistant"):
            st.write(response)
    
    
        
if __name__ == "__main__":
    main()
            
