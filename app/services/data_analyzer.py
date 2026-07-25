import pandas as pd
import numpy as np
from typing import Dict, Any

def analyze_csv_data(file_path: str) -> Dict[str, Any]:
    """
    Reads a CSV file, generates statistical summaries, and detects basic anomalies.
    """
    # 1. Load the data using Pandas
    try:
        df = pd.read_csv(file_path)
    except Exception as e:
        raise ValueError(f"Failed to read CSV file: {str(e)}")
        
    # 2. Extract Basic Metadata
    total_rows = len(df)
    
    # 3. Generate Statistical Summary
    # We isolate numeric columns because we can't calculate a 'mean' on text data
    numeric_df = df.select_dtypes(include=[np.number])
    
    # .describe() calculates count, mean, std, min, 25%, 50%, 75%, max
    summary_stats = numeric_df.describe().to_dict()
    
    # Identify how many missing (null) values exist in every column
    missing_values = df.isnull().sum().to_dict()
    
    # 4. Anomaly Detection (Using Z-Score)
    # A Z-score > 3 means the data point is more than 3 standard deviations away from the mean
    anomaly_count = 0
    if not numeric_df.empty:
        # Calculate Z-scores for all numeric columns
        z_scores = np.abs((numeric_df - numeric_df.mean()) / numeric_df.std(ddof=0))
        
        # Flag any row that has at least one column with a Z-score > 3
        anomalies = (z_scores > 3).any(axis=1)
        anomaly_count = int(anomalies.sum())

    # 5. Compile the final structured dictionary
    statistical_summary = {
        "summary_statistics": summary_stats,
        "missing_values": missing_values,
        "column_names": df.columns.tolist()
    }

    return {
        "total_rows": total_rows,
        "anomaly_count": anomaly_count,
        "statistical_summary": statistical_summary
    }