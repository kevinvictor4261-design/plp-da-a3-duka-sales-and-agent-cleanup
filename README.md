# PLP Data Analytics Assignment 3 — Duka Sales & Agent Cleanup (`plp-da-a3-duka-sales-and-agent-cleanup`)

## Engagements Summary
* **Engagement 1 — Duka Electronics (H1 2026 Sales Exploration):** Explores `1,000` orders (`seed 2026`, January–June 2026) across five branches, five products, and three channels; computes derived metrics; answers leadership questions on branch rankings, product revenue vs. units, weekend vs. weekday performance, monthly seasonality, and Premium online orders in Nairobi and Mombasa; exports `outputs/premium_online_coast_capital.csv`; and builds `excel/duka_branch_summary.xlsx` using `SUMIFS` and `XLOOKUP`[cite: 2, 4].
* **Engagement 2 — Mobile Money Agent Network (Audit, Cleaning & Summary):** Audits raw transaction records (`seed 44`) against the agent register (`agents.csv`), applies a reusable `clean_agent_data(txns, agents)` function in `cleaning_pipeline.py` with a cleaning log, flags missing/imputed amounts and IQR outliers, merges county metadata, generates county-by-type and weekly county pivot summaries, and presents a six-dimension Data Quality Report with Kenya Data Protection Act (2019) privacy protections[cite: 1, 2, 3].

## Duka Executive Summary
* Duka Electronics generated **KES 71,792,500** in total revenue across **1,000** orders from January 1, 2026 to June 29, 2026[cite: 2, 4].
* The Nairobi branch led performance with **KES 26,106,100** (**36.36%** of total revenue across **376** orders), followed by Mombasa at **KES 14,003,700**[cite: 4].
* Laptops dominated product revenue at **KES 41,535,000** (**57.85%** of revenue), whereas Tablets ranked first in unit volume with **691** units sold[cite: 4].
* April 2026 (`2026-04`) was the strongest month at **KES 13,518,300**, outperforming June 2026 (`2026-06`, the lowest month at **KES 10,903,400**) by **23.98%**[cite: 4].
* Premium online orders from Nairobi and Mombasa totaled **83** orders and **KES 10,218,000** in revenue[cite: 4].

## Agent Data Row Counts (Before vs. After)
* **Before cleaning (`agent_transactions.csv` raw extract):** **612** rows (`5` columns)[cite: 2, 3].
* **After cleaning (`outputs/agent_transactions_clean.csv`):** **600** rows (`8` columns) after removing **12** duplicate `txn_id` rows (`keep="first"`), imputing **20** missing/non-numeric amounts (`amount_imputed=True`), flagging **53** IQR outliers (`is_outlier=True`), and left-joining agent `county` (`7` deduplicated rows with unknown agent `AG099` assigned `county="Unknown"`)[cite: 1, 2, 3].

## How to Regenerate Data and Run Notebooks
```bash
pip install -r requirements.txt
python generate_data.py
jupyter nbconvert --to notebook --execute --inplace duka_sales_exploration.ipynb
jupyter nbconvert --to notebook --execute --inplace agent_cleanup.ipynb