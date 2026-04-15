# Result Analysis Summary

This document summarizes the evaluation of the vector model performance based on `RESULTADOS.csv` and the relevance labels in `RESULT/esperados.csv`.

## Data and structure
- `RESULTADOS.csv` contains 100 queries.
- `RESULT/esperados.csv` contains relevance labels for 99 of those queries.
- Each result row in `RESULTADOS.csv` stores a ranked list of tuples `(rank, doc_id, similarity)`.
- The model returns a ranking of almost all documents with similarity scores greater than zero.

## Observed metrics
The computed metrics across the labeled queries are:
- Mean Precision@10: `0.435`
- Mean Precision@20: `0.328`
- Mean Recall@20: `0.213`
- Mean Average Precision (MAP): `0.256`
- Mean coverage of relevant documents: `0.973`
- Minimum coverage: `0.698`
- Maximum coverage: `1.0`
- Queries with full coverage: `56`

## Interpretation
- The model recovers the vast majority of relevant documents: coverage is high at around 97%.
- The top-ranked results are reasonably relevant: on average, about 4 to 5 of the top 10 documents are relevant.
- The MAP value is moderate, indicating that many relevant documents are still ranked lower in the list.
- Recall at 20 is limited, which is expected for queries with many relevant documents, but it indicates the top 20 positions do not capture most of the relevant set.

## Conclusion
The vector model performs acceptably for initial retrieval and ranking, with good overall coverage and decent top-k precision.

However, the results suggest there is room for improvement in ranking quality, especially to push more relevant documents higher in the list and increase average precision.

## Detailed results
Detailed analysis results, including per-query metrics, are saved in `analysis_results.txt`.
