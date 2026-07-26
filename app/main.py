from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router

app = FastAPI(
    title="Agentic Data Automation API",
    description="FastAPI backend integrating Pandas analysis and LangGraph AI orchestration.",
    version="1.0.0"
)

# Add CORS Middleware to authorize React cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows requests from any origin (localhost:5173, etc.)
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (POST, GET, OPTIONS, etc.)
    allow_headers=["*"],  # Allows all headers
)

# Connect our endpoint routes to the main application
app.include_router(router, prefix="/api")

@app.get("/")
def root():
    return {"message": "Agentic AI System is Online and Ready."}