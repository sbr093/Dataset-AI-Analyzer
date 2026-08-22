import os
import pandas as pd
import numpy as np
from typing import Dict, Any

from app.services.file_loader import load_dataframe


def analyze_csv_data(file_path: str) -> Dict[str, Any]:
    """Read a supported dataset file, compute robust dataset metrics, and detect z-score anomalies safely."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Dataset not found: {file_path}")
    if os.path.isdir(file_path):
        raise ValueError(f"Expected a dataset file path, got a directory: {file_path}")

    try:
        df = load_dataframe(file_path)
    except Exception as exc:
        raise ValueError(f"Failed to read dataset file '{file_path}': {exc}") from exc

    total_rows = len(df)
    total_columns = len(df.columns)
    duplicate_rows = int(df.duplicated().sum())
    total_missing = int(df.isna().sum().sum())
    missing_values_by_col = df.isna().sum().to_dict()

    if total_rows == 0 or total_columns == 0:
        return {
            "total_rows": total_rows,
            "total_columns": total_columns,
            "duplicate_rows": duplicate_rows,
            "total_missing_values": total_missing,
            "anomaly_count": 0,
            "detailed_anomalies": {},
            "statistical_summary": {
                "summary_statistics": {},
                "missing_values_by_column": missing_values_by_col,
                "detailed_anomalies": {},
                "column_names": df.columns.tolist(),
                "numeric_columns": []
            }
        }

    numeric_df = df.select_dtypes(include=[np.number]).copy()
    object_columns = df.select_dtypes(include=["object", "string", "category"]).columns.tolist()

    for column in object_columns:
        coerced = pd.to_numeric(df[column], errors="coerce")
        if coerced.notna().any():
            numeric_df[column] = coerced

    detailed_anomalies: Dict[str, Any] = {}
    unique_anomalous_rows = set()
    summary_statistics: Dict[str, Any] = {}

    for column in numeric_df.columns:
        series = pd.to_numeric(numeric_df[column], errors="coerce")
        valid_count = int(series.count())
        if valid_count == 0:
            continue

        description = series.describe().to_dict()
        summary_statistics[column] = {
            key: (int(value) if key == "count" else float(value) if pd.notna(value) else None)
            for key, value in description.items()
        }

        if valid_count < 2:
            continue

        std = series.std(ddof=1)
        if pd.isna(std) or std == 0:
            continue

        mean = series.mean()
        z_scores = (series - mean) / std
        outlier_mask = z_scores.abs() > 2.0

        if outlier_mask.any():
            detailed_anomalies[column] = df.loc[outlier_mask, column].tolist()
            unique_anomalous_rows.update(df.loc[outlier_mask].index.tolist())

    anomaly_count = len(unique_anomalous_rows)

    total_cells = max(1, total_rows * total_columns)
    missing_rate = total_missing / total_cells
    duplicate_rate = duplicate_rows / max(1, total_rows)
    anomaly_rate = anomaly_count / max(1, total_rows)

    quality_penalty = (
        min(1.0, missing_rate * 3.0) * 0.4 +
        min(1.0, duplicate_rate * 3.0) * 0.35 +
        min(1.0, anomaly_rate * 3.0) * 0.25
    )
    quality_score = max(0, round((1.0 - quality_penalty) * 100))

    if quality_score >= 90:
        quality_label = "Excellent"
    elif quality_score >= 75:
        quality_label = "Good"
    elif quality_score >= 60:
        quality_label = "Fair"
    elif quality_score >= 40:
        quality_label = "Poor"
    else:
        quality_label = "Critical"

    statistical_summary = {
        "summary_statistics": summary_statistics,
        "missing_values_by_column": missing_values_by_col,
        "detailed_anomalies": detailed_anomalies,
        "column_names": df.columns.tolist(),
        "numeric_columns": numeric_df.columns.tolist()
    }

    return {
        "total_rows": total_rows,
        "total_columns": total_columns,
        "duplicate_rows": duplicate_rows,
        "total_missing_values": total_missing,
        "anomaly_count": anomaly_count,
        "data_quality_score": quality_score,
        "data_quality_label": quality_label,
        "data_quality_breakdown": {
            "missing_rate": round(missing_rate, 4),
            "duplicate_rate": round(duplicate_rate, 4),
            "anomaly_rate": round(anomaly_rate, 4)
        },
        "detailed_anomalies": detailed_anomalies,
        "statistical_summary": statistical_summary
    }
