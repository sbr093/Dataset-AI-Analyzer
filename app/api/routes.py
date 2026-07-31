import os
import shutil
import traceback
import pandas as pd

from fastapi import APIRouter, HTTPException, UploadFile, File, Depends
from pydantic import BaseModel
import json
from sqlalchemy.orm import Session
from langchain_core.messages import HumanMessage
from fastapi.responses import FileResponse
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from app.database.connection import get_db
from app.models.dataset import DatasetReport
from app.services.data_analyzer import analyze_csv_data
from app.agents.workflow import app_workflow

router = APIRouter()
DATA_DIR = "data"

# Ensure the local data directory exists for temporary file processing
os.makedirs(DATA_DIR, exist_ok=True)


def build_dataset_summary(analysis_result: dict) -> dict:
    missing_by_col = analysis_result["statistical_summary"]["missing_values_by_column"]
    top_missing = sorted(missing_by_col.items(), key=lambda item: item[1], reverse=True)[:3]

    return {
        "total_rows": analysis_result["total_rows"],
        "total_columns": analysis_result["total_columns"],
        "duplicate_rows": analysis_result["duplicate_rows"],
        "total_missing_values": analysis_result["total_missing_values"],
        "anomaly_count": analysis_result["anomaly_count"],
        "data_quality_score": analysis_result.get("data_quality_score"),
        "data_quality_label": analysis_result.get("data_quality_label"),
        "data_quality_breakdown": analysis_result.get("data_quality_breakdown"),
        "top_missing_columns": [
            {"column": col, "missing_values": count}
            for col, count in top_missing
        ],
        "detailed_anomalies": analysis_result.get("detailed_anomalies", {}),
        "statistical_summary": analysis_result["statistical_summary"]
    }


def get_cached_dataset_report(db: Session, filename: str):
    return (
        db.query(DatasetReport)
        .filter(DatasetReport.filename == filename)
        .order_by(DatasetReport.created_at.desc())
        .first()
    )


