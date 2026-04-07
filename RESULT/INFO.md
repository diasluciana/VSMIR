
# RESULT/

This folder stores intermediate and final artifacts produced by the pipeline.

Expected outputs:
- `consultas.csv`: processed queries.
- `esperados.csv`: expected query-document relevance votes.
- `lista_invertida.csv`: inverted list representation.
- `modelo_vetorial.json`: persisted vector-space model.

Notes:
- Files are generated in batch mode by each module.
- `RESULTADOS.csv` is written at project root by the search module.
