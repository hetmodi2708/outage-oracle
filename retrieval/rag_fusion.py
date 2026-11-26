import re
from typing import List, Dict, Any
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from retrieval.baseline import retriever as baseline_retriever

load_dotenv()


llm = ChatGroq(model="openai/gpt-oss-20b", temperature=0)

NUM_REWRITES = 4
PER_QUERY_K = 10     
RRF_K = 60           

RAG_FUSION_PROMPT = """You are an experienced site reliability engineer.
An on-call engineer typed this into an incident search engine:

"{query}"

Write {n} different search queries describing the same incident symptoms in different words.
Vary the vocabulary (e.g. "latency" vs "slow responses", "OOM" vs "out of memory"), and keep
the important specific details from the original.
No company names, product names, dates, or guesses at the root cause.
Return one query per line, with no numbering or extra text."""


### Step 1: Generate rewrites of the query

def generate_queries(query: str, n: int = NUM_REWRITES) -> List[str]:
    """Ask the LLM for n rephrasings of the query. Always keeps the original query first."""
    try:
        response = llm.invoke(RAG_FUSION_PROMPT.format(query=query, n=n))
        lines = response.content.strip().split("\n")
    except Exception as e:
        print(f"Query generation failed, using only the original query: {e}")
        lines = []

    rewrites = []
    for line in lines:
    
        line = re.sub(r"^\s*(\d+[.)]|[-*•])\s*", "", line).strip().strip('"')
        if line:
            rewrites.append(line)

    
    return [query] + rewrites[:n]


### Step 2: Reciprocal Rank Fusion

def reciprocal_rank_fusion(result_lists: List[List[Dict[str, Any]]], k: int = RRF_K) -> List[Dict[str, Any]]:
    """Merge several ranked lists into one.

    Each incident scores 1 / (k + rank) in every list it appears in, and the scores are added up.
    An incident that ranks well in many lists beats one that ranks #1 in just a single list.
    """
    fused_scores = {}
    docs_by_id = {}

    for docs in result_lists:
        for rank, doc in enumerate(docs, start=1):
            doc_id = doc["id"]                      
            fused_scores[doc_id] = fused_scores.get(doc_id, 0) + 1 / (k + rank)
            docs_by_id[doc_id] = doc

    reranked = []
    for new_rank, (doc_id, score) in enumerate(sorted(fused_scores.items(), key=lambda x: x[1], reverse=True), start=1):
        reranked.append({**docs_by_id[doc_id], "rrf_score": score, "rank": new_rank})
    return reranked


### Step 3: Search with every query, then fuse

def retrieve(query: str, top_k: int = 5, verbose: bool = False) -> List[Dict[str, Any]]:
    """RAG Fusion: query -> original + rewrites -> search each -> merge with RRF -> top_k"""
    queries = generate_queries(query)
    if verbose:
        print("Queries:\n  " + "\n  ".join(queries))

    result_lists = [baseline_retriever.retrieve(q, top_k=PER_QUERY_K) for q in queries]
    return reciprocal_rank_fusion(result_lists)[:top_k]


def query_retrieve(query: str, k: int = 5) -> List[str]:
    """Simple helper for evals: return just the top-k incident ids"""
    return [doc["id"] for doc in retrieve(query, top_k=k)]
