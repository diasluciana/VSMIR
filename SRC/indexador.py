import argparse
import ast
import csv
import json
import math
from collections import Counter, defaultdict
from typing import Dict

from common import PerfStats, parse_cfg, setup_logger, timed_call


def load_inverted_index(path: str):
    inverted = {}
    all_docs = set()

    with open(path, "r", encoding="utf-8") as f:
        reader = csv.reader(f, delimiter=";")
        next(reader, None)  # header
        for row in reader:
            if len(row) < 2:
                continue
            term = row[0].strip()
            postings = ast.literal_eval(row[1].strip())
            postings = [int(x) for x in postings]
            inverted[term] = postings
            all_docs.update(postings)

    return inverted, sorted(all_docs)


def build_tfidf_model(inverted: Dict[str, list], docs: list, idf_variant: str = "log10"):
    N = len(docs)
    doc_vectors = {doc_id: {} for doc_id in docs}
    norm_map = defaultdict(float)

    for term, postings in inverted.items():
        tf_counter = Counter(postings)
        df = len(tf_counter)
        if df == 0:
            continue

        if idf_variant == "ln":
            idf = math.log(N / df)
        else:
            idf = math.log10(N / df)

        for doc_id, tf in tf_counter.items():
            weight = tf * idf
            doc_vectors[doc_id][term] = weight
            norm_map[doc_id] += weight * weight

    doc_norms = {doc_id: math.sqrt(norm_map[doc_id]) for doc_id in docs}

    return {
        "version": "1.0",
        "weighting": {
            "scheme": "tfidf",
            "idf_variant": idf_variant,
            "tf": "raw_count",
        },
        "document_count": N,
        "vocabulary_size": len(inverted),
        "documents": docs,
        "doc_vectors": {str(k): v for k, v in doc_vectors.items()},
        "doc_norms": {str(k): v for k, v in doc_norms.items()},
        "idf": {
            term: (math.log(N / len(set(postings))) if idf_variant == "ln" else math.log10(N / len(set(postings))))
            for term, postings in inverted.items()
            if postings
        },
    }


def run(cfg_path: str):
    logger = setup_logger("indexador")
    perf = PerfStats()

    logger.info("Modulo Indexador iniciado")
    logger.info("Iniciando leitura do arquivo de configuracao")
    cfg = parse_cfg(cfg_path, ["LEIA", "ESCREVA"], allow_extra_keys=True)
    idf_variant = cfg.get("IDF", "log10").lower()
    if idf_variant not in {"log10", "ln"}:
        raise ValueError("IDF deve ser 'log10' ou 'ln'")
    logger.info("Arquivo de configuracao lido: %s", cfg_path)

    logger.info("Iniciando leitura da lista invertida")
    (inverted, docs), elapsed_read = timed_call(load_inverted_index, cfg["LEIA"])
    logger.info("Dados lidos. Documentos=%d Termos=%d", len(docs), len(inverted))

    logger.info("Iniciando processamento do modelo vetorial")
    model, elapsed_build = timed_call(build_tfidf_model, inverted, docs, idf_variant)
    perf.add("documentos", elapsed_build, max(len(docs), 1))
    perf.add("palavras", elapsed_build, max(len(inverted), 1))

    logger.info("Iniciando persistencia do modelo")
    with open(cfg["ESCREVA"], "w", encoding="utf-8") as f:
        json.dump(model, f, ensure_ascii=True, indent=2)

    logger.info("Tempo de leitura de dados: %.6fs", elapsed_read)
    logger.info("Tempo medio por documento: %.6fs", perf.avg("documentos"))
    logger.info("Tempo medio por palavra: %.6fs", perf.avg("palavras"))
    logger.info("Modulo Indexador finalizado")


def main():
    parser = argparse.ArgumentParser(description="Indexador do modelo vetorial")
    parser.add_argument("--config", default="INDEX.CFG", help="Caminho do arquivo INDEX.CFG")
    args = parser.parse_args()

    run(args.config)


if __name__ == "__main__":
    main()
