# SRC/

This folder contains all source code modules of the information retrieval system.

Main scripts:
- `pc.py`: query processor.
- `gli.py`: inverted list generator.
- `indexador.py`: vector model indexer (TF-IDF).
- `buscador.py`: search and ranking module.
- `common.py`: shared utilities (config parsing, normalization, CSV, logging, timing).

Design notes:
- Modules follow batch processing: read all, process all, write all.
- Each module has structured logging for observability and diagnostics.

