import argparse
import csv
import json
import math
from collections import Counter

from common import PerfStats, parse_cfg, setup_logger, timed_call, tokenize_terms, write_csv


def load_queries(path: str):
    queries = []
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.reader(f, delimiter=";")
        next(reader, None)
        for row in reader:
            if len(row) < 2:
                continue
            qid = row[0].strip()
            qtext = row[1].strip()
            queries.append((qid, qtext))
    return queries


def load_model(path: str):
    with open(path, "r", encoding="utf-8") as f:
        model = json.load(f)
    return model


def query_vector(query_text: str, idf_map: dict):
    # Cada palavra tem peso base 1; a frequencia na consulta vira multiplicador.
    terms = tokenize_terms(query_text)
    tf = Counter(terms)
    qvec = {}
    for term, count in tf.items():
        qvec[term] = 1.0 * count * idf_map.get(term, 0.0)
    qnorm = math.sqrt(sum(v * v for v in qvec.values()))
    return qvec, qnorm


def search(model: dict, queries: list):
    doc_vectors = {int(k): v for k, v in model["doc_vectors"].items()}
    doc_norms = {int(k): v for k, v in model["doc_norms"].items()}
    idf_map = model["idf"]

    result_rows = []

    for qid, qtext in queries:
        qvec, qnorm = query_vector(qtext, idf_map)
        triples = []

        if qnorm > 0:
            scores = []
            for doc_id, dvec in doc_vectors.items():
                dot = 0.0
                for term, qweight in qvec.items():
                    if term in dvec:
                        dot += qweight * dvec[term]

                dnorm = doc_norms.get(doc_id, 0.0)
                sim = dot / (qnorm * dnorm) if dnorm > 0 else 0.0
                if sim > 0:
                    scores.append((doc_id, sim))

            scores.sort(key=lambda x: (-x[1], x[0]))
            triples = [(rank, doc_id, round(score, 8)) for rank, (doc_id, score) in enumerate(scores, 1)]

        result_rows.append((qid, str(triples)))

    return result_rows


def run(cfg_path: str):
    logger = setup_logger("buscador")
    perf = PerfStats()

    logger.info("Modulo Buscador iniciado")
    logger.info("Iniciando leitura do arquivo de configuracao")
    cfg = parse_cfg(cfg_path, ["MODELO", "CONSULTAS", "RESULTADOS"])
    logger.info("Arquivo de configuracao lido: %s", cfg_path)

    logger.info("Iniciando leitura do modelo")
    model = load_model(cfg["MODELO"])

    logger.info("Iniciando leitura das consultas")
    queries = load_queries(cfg["CONSULTAS"])
    logger.info("Dados lidos. Consultas=%d", len(queries))

    logger.info("Iniciando processamento de buscas")
    rows, elapsed = timed_call(search, model, queries)
    perf.add("consultas", elapsed, max(len(queries), 1))

    logger.info("Iniciando escrita dos resultados")
    write_csv(cfg["RESULTADOS"], ["QueryNumber", "Results"], rows)

    logger.info("Tempo medio por consulta: %.6fs", perf.avg("consultas"))
    logger.info("Modulo Buscador finalizado")


def main():
    parser = argparse.ArgumentParser(description="Buscador do modelo vetorial")
    parser.add_argument("--config", default="BUSCA.CFG", help="Caminho do arquivo BUSCA.CFG")
    args = parser.parse_args()

    run(args.config)


if __name__ == "__main__":
    main()
