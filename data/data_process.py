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

def generate_uni_id(academy_name):
    if not academy_name:
        return "unknown_university"
    clean_name = re.sub(r'[^a-zA-Z0-9]', '_', academy_name)
    return re.sub(r'_+', '_', clean_name).strip('_').lower()

def parse_gallery(gallery_text):
    if not gallery_text:
        return {}

    # Split headers from content
    parts = gallery_text.split('\n\n\n\n', 1) 
    if len(parts) < 2:
        return {"Raw_Content": gallery_text} 
        
    headers_block = parts[0]
    content_block = parts[1]
    
    # Clean up the headers
    headers_list = [h.strip() for h in headers_block.split('\n\n\n') if h.strip()]
    
    # Construct the prompt for the LLM
    prompt = f"""
    Map the relevant parts of the text block to the corresponding headers.
    
    Headers: {headers_list}
    
    Text Block:
    {content_block}
    
    Return a valid JSON object where the keys are exactly the headers provided, and the values are the corresponding extracted text. Do not include any extra commentary.
    """
    
    try:
        # Call gpt-4o-mini enforcing JSON output
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a data extraction assistant designed to output JSON."},
                {"role": "user", "content": prompt}
            ],
            response_format={ "type": "json_object" }, # Forces the model to return valid JSON
            temperature=0.1 # Low temperature for more deterministic/factual extraction
        )
        
        # Parse and return the JSON string returned by the model
        result_string = response.choices[0].message.content
        return json.loads(result_string)
        
    except Exception as e:
        print(f"Error parsing gallery with GPT: {e}")
        
        # Fallback to your original code-based segmentation if the API call fails
        raw_lines = content_block.split('\n')
        return {
            "Raw_Text": content_block
        }

def process_data():
    universities = {}
    
    for file_name in INPUT_FILES:
        if not os.path.exists(file_name):
            print(f"File {file_name} not found. Skipping.")
            continue
            
        with open(file_name, 'r', encoding='utf-8') as f:
            courses = json.load(f)

        processed_courses = []
        
        for course in courses:
            academy = course.get('academy')
            uni_id = generate_uni_id(academy)
            details = course.get('details', {})
            course_name = course.get('courseName')
            # Build the University Record
            if uni_id not in universities:
                universities[uni_id] = {
                    "id": uni_id,
                    "name": academy,
                    "city": course.get('city')
                }
                # Grab the university-level info from the details object
                for key in UNI_LEVEL_KEYS:
                    if key in details[academy]:
                        universities[uni_id][key] = details[academy][key]
            
            # Extract and Parse the Gallery
            key = f"{course_name}\n{course_name}"
            course_block = details.get(key, {})   # empty dict if key is missing

            gallery_raw = course_block.get("Gallery", "")
            course["gallery_details"] = parse_gallery(gallery_raw)
            
            # Clean up the Course Record (Remove Duplicates)
            course['university_id'] = uni_id  # Add foreign key
            
            # Remove the duplicated university-level keys from the course's details
            for key in UNI_LEVEL_KEYS:
                course['details'].pop(key, None)
                
            # Remove the raw unparsed Gallery string to save space
            course['details'].pop('Gallery', None)
            
            # If details is now empty after removing the duplicates, you can remove it entirely
            if not course['details']:
                course.pop('details', None)
                
            processed_courses.append(course)
            
        # 4. Save the processed courses back to their respective files
        output_file = file_name.replace('.json', '_clean.json')
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(processed_courses, f, indent=4, ensure_ascii=False)
        print(f"Saved {len(processed_courses)} cleaned courses to {output_file}")

    # 5. Save the central Universities file
    with open(OUTPUT_UNIS_FILE, 'w', encoding='utf-8') as f:
        json.dump(universities, f, indent=4, ensure_ascii=False)
    print(f"Saved {len(universities)} unique universities to {OUTPUT_UNIS_FILE}")

if __name__ == "__main__":
    process_data()