import os
import sys
import json
import importlib
from collections import defaultdict

EVAL_SET = "evals/eval_set.json"
RESULTS_DIR = "evals/results"
K = 5


### Step 1: Load the eval set

def load_eval_set(path=EVAL_SET):
    """Load the hand-written queries and the incident each one should find"""
    with open(path, "r", encoding="utf-8") as f:
        items = json.load(f)
    items = [item for item in items if item["query"].strip()]   #ignore any unfinished entries
    print(f"Loaded {len(items)} eval queries")
    return items


### Step 2: Run every query and score it

def run_evals(retrieve, items, k=K):
    """Run each query through the retriever and measure recall@k and MRR

    Args:
        retrieve: function(query, k) -> list of incident ids, best first
        items: eval set entries with 'query' and 'expected_id'

    Returns:
        Dict with overall scores and per-query results
    """
    per_query = []
    hits = 0
    reciprocal_ranks = []

    for item in items:
        ids = retrieve(item["query"], k)
        expected = item["expected_id"]

        hit = expected in ids
        rank = ids.index(expected) + 1 if hit else None
        reciprocal_rank = 1 / rank if hit else 0

        hits += hit
        reciprocal_ranks.append(reciprocal_rank)
        per_query.append({**item, "hit": hit, "rank": rank, "returned": ids})

        mark = "✓" if hit else "✗"
        rank_text = f"rank {rank}" if hit else "miss  "
        print(f"  {mark} {rank_text}  {expected:22} | {item['query'][:70]}")

    return {
        "recall@k": hits / len(items),
        "mrr": sum(reciprocal_ranks) / len(items),
        "hits": hits,
        "total": len(items),
        "per_query": per_query,
    }


### Step 3: Print a summary (overall, per category, and what the misses returned)

def print_summary(name, results, k=K):
    print(f"\n===== {name} =====")
    print(f"recall@{k}: {results['recall@k']:.2f}  ({results['hits']}/{results['total']})")
    print(f"MRR:       {results['mrr']:.2f}")

    #Per-category recall: shows later whether routing helps or hurts rare categories
    by_category = defaultdict(lambda: [0, 0])
    for q in results["per_query"]:
        by_category[q["category"]][0] += q["hit"]
        by_category[q["category"]][1] += 1
    print("\nrecall by category:")
    for category, (h, n) in sorted(by_category.items()):
        print(f"  {category:12} {h}/{n}")

    misses = [q for q in results["per_query"] if not q["hit"]]
    if misses:
        print("\nmisses (expected -> what came back instead):")
        for q in misses:
            print(f"  {q['expected_id']:22} -> {', '.join(q['returned'])}")


### Step 4: Save results so every technique can be compared later

def save_results(name, results):
    os.makedirs(RESULTS_DIR, exist_ok=True)
    path = os.path.join(RESULTS_DIR, f"{name}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\nSaved to {path}")


if __name__ == "__main__":
    method = sys.argv[1] if len(sys.argv) > 1 else "baseline"
    module = importlib.import_module(f"retrieval.{method}")
    retrieve = module.query_retrieve

    items = load_eval_set()
    results = run_evals(retrieve, items)
    print_summary(method, results)
    save_results(method, results)
