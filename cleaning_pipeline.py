"""Reusable data-cleaning pipeline for mobile money agent transactions."""

from __future__ import annotations

import numpy as np
import pandas as pd


def clean_agent_data(
    txns: pd.DataFrame, agents: pd.DataFrame
) -> tuple[pd.DataFrame, dict]:
    """Clean raw mobile money agent transactions and merge with agent metadata.

    Applies deterministic, rule-based cleaning without hard-coded row indices:
    1. Audits data issues across six dimensions (Uniqueness, Consistency, Validity,
       Completeness, Accuracy, Timeliness).
    2. Removes duplicate `txn_id` records (keeping first occurrence).
    3. Standardises `txn_type` to Title Case ("Deposit" or "Withdrawal").
    4. Parses `amount` to numeric, flags missing/non-numeric values via
       `amount_imputed`, and imputes using per-`txn_type` median (fallback overall median).
    5. Parses `txn_date` to ISO format (`YYYY-MM-DD`).
    6. Flags extreme amounts outside `[Q1 - 1.5 * IQR, Q3 + 1.5 * IQR]` via `is_outlier`.
    7. Left-joins `agents` on `agent_id` and labels unmatched agents as `"Unknown"`.

    Returns
    -------
    tuple[pd.DataFrame, dict]
        `(clean_df, log)` where `clean_df` is the cleaned transaction DataFrame and
        `log` records audit findings, counts, imputation medians, IQR fences, and merge stats.
    """
    raw_rows = len(txns)
    raw_numeric = pd.to_numeric(txns["amount"], errors="coerce")
    raw_dates = pd.to_datetime(txns["txn_date"], format="mixed", errors="coerce")

    dup_extra_rows = int(txns.duplicated(subset=["txn_id"]).sum())
    inconsistent_type_rows = int(
        (~txns["txn_type"].isin(["Deposit", "Withdrawal"])).sum()
    )
    slash_date_rows = int(txns["txn_date"].astype(str).str.contains("/", na=False).sum())
    unparseable_date_rows = int(raw_dates.isna().sum())
    missing_na_amount_rows = int(txns["amount"].isna().sum())
    non_numeric_str_amount_rows = int(
        (txns["amount"].notna() & raw_numeric.isna()).sum()
    )
    high_value_250k_rows = int((raw_numeric == 250000).sum())
    unknown_agent_raw_rows = int((~txns["agent_id"].isin(agents["agent_id"])).sum())

    audit_df = pd.DataFrame([
        {
            "issue": "Duplicate txn_id rows",
            "dimension": "Uniqueness",
            "column": "txn_id",
            "rows_affected": dup_extra_rows,
        },
        {
            "issue": "Non-standard casing or trailing whitespace in txn_type",
            "dimension": "Consistency",
            "column": "txn_type",
            "rows_affected": inconsistent_type_rows,
        },
        {
            "issue": "Slash date delimiter (YYYY/MM/DD instead of YYYY-MM-DD)",
            "dimension": "Validity",
            "column": "txn_date",
            "rows_affected": slash_date_rows,
        },
        {
            "issue": "Missing (NaN) transaction amounts",
            "dimension": "Completeness",
            "column": "amount",
            "rows_affected": missing_na_amount_rows,
        },
        {
            "issue": "Non-numeric text (\x27N/A\x27) in transaction amounts",
            "dimension": "Validity",
            "column": "amount",
            "rows_affected": non_numeric_str_amount_rows,
        },
        {
            "issue": "Extreme KES 250,000 transaction amounts",
            "dimension": "Accuracy",
            "column": "amount",
            "rows_affected": high_value_250k_rows,
        },
        {
            "issue": "Unregistered agent_id (\x27AG099\x27) not in agents register",
            "dimension": "Consistency",
            "column": "agent_id",
            "rows_affected": unknown_agent_raw_rows,
        },
    ])

    df = txns.drop_duplicates(subset=["txn_id"], keep="first").copy()
    rows_after_dedup = len(df)

    df["txn_type"] = df["txn_type"].astype(str).str.strip().str.capitalize()

    parsed_amt = pd.to_numeric(df["amount"], errors="coerce")
    df["amount_imputed"] = parsed_amt.isna()

    medians_by_type = (
        pd.DataFrame({"txn_type": df["txn_type"], "amt": parsed_amt})
        .groupby("txn_type")["amt"]
        .median()
        .to_dict()
    )
    overall_median = float(parsed_amt.median())
    df["amount"] = (
        parsed_amt.fillna(df["txn_type"].map(medians_by_type))
        .fillna(overall_median)
        .astype(float)
    )

    parsed_dt = pd.to_datetime(df["txn_date"], format="mixed", errors="coerce")
    df["txn_date"] = parsed_dt.dt.strftime("%Y-%m-%d")

    q1 = float(df["amount"].quantile(0.25))
    q3 = float(df["amount"].quantile(0.75))
    iqr = q3 - q1
    lower_fence = q1 - 1.5 * iqr
    upper_fence = q3 + 1.5 * iqr
    df["is_outlier"] = (df["amount"] < lower_fence) | (df["amount"] > upper_fence)

    unknown_agents_clean = int((~df["agent_id"].isin(agents["agent_id"])).sum())
    agent_lookup = agents[["agent_id", "county"]].drop_duplicates(subset=["agent_id"])
    df = df.merge(agent_lookup, on="agent_id", how="left")
    df["county"] = df["county"].fillna("Unknown")

    clean_df = df[[
        "txn_id",
        "agent_id",
        "county",
        "txn_type",
        "amount",
        "txn_date",
        "amount_imputed",
        "is_outlier",
    ]].copy()

    log = {
        "raw_rows": raw_rows,
        "clean_rows": len(clean_df),
        "rows_after_dedup": rows_after_dedup,
        "duplicates_removed": dup_extra_rows,
        "imputed_rows": int(clean_df["amount_imputed"].sum()),
        "medians_by_type": medians_by_type,
        "overall_median": overall_median,
        "iqr_bounds": {
            "q1": q1,
            "q3": q3,
            "iqr": iqr,
            "lower_fence": lower_fence,
            "upper_fence": upper_fence,
        },
        "outlier_rows": int(clean_df["is_outlier"].sum()),
        "unknown_agent_txns_raw": unknown_agent_raw_rows,
        "unknown_agent_txns_clean": unknown_agents_clean,
        "unparseable_date_rows": unparseable_date_rows,
        "audit_table": audit_df,
    }
    return clean_df, log
