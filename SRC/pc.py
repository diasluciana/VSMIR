import argparse
import xml.etree.ElementTree as ET
from typing import List, Tuple

from common import PerfStats, normalize_text, parse_cfg, setup_logger, timed_call, write_csv


def _find_text(node: ET.Element, tag_name: str) -> str:
    for child in node.iter():
        if child.tag.upper().endswith(tag_name):
            return (child.text or "").strip()
    return ""


def _extract_records(query_node: ET.Element) -> List[Tuple[str, int]]:
    records: List[Tuple[str, int]] = []
    for item in query_node.iter():
        if not item.tag.upper().endswith("ITEM"):
            continue

        doc_number = (item.text or "").strip()
        raw_score = item.attrib.get("score", item.attrib.get("SCORE", "0")).strip()

        try:
            vote = 1 if float(raw_score) != 0 else 0
        except ValueError:
            vote = 0

        if doc_number:
            records.append((doc_number, vote))

    return records


def process_queries(xml_path: str):
    tree = ET.parse(xml_path)
    root = tree.getroot()

    query_rows = []
    expected_rows = []

    for query_node in root.iter():
        if not query_node.tag.upper().endswith("QUERY"):
            continue

        query_number = _find_text(query_node, "QUERYNUMBER")
        query_text = _find_text(query_node, "QUERYTEXT")

        if not query_number:
            continue

        norm_text = normalize_text(query_text)
        query_rows.append((query_number.replace(";", ""), norm_text.replace(";", "")))

        for doc_number, vote in _extract_records(query_node):
            expected_rows.append(
                (
                    query_number.replace(";", ""),
                    doc_number.replace(";", ""),
                    vote,
                )
            )

    return query_rows, expected_rows


def run(cfg_path: str) -> None:
    logger = setup_logger("pc")
    perf = PerfStats()

    logger.info("Modulo PC iniciado")
    logger.info("Iniciando leitura do arquivo de configuracao")
    cfg = parse_cfg(cfg_path, ["LEIA", "CONSULTAS", "ESPERADOS"])
    logger.info("Arquivo de configuracao lido: %s", cfg_path)

    logger.info("Iniciando leitura do arquivo de dados XML")
    (query_rows, expected_rows), elapsed_queries = timed_call(process_queries, cfg["LEIA"])
    perf.add("consultas", elapsed_queries, max(len(query_rows), 1))

    logger.info("Dados lidos. Consultas=%d Esperados=%d", len(query_rows), len(expected_rows))

    logger.info("Iniciando escrita do arquivo CONSULTAS")
    write_csv(cfg["CONSULTAS"], ["QueryNumber", "QueryText"], query_rows)

    logger.info("Iniciando escrita do arquivo ESPERADOS")
    write_csv(cfg["ESPERADOS"], ["QueryNumber", "DocNumber", "DocVotes"], expected_rows)

    logger.info(
        "Tempo medio por consulta: %.6fs",
        perf.avg("consultas"),
    )
    logger.info("Modulo PC finalizado")


def main():
    parser = argparse.ArgumentParser(description="Processador de Consultas (PC)")
    parser.add_argument("--config", default="PC.CFG", help="Caminho do arquivo PC.CFG")
    args = parser.parse_args()

    run(args.config)


if __name__ == "__main__":
    main()
