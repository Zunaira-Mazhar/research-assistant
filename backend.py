import os
import time

import json
import requests
import io
from typing import TypedDict, List
from dotenv import load_dotenv
from pypdf import PdfReader
from docx import Document as DocxDocument

from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, END

# Load API key from .env file
load_dotenv()
os.environ["GROQ_API_KEY"] = os.getenv("GROQ_API_KEY")

# Setup LLM
llm = ChatGroq(model="openai/gpt-oss-120b", temperature=0)


#  STATE DEFINITION
class ResearchState(TypedDict):
    topic: str
    papers: List[dict]
    summaries: str
    contradictions: str
    research_gaps: str
    final_report: str


#  HELPER: REBUILD ABSTRACT TEXT
def reconstruct_abstract(inverted_index):
    """OpenAlex stores abstracts as an inverted index; this rebuilds the plain text."""
    if not inverted_index:
        return ""
    word_positions = []
    for word, positions in inverted_index.items():
        for pos in positions:
            word_positions.append((pos, word))
    word_positions.sort()
    return " ".join(word for pos, word in word_positions)


#  TOOL: FETCH REAL PAPERS FROM OPENALEX
def fetch_papers(query: str, limit: int = 6) -> List[dict]:
    """Fetches real, verifiable research papers from the OpenAlex API"""
    url = "https://api.openalex.org/works"
    params = {
        "search": query,
        "per-page": limit
    }

    try:
        response = requests.get(url, params=params, timeout=20)
        response.raise_for_status()

        data = response.json()
        results = data.get("results", [])

        papers = []
        for item in results:
            title = item.get("title") or "Untitled"
            year = item.get("publication_year", "Unknown")
            abstract = reconstruct_abstract(item.get("abstract_inverted_index"))
            link = item.get("id", "")

            if not abstract:
                abstract = "No abstract available for this paper."

            papers.append({
                "title": title,
                "abstract": abstract,
                "link": link,
                "year": year
            })

        return papers

    except (requests.exceptions.RequestException, ValueError):
        return []


#  NODE 1: SEARCH AGENT
def search_agent(state: ResearchState):
    papers = fetch_papers(state["topic"])
    return {"papers": papers}


#  NODE 2: SUMMARIZER AGENT
def summarizer_agent(state: ResearchState):
    papers = state["papers"]

    if not papers:
        return {"summaries": "No papers were found on this topic."}

    papers_text = ""
    for i, paper in enumerate(papers, start=1):
        papers_text += f"\nPaper {i}: {paper['title']} ({paper['year']})\nAbstract: {paper['abstract']}\n"

    prompt = f"""You are a research assistant. Below are real research papers with their abstracts.
Summarize the key finding of EACH paper in 1-2 sentences, in plain, simple language.
Only use information from the abstracts provided. Do not add information that is not in the abstracts.

{papers_text}

Format your response as a numbered list, one summary per paper."""

    result = llm.invoke(prompt).content
    return {"summaries": result}


#  NODE 3: CONTRADICTION AGENT
def contradiction_agent(state: ResearchState):
    papers = state["papers"]

    if not papers:
        return {"contradictions": "No papers to compare."}

    papers_text = ""
    for i, paper in enumerate(papers, start=1):
        papers_text += f"\nPaper {i}: {paper['title']}\nAbstract: {paper['abstract']}\n"

    prompt = f"""You are a research assistant. Below are real research papers.
Identify if any papers present conflicting or contradicting findings.
If you find contradictions, explain them clearly, mentioning which papers disagree.
If there are no clear contradictions, simply say "No major contradictions were found among these papers."
Only base your answer on the abstracts provided.

{papers_text}"""

    result = llm.invoke(prompt).content
    return {"contradictions": result}


#  NODE 4: RESEARCH GAP AGENT
def gap_agent(state: ResearchState):
    papers = state["papers"]

    if not papers:
        return {"research_gaps": "No papers to analyze for gaps."}

    papers_text = ""
    for i, paper in enumerate(papers, start=1):
        papers_text += f"\nPaper {i}: {paper['title']}\nAbstract: {paper['abstract']}\n"

    prompt = f"""You are a research assistant. Based on the abstracts below, identify 2-3 potential
research gaps — areas that these papers do not cover well, or questions that remain unanswered
about the topic "{state['topic']}".
Only base your answer on what is present or missing in these abstracts.

{papers_text}"""

    result = llm.invoke(prompt).content
    return {"research_gaps": result}


#  NODE 5: FINAL REPORT AGENT
def report_agent(state: ResearchState):
    papers = state["papers"]

    citations = ""
    for i, paper in enumerate(papers, start=1):
        citations += f"{i}. {paper['title']} ({paper['year']}) - {paper['link']}\n"

    report = f"""RESEARCH SUMMARY: {state['topic']}

KEY FINDINGS:
{state['summaries']}

CONTRADICTIONS BETWEEN PAPERS:
{state['contradictions']}

RESEARCH GAPS:
{state['research_gaps']}

REFERENCES (Real, Verifiable Papers):
{citations}"""

    return {"final_report": report}


