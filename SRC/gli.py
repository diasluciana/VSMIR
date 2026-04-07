import argparse
import ast
import xml.etree.ElementTree as ET
from collections import defaultdict
from typing import DefaultDict, List

from common import PerfStats, parse_cfg, setup_logger, timed_call, tokenize_terms, write_csv


def _find_doc_text(record: ET.Element) -> str:
    parts = []
    for child in record:
        tag = child.tag.upper()
        if tag.endswith("ABSTRACT") or tag.endswith("EXTRACT"):
            parts.append((child.text or ""))
    return " ".join(parts)


def _find_doc_id(record: ET.Element) -> str:
    for child in record:
        if child.tag.upper().endswith("RECORDNUM"):
            return (child.text or "").strip()
    return ""


def process_xml_documents(xml_files: List[str]):
    inverted: DefaultDict[str, List[int]] = defaultdict(list)
    doc_count = 0
    word_count = 0

    for xml_file in xml_files:
        tree = ET.parse(xml_file)
        root = tree.getroot()

        for node in root.iter():
            if not node.tag.upper().endswith("RECORD"):
                continue

            doc_id_raw = _find_doc_id(node)
            if not doc_id_raw:
                continue

            doc_count += 1
            doc_id = int(doc_id_raw)
            text = _find_doc_text(node)
            terms = tokenize_terms(text)
            word_count += len(terms)

            for term in terms:
                inverted[term].append(doc_id)

    rows = [(term, str(inverted[term])) for term in sorted(inverted)]
    return rows, doc_count, word_count


def run(cfg_path: str):
    logger = setup_logger("gli")
    perf = PerfStats()

    logger.info("Modulo GLI iniciado")
    logger.info("Iniciando leitura do arquivo de configuracao")
    cfg = parse_cfg(cfg_path, ["LEIA", "ESCREVA"], allow_multiple_read=True)
    logger.info("Arquivo de configuracao lido: %s", cfg_path)

    logger.info("Iniciando leitura dos arquivos XML de documentos")
    (rows, doc_count, word_count), elapsed = timed_call(process_xml_documents, cfg["LEIA"])
    perf.add("documentos", elapsed, max(doc_count, 1))
    perf.add("palavras", elapsed, max(word_count, 1))

    logger.info(
        "Arquivos lidos. Documentos=%d Palavras=%d Termos=%d",
        doc_count,
        word_count,
        len(rows),
    )

    logger.info("Iniciando escrita da lista invertida")
    write_csv(cfg["ESCREVA"], ["Term", "PostingList"], rows)

    logger.info("Tempo medio por documento: %.6fs", perf.avg("documentos"))
    logger.info("Tempo medio por palavra: %.6fs", perf.avg("palavras"))
    logger.info("Modulo GLI finalizado")


def main():
    parser = argparse.ArgumentParser(description="Gerador de Lista Invertida (GLI)")
    parser.add_argument("--config", default="GLI.CFG", help="Caminho do arquivo GLI.CFG")
    args = parser.parse_args()

    run(args.config)


if __name__ == "__main__":
    main()
