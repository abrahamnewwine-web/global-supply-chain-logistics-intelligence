# UAT Test Plan & Defect Log — Global Supply Chain & Logistics Intelligence

*(Excel workbook generated at [`uat_test_log.xlsx`](./uat_test_log.xlsx))*

All 6 automated UAT assertions run via `pytest -v`, verifying foreign-key integrity, `Disruption Rate + Success Rate == 100.0%`, exact weather disruption sums (`3,063`), regional & modal totals (`5,000`), critical route ranking (`Rotterdam → Marseille`), HTTP 400 validation, and CSV export.

**Resolved Defects:** Corrected reference visual typo (`DISTRUPTION` -> `DISRUPTION`) and synchronized executive insight text cards dynamically with filtered SQL metrics.