#  BUILD THE GRAPH
workflow = StateGraph(ResearchState)

workflow.add_node("search", search_agent)
workflow.add_node("summarize", summarizer_agent)
workflow.add_node("contradictions", contradiction_agent)
workflow.add_node("gaps", gap_agent)
workflow.add_node("report", report_agent)

workflow.set_entry_point("search")

workflow.add_edge("search", "summarize")
workflow.add_edge("summarize", "contradictions")
workflow.add_edge("contradictions", "gaps")
workflow.add_edge("gaps", "report")
workflow.add_edge("report", END)

app = workflow.compile()


#  FUNCTION FOR FRONTEND TO CALL
def generate_research_report(topic: str) -> str:
    result = app.invoke({
        "topic": topic,
        "papers": [],
        "summaries": "",
        "contradictions": "",
        "research_gaps": "",
        "final_report": ""
    })
    return result["final_report"]
# =============================
# DOCUMENT VERIFICATION FEATURE
# ============================

class VerificationState(TypedDict):
    document_text: str
    claims: List[str]
    verification_results: str


#  NODE: EXTRACT CLAIMS FROM DOCUMENT
def extract_claims_agent(state: VerificationState):
    prompt = f"""You are a research verification assistant. Read the document below and extract
3-5 key factual claims or statements that could be checked against scientific research.
Only extract clear, checkable claims — not opinions or vague statements.

Document:
{state['document_text']}

Format your response as a numbered list of claims, nothing else."""

    result = llm.invoke(prompt).content

    # Parse the numbered list into a Python list
    claims = []
    for line in result.split("\n"):
        line = line.strip()
        if line and (line[0].isdigit()):
            # Remove the number and punctuation at the start, e.g. "1. " or "1)"
            cleaned = line.lstrip("0123456789.) ").strip()
            if cleaned:
                claims.append(cleaned)

    return {"claims": claims}




def chunk_text(text: str, chunk_size: int = 3000) -> List[str]:
    """Splits long text into smaller chunks so each stays within the model's token limits"""
    chunks = []
    for i in range(0, len(text), chunk_size):
        chunks.append(text[i:i + chunk_size])
    return chunks


def extract_claims_agent(state: VerificationState):
    document_text = state["document_text"]
    chunks = chunk_text(document_text, chunk_size=3000)

    all_claims = []

    for chunk in chunks:
        prompt = f"""You are a research verification assistant. Read the document excerpt below and extract
UP TO 3 key factual claims or statements that could be checked against scientific research.
Only extract clear, checkable claims — not opinions or vague statements.
If there are no checkable claims in this excerpt, respond with "NONE".

Document excerpt:
{chunk}

Format your response as a numbered list of claims, nothing else."""

        result = llm.invoke(prompt).content

        if "NONE" not in result.upper() or len(result.strip()) > 10:
            for line in result.split("\n"):
                line = line.strip()
                if line and line[0].isdigit():
                    cleaned = line.lstrip("0123456789.) ").strip()
                    if cleaned and cleaned.upper() != "NONE":
                        all_claims.append(cleaned)

        # Small pause between calls to stay within the per-minute token limit
        time.sleep(2)

    return {"claims": all_claims}


#  NODE: VERIFY EACH CLAIM AGAINST REAL PAPERS
def verify_claims_agent(state: VerificationState):
    claims = state["claims"]

    if not claims:
        return {"verification_results": "No checkable claims were found in this document."}

    all_results = ""

    for claim in claims:
        papers = fetch_papers(claim, limit=3)

        if not papers:
            all_results += f"\n\nCLAIM: {claim}\nSTATUS: No supporting research found.\n"
            continue

        papers_text = ""
        for i, paper in enumerate(papers, start=1):
            papers_text += f"\nPaper {i}: {paper['title']} ({paper['year']})\nAbstract: {paper['abstract']}\n"

        prompt = f"""You are a fact-checking assistant. Below is a claim, followed by real research papers.
Determine if the claim is SUPPORTED, PARTIALLY SUPPORTED, or NOT SUPPORTED by these papers.
Explain your reasoning in 1-2 sentences, referring to the papers.

Claim: {claim}

Papers:
{papers_text}

Respond in this format:
VERDICT: [Supported / Partially Supported / Not Supported]
REASONING: [your explanation]"""

        result = llm.invoke(prompt).content

        citations = ""
        for i, paper in enumerate(papers, start=1):
            citations += f"  - {paper['title']} ({paper['year']})\n"

        all_results += f"\n\nCLAIM: {claim}\n{result}\n\nSUPPORTING PAPERS FOUND:\n{citations}"

    return {"verification_results": all_results}


#  BUILD THE VERIFICATION GRAPH
verify_workflow = StateGraph(VerificationState)

verify_workflow.add_node("extract_claims", extract_claims_agent)
verify_workflow.add_node("verify_claims", verify_claims_agent)

