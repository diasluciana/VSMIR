# data/

This folder stores the source dataset files used by the retrieval pipeline.

Contents:
- Document XML files (`cf74.xml` to `cf79.xml`) used by the inverted index generator.
- Query XML file (`cfquery.xml`) used by the query processor.
- DTD files (`cfc-2.dtd`, `cfcquery-2.dtd`) describing XML structure.
- Collection reference material (HTML description file).

Notes:
- These files are treated as input data.
- The pipeline reads from this folder but does not need to overwrite original files.

