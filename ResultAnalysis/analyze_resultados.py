import csv
from ast import literal_eval
from collections import defaultdict


def load_relevance(path):
    rel = defaultdict(set)
    with open(path, encoding="utf-8") as f:
        reader = csv.reader(f, delimiter=";")
        next(reader, None)
        for qid, doc, vote in reader:
            rel[qid].add(int(doc))
    return rel


def load_results(path):
    results = {}
    with open(path, encoding="utf-8") as f:
        reader = csv.reader(f, delimiter=";")
        next(reader, None)
        for qid, result_text in reader:
            results[qid] = literal_eval(result_text)
    return results


def compute_metrics(rel, results):
    stats = []
    for qid, rel_docs in rel.items():
        ranked = results.get(qid)
        if ranked is None:
            continue

        docs = [doc for _, doc, _ in ranked]
        relevant_hits = 0
        precision_at_k = {10: 0, 20: 0}
        precisions = []

        for i, doc in enumerate(docs, start=1):
            if doc in rel_docs:
                relevant_hits += 1
                precisions.append(relevant_hits / i)
            if i == 10:
                precision_at_k[10] = relevant_hits / 10
            if i == 20:
                precision_at_k[20] = relevant_hits / 20

        if len(docs) < 10:
            precision_at_k[10] = relevant_hits / 10
        if len(docs) < 20:
            precision_at_k[20] = relevant_hits / 20

        recall_at_20 = relevant_hits_at_20 = sum(1 for doc in docs[:20] if doc in rel_docs) / len(rel_docs)
        ap = sum(precisions) / len(rel_docs) if rel_docs else 0.0
        coverage = len(set(docs).intersection(rel_docs)) / len(rel_docs) if rel_docs else 0.0

        stats.append({
            "qid": qid,
            "relevant_docs": len(rel_docs),
            "p10": precision_at_k[10],
            "p20": precision_at_k[20],
            "recall20": recall_at_20,
            "avg_precision": ap,
            "coverage": coverage,
        })

    return stats


def summarize(stats):
    n = len(stats)
    if n == 0:
        return {}

    values = defaultdict(list)
    for item in stats:
        for key, value in item.items():
            if key != "qid":
                values[key].append(value)

    summary = {
        "queries_evaluated": n,
        "mean_p10": sum(values["p10"]) / n,
        "mean_p20": sum(values["p20"]) / n,
        "mean_recall20": sum(values["recall20"]) / n,
        "mean_avg_precision": sum(values["avg_precision"]) / n,
        "mean_coverage": sum(values["coverage"]) / n,
        "min_coverage": min(values["coverage"]),
        "max_coverage": max(values["coverage"]),
        "full_coverage_count": sum(1 for v in values["coverage"] if v == 1.0),
    }
    return summary


def main():
    rel_path = "RESULT/esperados.csv"
    results_path = "RESULTADOS.csv"

    rel = load_relevance(rel_path)
    results = load_results(results_path)
    stats = compute_metrics(rel, results)
    summary = summarize(stats)

    print("=== Resultado da análise ===")
    for key, value in summary.items():
        print(f"{key}: {value}")
    print()
    print("Exemplo de métricas por query:")
    for item in stats[:5]:
        print(item)


if __name__ == "__main__":
    main()
