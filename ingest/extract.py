import json
import os
from dotenv import load_dotenv
import time

from langchain_groq import ChatGroq

load_dotenv()

llm = ChatGroq(model="openai/gpt-oss-20b", temperature=0,
               model_kwargs={"response_format": {"type": "json_object"}})


os.makedirs("data/structured", exist_ok=True)

for file in os.listdir("data/raw"):
    out_path = os.path.join("data/structured", file)

    #Already extracted on a previous run -> skip it (lets you resume after a crash)
    if os.path.exists(out_path):
        continue

    with open(os.path.join("data/raw", file), "r", encoding="utf-8") as f:
        record = json.load(f)
    text = record["text"][:15000]
    
    
    prompt = f"""You are extracting structured data from an incident postmortem.
        Return ONLY a JSON object with exactly these keys and types:

        {{
        "symptoms": "string, 2-4 sentences. What an on-call engineer would SEE during the incident: errors, failing requests, metrics, user complaints. Write it generically, as if typing into a search box. Do NOT include the company name, product names, locations, dates/times, or the root cause.",
        "root_cause": "string. Why it happened.",
        "fix": "string. What was done DURING the incident to restore service.",
        "prevention": "string. Follow-up changes made AFTER, to stop it happening again.",
        "category": "which system failed — one of: database, network, dns, compute, storage, auth-cert, application, other",
        "trigger":  "what started it — one of: config-change, deploy, hardware, traffic-spike, dependency-failure, human-error, bug, unknown",
        "severity": "one of: low, medium, high",
        "duration_minutes": "integer, or null if not stated"
        }}

        Postmortem:
        {text}"""

    print(f"Extracting: {file}")
    data = None                                  #reset every loop, so stale data can never leak
    for attempt in range(3):                     #try up to 3 times
        try:
            response = llm.invoke(prompt)
            data = json.loads(response.content)
            break                                #success -> stop retrying
        except Exception as e:
            if "rate_limit" in str(e).lower():
                print("   Rate limited, waiting 60s...")
                time.sleep(60)
            else:
                print(f"   Failed: {e}")
                break                            #a non-rate-limit error won't fix itself on retry

    if data is None:
        print("   Skipping this file")
        continue                                 #never save without fresh data

    if isinstance(data.get("symptoms"), list):
        data["symptoms"] = " ".join(data["symptoms"])

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({**record, **data}, f, ensure_ascii=False, indent=2)

    time.sleep(2)

