import requests
import json
import os
import time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from bs4 import BeautifulSoup, NavigableString

BASE_SEARCH_URL = "https://www2.daad.de/deutschland/studienangebote/international-programmes/api/solr/en/search.json"
BASE_DETAIL_URL = "https://www2.daad.de/deutschland/studienangebote/international-programmes/en/detail/"
DEGREE_MAP = {
    "bachelor": "1",
    "master": "2",
    "doctorate": "3"
}
LIMIT = 100
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Accept": "application/json",
    "Referer": "https://www2.daad.de/deutschland/studienangebote/international-programmes/en/"
}
ENGLISH_ONLY = True  # Set to False for all languages
FETCH_DETAILS = True  # Set to False to skip details and only get basics
DETAIL_SLEEP = 1  # Seconds between detail requests to avoid rate limiting

def fetch_programs(degree_type: str, degree_code: str):
    programs = []
    offset = 0
    total = None
    
    session = requests.Session()
    retry = Retry(total=3, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    
    while True:
        params = {
            "limit": LIMIT,
            "offset": offset,
            "degree[]": degree_code,
            "sort": "name"
        }
        if ENGLISH_ONLY:
            params["lang[]"] = "2"
        
        try:
            response = session.get(BASE_SEARCH_URL, params=params, headers=HEADERS, timeout=10)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching {degree_type}: {e}")
            break
        
        try:
            data = response.json()
        except json.JSONDecodeError:
            print(f"Invalid JSON for {degree_type}")
            break
        
        if total is None:
            total = data.get("numResults", 0)
            print(f"{degree_type.capitalize()}: Total programs = {total}")
        
        courses = data.get("courses", [])
        programs.extend(courses)
        
        if len(courses) < LIMIT:
            break
        
        offset += LIMIT
        time.sleep(1)  # Rate limit for search
    
    return programs

def fetch_program_details(prog_id: str):
    url = f"{BASE_DETAIL_URL}{prog_id}/"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching details for ID {prog_id}: {e}")
        return {}
    
    soup = BeautifulSoup(response.text, "html.parser")
    
    details = {}
    current_section = None
    current_subsection = None
    
    # Find main content area (adjust selector if needed; e.g., div with class 'c-description')
    content_area = soup.find("div", class_="js-course-detail__main") or soup  # Fallback to whole soup
    
    for element in content_area.find_all(["h2", "h3", "p", "ul", "ol", "strong"]):
        if element.name == "h2":
            current_section = element.text.strip()
            details[current_section] = {}
            current_subsection = None
        elif element.name == "h3":
            if current_section:
                current_subsection = element.text.strip()
                details[current_section][current_subsection] = []
        elif element.name in ["p", "ul", "ol"]:
            text = element.text.strip()
            if text:
                if current_subsection:
                    details[current_section][current_subsection].append(text)
                elif current_section:
                    if isinstance(details[current_section], dict):
                        if "content" not in details[current_section]:
                            details[current_section]["content"] = []
                        details[current_section]["content"].append(text)
                    else:
                        details[current_section] = {"content": [text]}
        elif element.name == "strong":
            text = element.text.strip()
            if text and current_section:
                # Handle bold keys like in fees
                next_text = ""
                if element.next_sibling:
                    if isinstance(element.next_sibling, NavigableString):
                        next_text = element.next_sibling.strip()
                    elif hasattr(element.next_sibling, 'text'):
                        next_text = element.next_sibling.text.strip()
                
                if current_subsection:
                    details[current_section][current_subsection].append(f"{text}: {next_text}")
                else:
                    if "content" not in details[current_section]:
                        details[current_section]["content"] = []
                    details[current_section]["content"].append(f"{text}: {next_text}")
    
    # Clean up: Join lists into strings for simplicity
    for section in details:
        if isinstance(details[section], dict):
            for sub in details[section]:
                if isinstance(details[section][sub], list):
                    details[section][sub] = "\n".join(details[section][sub])
    
    return details

def save_programs(degree_type: str, programs):
    folder = f"../data"
    os.makedirs(folder, exist_ok=True)
    
    enhanced_programs = []
    for prog in programs:
        enhanced_prog = prog.copy()
        prog_id = prog.get("id")
        if FETCH_DETAILS and prog_id:
            details = fetch_program_details(prog_id)
            enhanced_prog["details"] = details
            time.sleep(DETAIL_SLEEP)  # Rate limit for details
        enhanced_programs.append(enhanced_prog)
    
    combined_path = os.path.join(folder, f"{degree_type}.json")
    with open(combined_path, "w", encoding="utf-8") as f:
        json.dump(enhanced_programs, f, ensure_ascii=False, indent=4)
    print(f"Saved {len(enhanced_programs)} programs (with details) to {combined_path}")

if __name__ == "__main__":
    for degree_type, degree_code in DEGREE_MAP.items():
        programs = fetch_programs(degree_type, degree_code)
        save_programs(degree_type, programs)