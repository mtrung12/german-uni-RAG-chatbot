# German Universities Admission Information Chatbot

A **Retrieval-Augmented Generation (RAG)–based chatbot** designed to answer questions related to **admission information for German universities**, with a focus on **international students**.

The chatbot supports admission inquiries across all academic levels:
- Undergraduate (Bachelor)
- Graduate (Master)
- Doctoral (PhD)

All information is collected from **DAAD (German Academic Exchange Service)** and processed into a searchable knowledge base to improve accuracy and relevance.

---

## Features

- Domain-specific chatbot for German university admissions  
- Supports Bachelor, Master, and PhD programs  
- Retrieval-Augmented Generation (RAG) using FAISS  
- Data scraped from DAAD (international student enrollment information)  
- Interactive web interface built with Streamlit  

---

## Project Structure

```text
.
├── info_scrape/          # Web scraping scripts
│   └── scrape.py
├── data/                 # Data processing and vector creation
│   ├── data_process.py
│   └── create_vector.py
├── app.py                # Streamlit chatbot application
└── README.md
```

---

## Setup Instructions

Follow the steps below to run the project locally.

### Step 1: Scrape Admission Data

Navigate to the scraping directory and collect admission data from `daad.de`:

```bash
cd info_scrape
python scrape.py
```

---

### Step 2: Process the Scraped Data

Clean and prepare the raw data for embedding:

```bash
cd ../data
python data_process.py
```

---

### Step 3: Create the Vector Store

Generate the FAISS vector store used by the RAG pipeline:

```bash
python create_vector.py
```

---

### Step 4: Run the Chatbot Application

Return to the project root and start the Streamlit application:

```bash
cd ..
streamlit run app.py
```

The chatbot will be available in your browser after launching.

---

## Requirements

- Python 3.9 or higher
- Streamlit
- FAISS
- Other dependencies listed in `requirements.txt`

Install dependencies with:

```bash
pip install -r requirements.txt
```

---

## Notes

- Please ensure that web scraping complies with DAAD’s terms of service.
- Response quality depends on the completeness and freshness of the scraped data.
- This project is intended for educational and research purposes.

---

## License

This project is provided for academic and non-commercial use.