import json
import re
import os
from dotenv import load_dotenv
from openai import OpenAI
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS

# Load the environment variables from the parent directory
load_dotenv('../.env')

# Initialize the OpenAI client 
client = OpenAI()

INPUT_FILES = ['bachelor.json', 'master.json', 'doctorate.json']
OUTPUT_UNIS_FILE = 'universities.json'

UNI_LEVEL_KEYS = [
    "content",
    "University location"
]

def create_and_save_vector_store():
    print("Building vector store and generating embeddings...")
    docs = []
    
    # Load Universities
    with open('universities.json', 'r', encoding='utf-8') as f:
        unis = json.load(f)
        for uni_id, data in unis.items():
            content = data.get('content', 'No description available.')
            location = data.get('University location', 'No location data.')
            text = f"University Name: {data.get('name')}\nCity: {data.get('city')}\nDetails: {content}\nLocation: {location}"
            docs.append(Document(page_content=text, metadata={"source": "universities", "id": uni_id}))
            
    # Load Courses
    degree_files = {
        "bachelor": "bachelor_clean.json",
        "master": "master_clean.json",
        "doctorate": "doctorate_clean.json"
    }

    for degree_level, filename in degree_files.items():
        if not os.path.exists(filename):
            continue
            
        with open(filename, 'r', encoding='utf-8') as f:
            courses = json.load(f)
            for course in courses:
                name = course.get('courseName', 'Unknown Course')
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

    # Generate Embeddings and Save Locally
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    vector_store = FAISS.from_documents(docs, embeddings)
    
    # This creates a folder called 'faiss_index' containing your database
    vector_store.save_local("faiss_index")
    print("Vector store successfully saved to the 'faiss_index' folder!")


if __name__ == "__main__":
    create_and_save_vector_store()