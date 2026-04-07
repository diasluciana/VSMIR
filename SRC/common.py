import csv
import logging
import os
import re
import time
import unicodedata
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Tuple

try:
    from nltk.tokenize import wordpunct_tokenize
except Exception:  # pragma: no cover - fallback when nltk is unavailable
    wordpunct_tokenize = None


def setup_logger(module_name: str, log_dir: str = "logs") -> logging.Logger:
    os.makedirs(log_dir, exist_ok=True)
    logger = logging.getLogger(module_name)
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        formatter = logging.Formatter(
            "%(asctime)s | %(name)s | %(levelname)s | %(message)s"
        )
        file_handler = logging.FileHandler(os.path.join(log_dir, f"{module_name}.log"), encoding="utf-8")
        file_handler.setFormatter(formatter)
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        logger.addHandler(stream_handler)

    return logger


def parse_cfg(
    path: str,
    required_order: List[str],
    allow_multiple_read: bool = False,
    allow_extra_keys: bool = False,
) -> Dict[str, object]:
    with open(path, "r", encoding="utf-8") as f:
        lines = [ln.strip() for ln in f if ln.strip() and not ln.strip().startswith("#")]

    parsed: Dict[str, object] = {}
    read_values: List[str] = []

    for line in lines:
        if "=" not in line:
            raise ValueError(f"Linha invalida no cfg: {line}")
        key, value = [x.strip() for x in line.split("=", 1)]

        if key == "LEIA" and allow_multiple_read:
            read_values.append(value)
            continue

        if key in parsed:
            raise ValueError(f"Chave duplicada no cfg: {key}")
        parsed[key] = value

    if allow_multiple_read:
        if not read_values:
            raise ValueError("Ao menos uma instrucao LEIA=... e obrigatoria")
        parsed["LEIA"] = read_values

    ordered_keys = [k for k in required_order if k != "LEIA"]
    if allow_multiple_read:
        expected = ["LEIA"] + ordered_keys
        present = ["LEIA"] + [k for k in parsed.keys() if k != "LEIA"]
    else:
        expected = required_order
        present = list(parsed.keys())

    for key in required_order:
        if key not in parsed:
            raise ValueError(f"Chave obrigatoria ausente no cfg: {key}")

    # valida ordem quando nao ha repeticao de LEIA
    if not allow_multiple_read:
        if allow_extra_keys:
            if present[: len(expected)] != expected:
                raise ValueError(
                    f"Ordem invalida de instrucoes em {path}. Esperado inicio: {expected}, recebido: {present}"
                )
        elif present != expected:
            raise ValueError(
                f"Ordem invalida de instrucoes em {path}. Esperado: {expected}, recebido: {present}"
            )
    else:
        non_read_order = [k for k in present if k != "LEIA"]
        if non_read_order != ordered_keys:
            raise ValueError(
                f"Ordem invalida de instrucoes em {path}. Esperado apos LEIA: {ordered_keys}, recebido: {non_read_order}"
            )

    return parsed


def strip_accents(text: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFD", text) if unicodedata.category(c) != "Mn"
    )


def normalize_text(text: str) -> str:
    text = text.replace(";", " ")
    text = strip_accents(text)
    text = text.upper()
    text = re.sub(r"[^A-Z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def tokenize_terms(text: str) -> List[str]:
    normalized = normalize_text(text)
    if not normalized:
        return []

    if wordpunct_tokenize:
        tokens = wordpunct_tokenize(normalized)
    else:
        tokens = re.findall(r"[A-Z]+", normalized)

    # Regras do indexador: apenas letras, tamanho >= 2
    return [tk for tk in tokens if re.fullmatch(r"[A-Z]{2,}", tk)]


def write_csv(path: str, header: List[str], rows: Iterable[Iterable[object]]) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow(header)
        for row in rows:
            writer.writerow(row)


@dataclass
class PerfStats:
    counters: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    totals: Dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def add(self, group: str, elapsed: float, count: int = 1) -> None:
        self.counters[group] += count
        self.totals[group] += elapsed

    def avg(self, group: str) -> float:
        count = self.counters[group]
        if count == 0:
            return 0.0
        return self.totals[group] / count


def timed_call(fn, *args, **kwargs):
    start = time.perf_counter()
    result = fn(*args, **kwargs)
    return result, time.perf_counter() - start