verify_workflow.set_entry_point("extract_claims")
verify_workflow.add_edge("extract_claims", "verify_claims")
verify_workflow.add_edge("verify_claims", END)

verify_app = verify_workflow.compile()


#  FUNCTION FOR FRONTEND TO CALL
def verify_document(document_text: str) -> str:
    result = verify_app.invoke({
        "document_text": document_text,
        "claims": [],
        "verification_results": ""
    })
    return result["verification_results"]




HISTORY_FILE = "search_history.json"


def load_history():
    """Loads saved search history from a file"""
    if not os.path.exists(HISTORY_FILE):
        return []
    with open(HISTORY_FILE, "r") as f:
        return json.load(f)


def save_history(history):
    """Saves search history to a file"""
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f)


def add_to_history(topic, report):
    """Adds a new search to the history and saves it"""
    history = load_history()
    history.append({"topic": topic, "report": report})
    save_history(history)


# FILE READING

def read_uploaded_file(uploaded_file) -> str:
    """Reads text from PDF, DOCX, or TXT files"""
    filename = uploaded_file.name.lower()

    if filename.endswith(".pdf"):
        reader = PdfReader(uploaded_file)
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""
        return text

    elif filename.endswith(".docx"):
        doc = DocxDocument(uploaded_file)
        return "\n".join(para.text for para in doc.paragraphs)

    elif filename.endswith(".txt"):
        return uploaded_file.read().decode("utf-8")

    return ""

#-----------------------------------------------------------
# DOCUMENT VERIFICATION FEATURE (Structured Output Version)
#-----------------------------------------------------------

class VerificationState(TypedDict):
    document_text: str
    claims: List[str]
    verification_results: List[dict]


def extract_claims_agent(state: VerificationState):
    # Limit document length to avoid exceeding the model's token rate limit
    document_text = state["document_text"][:4000]

    prompt = f"""You are a research verification assistant. Read the document below and extract
3-5 key factual claims or statements that could be checked against scientific research.
Only extract clear, checkable claims — not opinions or vague statements.

Document:
{document_text}

Format your response as a numbered list of claims, nothing else."""

    result = llm.invoke(prompt).content

    claims = []
    for line in result.split("\n"):
        line = line.strip()
        if line and line[0].isdigit():
            cleaned = line.lstrip("0123456789.) ").strip()
            if cleaned:
                claims.append(cleaned)

    return {"claims": claims}


def verify_claims_agent(state: VerificationState):
    claims = state["claims"]
    results = []

    for claim in claims:
        papers = fetch_papers(claim, limit=3)

        if not papers:
            results.append({
                "claim": claim,
                "verdict": "No Data",
                "reasoning": "No supporting research papers were found for this claim.",
                "papers": []
            })
            continue

        papers_text = ""
        for i, paper in enumerate(papers, start=1):
            papers_text += f"\nPaper {i}: {paper['title']} ({paper['year']})\nAbstract: {paper['abstract']}\n"

        prompt = f"""You are a fact-checking assistant. Below is a claim, followed by real research papers.
Determine if the claim is SUPPORTED, PARTIALLY SUPPORTED, or NOT SUPPORTED by these papers.
Explain your reasoning in 1-2 sentences, referring to the papers.

Claim: {claim}

Papers:
{papers_text}

Respond in this exact format:
VERDICT: [Supported / Partially Supported / Not Supported]
REASONING: [your explanation]"""

        result = llm.invoke(prompt).content

        verdict = "Unknown"
        reasoning = result
        for line in result.split("\n"):
            if line.strip().upper().startswith("VERDICT:"):
                verdict = line.split(":", 1)[1].strip()
            if line.strip().upper().startswith("REASONING:"):
                reasoning = line.split(":", 1)[1].strip()

        results.append({
            "claim": claim,
            "verdict": verdict,
            "reasoning": reasoning,
            "papers": papers
        })

    return {"verification_results": results}


verify_workflow = StateGraph(VerificationState)
verify_workflow.add_node("extract_claims", extract_claims_agent)
verify_workflow.add_node("verify_claims", verify_claims_agent)
verify_workflow.set_entry_point("extract_claims")
verify_workflow.add_edge("extract_claims", "verify_claims")
verify_workflow.add_edge("verify_claims", END)

verify_app = verify_workflow.compile()


def verify_document(document_text: str) -> List[dict]:
    result = verify_app.invoke({
        "document_text": document_text,
        "claims": [],
        "verification_results": []
    })
    return result["verification_results"]


# ============================
# HISTORY (persistent storage)
# ===========================

HISTORY_FILE = "search_history.json"


def load_history():
    if not os.path.exists(HISTORY_FILE):
        return []
    with open(HISTORY_FILE, "r") as f:
        return json.load(f)


def save_history(history):
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f)


def add_to_history(topic, report):
    history = load_history()
    history.append({"topic": topic, "report": report})
    save_history(history)
