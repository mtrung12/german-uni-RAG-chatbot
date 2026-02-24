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
    
    with open('data/universities.json', 'r', encoding='utf-8') as f:
        unis = json.load(f)
        for uni_id, data in unis.items():
            content = data.get('content', 'No description available.')
            location = data.get('University location', 'No location data.')
            text = f"University Name: {data.get('name')}\nCity: {data.get('city')}\nDetails: {content}\nLocation: {location}"
            docs.append(Document(page_content=text, metadata={"source": "universities", "id": uni_id}))
            
    degree_files = {
        "bachelor": "data/bachelor_clean.json",
        "master": "data/master_clean.json",
        "doctorate": "data/doctorate_clean.json"
    }

    for degree_level, filename in degree_files.items():
        with open(filename, 'r', encoding='utf-8') as f:
            courses = json.load(f)
            for course in courses:
                name = course.get('courseName', 'Unknown Course')
                university_id = course.get('university_id', 'Unknown University')
                academy = course.get('academy', 'Unknown University')
                tuition = course.get('tuitionFees', 'Unknown')
                beginning = course.get('beginning', 'Unknown')
                programmeDuration = course.get('programmeDuration', 'Unknown')
                application_deadline = course.get('applicationDeadline', 'Unknown')
                request_language = course.get('requestLanguage', 'Unknown')
                is_elearning = course.get('isElearning', 'Unknown')
                details = course.get('gallery_details', 'No details available.')
                
                    
                text = f"""Degree Level: {degree_level.capitalize()}\nCourse: {name}\nUniversity: {academy}\nTuition: {tuition}\nBeginning: {beginning}\nDuration: {programmeDuration}\nApplication Deadline: {application_deadline}\nRequest Language: {request_language}\nIs E-learning: {is_elearning}\nDetails: {details}"""
                    
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

def get_response(prompt, vector_store):
    retrieved_docs = vector_store.similarity_search(prompt, k=3)
    context = "\n\n".join([doc.page_content for doc in retrieved_docs])
    augmented_prompt = f"""
    Use the following context about German universities and courses to answer the user's question. 
    If the answer is not in the context, say you don't know based on the provided data.
    
    Context:
    {context}
    
    Question:
    {prompt}
    """
    
    system_prompt = """
    You are an expert advisor in enrollment for German universities and academic programs. 
    Use the following retrieved context to answer the user's question concisely and accurately. 
    If the answer cannot be found in the context, explicitly say that you do not have that information.
    """
    
    response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": augmented_prompt}
            ],
            temperature=0.1
        )
    return response.choices[0].message.content.strip()

def main():
    with st.spinner("Loading data and initializing vector store..."):
        vector_store = initialize_vector_store()
    
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
        st.session_state.messages.append(
            {"role": "user", "content": prompt}
        )

        with st.chat_message("user"):
            st.write(prompt)

        response = get_response(prompt, vector_store)

        st.session_state.messages.append(
            {"role": "assistant", "content": response}
        )

        with st.chat_message("assistant"):
            st.write(response)
    
    
        
if __name__ == "__main__":
    main()
            