@router.post("/upload")
def upload_dataset(file: UploadFile = File(...), db: Session = Depends(get_db), force_refresh: bool = False):
    """Uploads a CSV, analyzes it via Pandas, and returns the exact frontend contract."""
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are allowed.")

    file_path = os.path.join(DATA_DIR, file.filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    cached_report = None
    if not force_refresh:
        cached_report = get_cached_dataset_report(db, file.filename)

    if cached_report:
        return {
            "message": "Loaded cached analysis",
            "filename": cached_report.filename,
            "filepath": file_path,
            "cached": True,
            "total_rows": cached_report.total_rows,
            "anomaly_count": cached_report.anomaly_count,
            "statistical_summary": cached_report.statistical_summary,
            "dataset_summary": {
                "total_rows": cached_report.total_rows,
                "anomaly_count": cached_report.anomaly_count,
                "statistical_summary": cached_report.statistical_summary,
            },
        }

    try:
        analysis_result = analyze_csv_data(file_path)
    except Exception as exc:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Dataset analysis failed: {exc}")

    db_report = DatasetReport(
        filename=file.filename,
        total_rows=analysis_result["total_rows"],
        anomaly_count=analysis_result["anomaly_count"],
        statistical_summary=analysis_result["statistical_summary"]
    )
    db.add(db_report)
    db.commit()
    db.refresh(db_report)

    total_cells = analysis_result['total_rows'] * analysis_result['total_columns']
    missing_pct = (analysis_result['total_missing_values'] / total_cells * 100) if total_cells > 0 else 0.0

    summary = (
        f"This dataset contains {analysis_result['total_rows']} rows and {analysis_result['total_columns']} columns, "
        f"with a {analysis_result.get('data_quality_label', 'Unknown')} quality score of "
        f"{analysis_result.get('data_quality_score', 0)}%. "
        f"It includes {analysis_result['duplicate_rows']} duplicate row(s) and "
        f"{analysis_result['total_missing_values']} missing value(s) "
        f"({missing_pct:.1f}% of all cells). "
        f"{analysis_result['anomaly_count']} anomalous row(s) were detected across "
        f"{len(analysis_result.get('detailed_anomalies', {}))} numeric field(s)."
    )

    dataset_summary = build_dataset_summary(analysis_result)

    return {
        "message": "File uploaded successfully",
        "filename": file.filename,
        "filepath": file_path,
        "cached": False,
        "total_rows": analysis_result["total_rows"],
        "columns": analysis_result["total_columns"],
        "missing": analysis_result["total_missing_values"],
        "duplicates": analysis_result["duplicate_rows"],
        "anomaly_count": analysis_result["anomaly_count"],
        "data_quality_score": analysis_result.get("data_quality_score", 0),
        "data_quality_label": analysis_result.get("data_quality_label", "Unknown"),
        "data_quality_breakdown": analysis_result.get("data_quality_breakdown", {}),
        "summary": summary,
        "detailed_anomalies": analysis_result.get("detailed_anomalies", {}),
        "statistical_summary": analysis_result["statistical_summary"],
        "dataset_summary": dataset_summary
    }


@router.get("/dataset/cache")
def get_cached_dataset_analysis(filename: str, db: Session = Depends(get_db)):
    report = get_cached_dataset_report(db, filename)
    if not report:
        raise HTTPException(status_code=404, detail="No cached analysis found for this filename.")

    return {
        "filename": report.filename,
        "cached": True,
        "total_rows": report.total_rows,
        "anomaly_count": report.anomaly_count,
        "statistical_summary": report.statistical_summary,
        "created_at": report.created_at,
    }

class ChatRequest(BaseModel):
    query: str
    file_path: str = "data/Updated_Car_Sales_Data.csv"
    dataset_summary: dict = {}


@router.post("/chat")
def chat_with_agent(request: ChatRequest):
    try:
        initial_state = {
            "messages": [HumanMessage(content=request.query)],
            "current_file_path": request.file_path,
            "dataset_summary": request.dataset_summary or {}
        }

        result = app_workflow.invoke(initial_state)
        # Attempt to parse a structured JSON response if the agent returned one
        final_msg = result.get("messages", [])[ -1 ]
        content = getattr(final_msg, "content", "")
        structured = None
        try:
            parsed = json.loads(content)
            if isinstance(parsed, dict) and parsed.get("type") in ("dataset_summary", "anomalies", "chart", "save_report"):
                structured = parsed
        except Exception:
            structured = None

        if structured:
            return {"response": content, "structured": structured}
        return {"response": content}
    except Exception as e:
        print(f"LANGGRAPH AI ERROR: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Agent workflow failed.")

# ... existing code ...

@router.get("/dataset/visualize")
def get_visualization_data(
    file_path: str = "data/Updated_Car_Sales_Data.csv",
    x_axis: str = None,
    y_axis: str = None
):
    try:
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail=f"Visualization file not found: {file_path}")

        df = pd.read_csv(file_path)
        columns = df.columns.tolist()
        response = {"columns": columns}

        if not x_axis or not y_axis:
            response["sample_data"] = df.head(100).fillna("").to_dict(orient="records")
            return response

        if x_axis not in columns or y_axis not in columns:
            raise HTTPException(status_code=400, detail="Selected visualization columns are not present in the dataset.")

        plot_df = df[[x_axis, y_axis]].copy()
        plot_df[x_axis] = plot_df[x_axis].fillna("Unknown").astype(str)
        plot_df[y_axis] = pd.to_numeric(plot_df[y_axis], errors="coerce")
        valid_plot_df = plot_df.dropna(subset=[y_axis])

        aggregated = valid_plot_df.groupby(x_axis)[y_axis].agg(["min", "max", "mean", "count"]).reset_index()
        chart_data = [
            {
                x_axis: row[x_axis],
                f"{y_axis}Min": float(row["min"]),
                f"{y_axis}Max": float(row["max"]),
                f"{y_axis}Average": float(row["mean"]),
                f"{y_axis}Count": int(row["count"])
            }
            for row in aggregated.to_dict(orient="records")
        ]

        highest = None
        lowest = None
        if not valid_plot_df.empty:
            highest_row = valid_plot_df.loc[valid_plot_df[y_axis].idxmax()]
            lowest_row = valid_plot_df.loc[valid_plot_df[y_axis].idxmin()]
            highest = {"x": str(highest_row[x_axis]), "value": float(highest_row[y_axis])}
            lowest = {"x": str(lowest_row[x_axis]), "value": float(lowest_row[y_axis])}

        largest_spread = None
        highest_average = None
        for row in aggregated.to_dict(orient="records"):
            spread = row["max"] - row["min"]
            avg = float(row["mean"])
            if largest_spread is None or spread > largest_spread["range"]:
                largest_spread = {
                    "group": str(row[x_axis]),
                    "range": float(spread),
                    "min": float(row["min"]),
                    "max": float(row["max"]),
                    "avg": avg,
                    "count": int(row["count"])
                }
            if highest_average is None or avg > highest_average["avg"]:
                highest_average = {
                    "group": str(row[x_axis]),
                    "avg": avg,
                    "min": float(row["min"]),
                    "max": float(row["max"]),
                    "count": int(row["count"])
                }

        response.update({
            "chart_data": chart_data,
            "chart_insights": {
                "highest": highest,
                "lowest": lowest,
                "largestSpread": largest_spread,
                "highestAverage": highest_average,
                "totalGroups": int(aggregated.shape[0]),
                "totalRecords": int(valid_plot_df.shape[0])
            },
            "selected_x_axis": x_axis,
            "selected_y_axis": y_axis
        })

        return response
    except HTTPException:
        raise
    except Exception as e:
        print(f"VISUALIZATION ERROR: {str(e)}")
        traceback.print_exc()
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