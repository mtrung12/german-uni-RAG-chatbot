# German Universities Admission Information Chatbot

A **Retrieval-Augmented Generation (RAG)–based chatbot** designed to answer questions related to **admission information for German universities**, with a focus on **international students**.

The chatbot supports admission inquiries across all academic levels:
- Undergraduate (Bachelor)
- Graduate (Master)
- Doctoral (PhD)

All information is collected from **DAAD (German Academic Exchange Service)** and processed into a searchable knowledge base to improve accuracy and relevance.

---

## Live Demo

You can access the deployed application directly at:

https://germanuni.streamlit.app/

No local setup is required to try the chatbot via the web interface.

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

## Setup Instructions (Local Deployment)

Follow the steps below if you want to build and run the chatbot locally.

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

### Step 4: Configure Environment Variables

Create a `.env` file in the **project root directory** with the following content:

```env
OPENAI_API_KEY=""
GROQ_API_KEY=""
```

Make sure to replace the empty strings with your actual API keys.

---

### Step 5: Run the Chatbot Application

Return to the project root and start the Streamlit application:

```bash
cd ..
streamlit run app.py
```

After launching, the chatbot will be available in your browser.

---

## Requirements

- Python 3.10
- Streamlit
- FAISS
- Other dependencies listed in `requirements.txt`

Install dependencies with:

```bash
pip install -r requirements.txt
```

---

## Notes

- Ensure that web scraping complies with DAAD’s terms of service.
- Response quality depends on the completeness and freshness of the scraped data.
- The hosted version and the local version use the same RAG pipeline.
- This project is intended for educational and research purposes.

---

## License

This project is provided for academic and non-commercial use.