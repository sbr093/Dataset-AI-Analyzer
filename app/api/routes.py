import os
import shutil
import pandas as pd
from fastapi import APIRouter, HTTPException
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
from langchain_core.messages import HumanMessage

from app.database.connection import get_db
from app.models.dataset import DatasetReport
from app.schemas.dataset import DatasetReportResponse
from app.services.data_analyzer import analyze_csv_data
from app.agents.workflow import app_workflow

router = APIRouter()
DATA_DIR = "data"

# Ensure the local data directory exists for temporary file processing
os.makedirs(DATA_DIR, exist_ok=True)

@router.post("/upload", response_model=DatasetReportResponse)
def upload_dataset(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Uploads a CSV, analyzes it via Pandas, and saves the report to PostgreSQL."""
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are allowed.")
        
    file_path = os.path.join(DATA_DIR, file.filename)
    
    # Save file locally
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    # Analyze using your isolated Pandas Service
    try:
        analysis_result = analyze_csv_data(file_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        
    # Persist the results to the database via SQLAlchemy
    db_report = DatasetReport(
        filename=file.filename,
        total_rows=analysis_result["total_rows"],
        anomaly_count=analysis_result["anomaly_count"],
        statistical_summary=analysis_result["statistical_summary"]
    )
    db.add(db_report)
    db.commit()
    db.refresh(db_report)
    
    return db_report

@router.post("/chat")
def chat_with_agent(query: str, file_path: str = "data/Updated_Car_Sales_Data.csv"):
    try:
        initial_state = {
            "messages": [HumanMessage(content=query)],
            "current_file_path": file_path, 
            "dataset_summary": {} 
        }
        
        result = app_workflow.invoke(initial_state)
        return {"response": result["messages"][-1].content}
    except Exception as e:
        print(f"LANGGRAPH AI ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Agent workflow failed.")

# ... existing code ...

@router.get("/dataset/visualize")
def get_visualization_data(file_path: str = "data/Updated_Car_Sales_Data.csv"):
    try:
        df = pd.read_csv(file_path)
        df = df.fillna("") # Clean NaN values for JSON safety
        
        return {
            "columns": df.columns.tolist(),
            "data": df.to_dict(orient="records")
        }
    except Exception as e:
        print(f"VISUALIZATION ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to load dataset for visualization.")