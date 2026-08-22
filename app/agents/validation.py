from typing import Dict, Any


def validate_dataset_summary(obj: Dict[str, Any]) -> bool:
    if not isinstance(obj, dict):
        return False
    required = ["type", "rows", "columns", "missing_values", "anomaly_count"]
    if obj.get("type") != "dataset_summary":
        return False
    for k in required[1:]:
        if k not in obj:
            return False
        if not isinstance(obj[k], (int, float)):
            return False
    return True


def validate_chart(obj: Dict[str, Any]) -> bool:
    if not isinstance(obj, dict):
        return False
    if obj.get("type") != "chart":
        return False
    if "chart_data" not in obj or not isinstance(obj["chart_data"], list):
        return False
    # check first row keys if exists
    if obj["chart_data"]:
        row = obj["chart_data"][0]
        if not isinstance(row, dict):
            return False
        if "value" not in row:
            return False
    return True


def validate_anomalies(obj: Dict[str, Any]) -> bool:
    if not isinstance(obj, dict):
        return False
    if obj.get("type") != "anomalies":
        return False
    if "items" not in obj or not isinstance(obj["items"], list):
        return False
    # each item should have column and row_index
    for it in obj["items"]:
        if not isinstance(it, dict):
            return False
        if "column" not in it or "row_index" not in it:
            return False
    return True


def validate_extreme_row(obj: Dict[str, Any]) -> bool:
    if not isinstance(obj, dict):
        return False
    if obj.get("type") != "extreme_row":
        return False
    if "row" not in obj or not isinstance(obj["row"], dict):
        return False
    if "column" not in obj or "value" not in obj:
        return False
    return True


def validate_filter_count(obj: Dict[str, Any]) -> bool:
    if not isinstance(obj, dict):
        return False
    if obj.get("type") != "filter_count":
        return False
    if "count" not in obj or not isinstance(obj["count"], (int, float)):
        return False
    return True


def validate_most_common(obj: Dict[str, Any]) -> bool:
    if not isinstance(obj, dict):
        return False
    if obj.get("type") != "most_common":
        return False
    if "top_value" not in obj or "top_count" not in obj:
        return False
    if "distribution" not in obj or not isinstance(obj["distribution"], list):
        return False
    return True
