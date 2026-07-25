from fastapi import FastAPI
from app.api.routes import router

app = FastAPI(
    title="Agentic Data Automation API",
    description="FastAPI backend integrating Pandas analysis and LangGraph AI orchestration.",
    version="1.0.0"
)

# Connect our endpoint routes to the main application
app.include_router(router, prefix="/api")

@app.get("/")
def root():
    return {"message": "Agentic AI System is Online and Ready."}