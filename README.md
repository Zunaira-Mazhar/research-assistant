# 📚 AI Research Assistant

An AI-powered research assistant that helps users explore academic research using real and verifiable research papers.

## 🎯 Project Purpose

The purpose of this project is to make academic research easier and faster by helping users find relevant research papers, understand their key findings, identify contradictions and potential research gaps, and verify factual claims using real research evidence.

## ✨ Features

* 🔍 Search real research papers using the OpenAlex API
* 📝 Generate simple summaries of research findings
* ⚖️ Identify contradictions between papers
* 🧩 Identify potential research gaps
* 📄 Verify claims from uploaded PDF, DOCX, or TXT documents
* 📜 Save and view previous research searches

## 🛠️ Technologies

* Python
* Streamlit
* LangGraph
* LangChain Groq
* Groq
* OpenAlex API
* PyPDF
* python-docx

## ⚙️ Setup

1. Clone the repository.
2. Install the required packages:

```bash
pip install -r requirements.txt
```

3. Create a `.env` file and add your Groq API key:

```env
GROQ_API_KEY=your_api_key
```

4. Run the application:

```bash
streamlit run app.py
```

## 🔬 How It Works

The system uses multiple AI agents to search and analyze research papers. It can summarize findings, compare papers, identify potential research gaps, and verify factual claims from uploaded documents.

## 📌 Note

Research results are retrieved from OpenAlex, while AI is used for analysis and summarization. Users should review the original research papers before relying on the results.
