# app.py
from fastapi import FastAPI, Query
from qa_engine import find_answer

app = FastAPI(
    title="Aurora Q&A System",
    description="A simple API that answers natural-language questions about member data.",
    version="1.0"
)

@app.get("/")
def root():
    """Health check endpoint."""
    return {
        "status": "online",
        "service": "Aurora Q&A System",
        "endpoint": "/ask?question=your-question"
    }

@app.get("/ask")
def ask(question: str = Query(..., description="Enter a natural-language question")):
    """
    API endpoint that receives a question and returns an answer.
    """
    result = find_answer(question)
    return result