from langchain_core.tools import tool
from app.services.data_analyzer import analyze_csv_data
import os
import pandas as pd


@tool
def analyze_dataset_tool(file_path: str) -> dict:
    """
    Use this tool to analyze a CSV dataset.
    It returns total rows, anomaly counts, and statistical summaries.
    """
    # Safety check to ensure the file exists before processing
    if not os.path.exists(file_path):
        return {"error": f"File not found at {file_path}"}

    try:
        report = analyze_csv_data(file_path)
        return report
    except Exception as e:
        return {"error": f"Failed to analyze dataset: {str(e)}"}


@tool
def summarize_dataset_tool(file_path: str) -> dict:
    """
    Return a short structured summary for the dataset (rows, columns, top issues).
    """
    if not os.path.exists(file_path):
        return {"error": "file_not_found", "message": f"File not found: {file_path}"}

    try:
        report = analyze_csv_data(file_path)
        summary = {
            "type": "dataset_summary",
            "rows": report.get("total_rows", 0),
            "columns": report.get("total_columns", 0),
            "missing_values": report.get("total_missing_values", 0),
            "duplicate_rows": report.get("duplicate_rows", 0),
            "anomaly_count": report.get("anomaly_count", 0),
            "data_quality_score": report.get("data_quality_score"),
            "top_missing_columns": report.get("statistical_summary", {}).get("missing_values_by_column", {})
        }
        return summary
    except Exception as e:
        return {"error": "analysis_failed", "message": str(e)}


@tool
def generate_chart_tool(file_path: str, x_axis: str, y_axis: str, agg: str = "mean", max_groups: int = 100) -> dict:
    """
    Return chart-ready JSON: columns, chart_data (list of small dicts), and lightweight insights.
    """
    if not os.path.exists(file_path):
        return {"error": "file_not_found"}

    try:
        # Read only the necessary columns to keep memory usage low
        df = pd.read_csv(file_path, usecols=[x_axis, y_axis])
    except Exception as e:
        return {"error": "read_failed", "message": str(e)}

    try:
        df[x_axis] = df[x_axis].fillna("Unknown").astype(str)
        df[y_axis] = pd.to_numeric(df[y_axis], errors="coerce")
        df = df.dropna(subset=[y_axis])

        if df.empty:
            return {"type": "chart", "chart_data": [], "insights": {"note": "no_numeric_data"}}

        if agg == "mean":
            agg_df = df.groupby(x_axis)[y_axis].agg(["mean", "count"]).reset_index()
            agg_df = agg_df.sort_values("count", ascending=False).head(max_groups)
            chart_rows = [
                {x_axis: str(r[x_axis]), "value": float(r["mean"]), "count": int(r["count"])}
                for r in agg_df.to_dict(orient="records")
            ]
        else:
            agg_df = df.groupby(x_axis)[y_axis].agg([agg, "count"]).reset_index()
            agg_df = agg_df.sort_values("count", ascending=False).head(max_groups)
            stat_col = agg
            chart_rows = [
                {x_axis: str(r[x_axis]), "value": float(r[stat_col]), "count": int(r["count"])}
                for r in agg_df.to_dict(orient="records")
            ]

        insights = {"total_groups": len(chart_rows), "top_group": chart_rows[0][x_axis] if chart_rows else None}
        return {"type": "chart", "x": x_axis, "y": y_axis, "chart_data": chart_rows, "insights": insights}
    except Exception as e:
        return {"error": "aggregation_failed", "message": str(e)}