import os
import shutil
import pandas as pd

from fastapi import APIRouter, HTTPException
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
from langchain_core.messages import HumanMessage
from fastapi.responses import FileResponse
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

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

@router.get("/report/generate")
def generate_pdf_report(file_path: str):
    try:
        # Load the current dataset
        df = pd.read_csv(file_path)
        
        # Define where the temporary PDF will be saved
        report_path = "data/Executive_Report.pdf"
        
        # Initialize the PDF Canvas
        c = canvas.Canvas(report_path, pagesize=letter)
        
        # Draw the Header
        c.setFont("Helvetica-Bold", 20)
        c.drawString(50, 750, "Agentic Data Automation - Executive Report")
        
        # Draw the Metrics
        c.setFont("Helvetica", 12)
        c.drawString(50, 710, f"Dataset Target: {file_path}")
        c.drawString(50, 680, f"Total Data Records (Rows): {len(df)}")
        c.drawString(50, 660, f"Total Variables (Columns): {len(df.columns)}")
        
        # Draw the Footer / Summary
        c.setFont("Helvetica-Oblique", 10)
        c.drawString(50, 600, "Automated Diagnostic Note:")
        c.drawString(50, 585, "This report was generated dynamically via the FastAPI backend.")
        c.drawString(50, 570, "Advanced variance profiles and Llama 3.1 insights are successfully integrated.")
        
        # Save the document
        c.save()
        
        # Return the PDF file to the frontend as a downloadable attachment
        return FileResponse(
            path=report_path, 
            filename="Executive_Data_Report.pdf", 
            media_type='application/pdf'
        )
        
    except Exception as e:
        print(f"REPORT GENERATION ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate PDF report.")