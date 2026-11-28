from retrieval.chunks import retrieve
from langchain_groq import ChatGroq
from dotenv import load_dotenv
import os
import json

load_dotenv()
llm = ChatGroq(model="openai/gpt-oss-20b", temperature=0)

STRUCTURED_DIR = "data/structured"

def load_incidents():
    """Load every structured postmortem, skipping pages that weren't real postmortems"""
    incidents = []
    for file in sorted(os.listdir(STRUCTURED_DIR)):
        with open(os.path.join(STRUCTURED_DIR, file), "r", encoding="utf-8") as f:
            record = json.load(f)

        if not record.get("symptoms") or not record.get("root_cause"):
            print(f"Skipping {file}: not a postmortem")
            continue

        record["id"] = file.replace(".json", "")
        incidents.append(record)

    print(f"Loaded {len(incidents)} incidents")
    return incidents

incidents = {record["id"]: record for record in load_incidents()}

def generate(query, top_k=3, score_threshold=0.42):
    """
    Retrieve similar incidents and summarize likely causes. Returns query, likely_causes, confidence, incidents."

    """
    #retrieve the context
    results = retrieve(query, top_k=top_k)
    confidence = max([doc['similarity_score'] for doc in results]) if results else 0.0
        
    if confidence < score_threshold or not results:
        return {"query": query, "likely_causes": "No match found", "confidence": confidence, "incidents": []}
    
    context = "\n\n".join(
    f"[{i}] Company: {incidents[inc['id']]['company']} | Category: {incidents[inc['id']]['category']} | Trigger: {incidents[inc['id']]['trigger']}\n"
        f"Root Cause: {incidents[inc['id']]['root_cause']}\n"
        f"Fix: {incidents[inc['id']]['fix']}\n"
        f"Prevention: {incidents[inc['id']]['prevention']}\n"
        for i, inc in enumerate(results, start=1)
    ) 

    incident_cards = [
        {
            "id": inc['id'],
            "company": incidents[inc['id']]['company'],
            "url": incidents[inc['id']]['url'],
            "category": incidents[inc['id']]['category'],
            "trigger": incidents[inc['id']]['trigger'],
            "root_cause": incidents[inc['id']]['root_cause'],
            "fix": incidents[inc['id']]["fix"],
            "prevention": incidents[inc['id']]["prevention"],
            "similarity": inc['similarity_score'],
            "matched_text": inc['content']
        }
        for inc in results
    ]
    
    #Generate a response using the LLM
    prompt = f"You are helping an on-call engineer. They described this symptom:\n{query}\nHere are similar past incidents from real postmortems:\n{context}\nWrite 1-3 likely causes for their issue, most likely first. Only include an incident if its situation genuinely resembles theirs. One strong cause is better than three weak ones.\nFor each one:\n- one sentence on the cause\n- what to check first to confirm it\n- cite the supporting incident like [1] or [2]\nOnly use the incidents above. If none of them really match, say so. Use a short bulleted list, not a table."
    response = llm.invoke(prompt)
    output = {"query": query,
              "likely_causes":response.content,
              "confidence": confidence,
              "incidents": incident_cards,
    }
    return output


if __name__ == "__main__":
    for q in ["cpu 100% on all edge servers after a firewall rule push", "my cake didn't rise in the oven"]:
        print(json.dumps(generate(q), indent=2, ensure_ascii=False))