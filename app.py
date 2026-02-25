import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI
import json
from datetime import datetime
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
import os
import glob

load_dotenv()
client = OpenAI()


groq_client = OpenAI(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1"
)

st.set_page_config(
    page_title="German Uni Chatbot",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)


@st.cache_resource
def initialize_vector_store():
    # We still need the embedding model so FAISS can embed the user's chat input
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    if not os.path.exists("data/faiss_index"):
        st.warning("Vector store not found. Please run data/create_vector.py to create it.")
        return None
    # Load the pre-computed database from the folder we created
    vector_store = FAISS.load_local(
        folder_path="data/faiss_index", 
        embeddings=embeddings, 
        allow_dangerous_deserialization=True 
    )
    
    return vector_store

def generate_chat_title(messages):
    context = "\n".join([f"{m['role']}: {m['content']}" for m in messages[:3]])
    
    response = groq_client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": "You generate very short, 3 to 5 word titles for conversations. Reply with ONLY the title. No quotes, no punctuation, no extra text."},
            {"role": "user", "content": f"Create a title for this conversation:\n\n{context}"}
        ],
        temperature=0.3, 
        max_tokens=15    
    )
    return response.choices[0].message.content.strip()

def save_chat_history():
    if "messages" in st.session_state:
        os.makedirs('chat_history', exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"chat_history/chat_{timestamp}.json"
        summary = generate_chat_title(st.session_state.messages)
        chat_data = {
            "summary_name": summary,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "messages": st.session_state.messages
        }
        
        # 3. Save it
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(chat_data, f, indent=4, ensure_ascii=False)
        
def load_chat_history(file):
    with open(file, 'r', encoding='utf-8') as f:
        chat_data = json.load(f)
        st.session_state.messages = chat_data.get("messages", [])
        
def display_chat_history():
    if not os.path.exists('chat_history'):
        st.info("No chat history found.")
        return
    files = glob.glob('chat_history/*.json')
    files.sort(key=os.path.getmtime, reverse=True)
    for file in files:
        with open(file, 'r', encoding='utf-8') as f:
            chat_data = json.load(f)
            summary = chat_data.get("summary_name", "No Summary")
            if st.button(f"**{summary}**", key=file):
                load_chat_history(file)
                st.session_state.is_new_chat = False
                st.rerun()
    

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
    if "is_new_chat" not in st.session_state:
        st.session_state.is_new_chat = True
    
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])
            
    with st.sidebar:
        st.title("German Uni Chatbot")
        if st.button("New chat"):
            if len(st.session_state.messages) > 0 and st.session_state.is_new_chat:
                save_chat_history()
            st.session_state.messages = []
            st.session_state.is_new_chat = True
            st.rerun()
        st.divider()
        display_chat_history()
        
    
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
            
