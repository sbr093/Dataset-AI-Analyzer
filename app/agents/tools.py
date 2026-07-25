from langchain_core.tools import tool
from app.services.data_analyzer import analyze_csv_data
import os

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