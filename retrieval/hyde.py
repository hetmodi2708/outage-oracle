from typing import List, Dict, Any
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from retrieval.baseline import retriever as baseline_retriever

load_dotenv()

llm = ChatGroq(model="openai/gpt-oss-20b", temperature=0)

HYDE_PROMPT = """You are an experienced site reliability engineer.
An on-call engineer typed this into an incident search engine:

"{query}"

Write the "symptoms" section of a postmortem for an incident that matches this.
3-4 sentences describing what users and engineers OBSERVED: errors, failing requests,
metrics, alerts, and knock-on effects on other systems.
Write it generically: no company names, product names, dates, or the root cause.
Return only the symptoms text."""


### Step 1: Generate a hypothetical document from the query

def generate_hypothetical(query: str) -> str:
    """Ask the LLM to write the symptoms an incident like this would have"""
    try:
        response = llm.invoke(HYDE_PROMPT.format(query=query))
        return response.content.strip()
    except Exception as e:
        print(f"HyDE generation failed, falling back to the raw query: {e}")
        return query


### Step 2: Search with the hypothetical document instead of the raw query

def retrieve(query: str, top_k: int = 5, verbose: bool = False) -> List[Dict[str, Any]]:
    """HyDE retrieval: query -> LLM-written hypothetical symptoms -> embed -> search"""
    hypothetical = generate_hypothetical(query)
    if verbose:
        print(f"Query:        {query}\nHypothetical: {hypothetical}\n")
    return baseline_retriever.retrieve(hypothetical, top_k=top_k)


def query_retrieve(query: str, k: int = 5) -> List[str]:
    """Simple helper for evals: return just the top-k incident ids"""
    return [doc["id"] for doc in retrieve(query, top_k=k)]
