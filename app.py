# app.py
from fastapi import FastAPI, Query, HTTPException
from qa_engine import find_answer
import traceback

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
    try:
        result = find_answer(question)
        return result
    except Exception as e:
        # Log the error (will appear in Cloud Logging)
        print(f"Error processing question: {str(e)}")
        print(traceback.format_exc())
        
        # Return a user-friendly error
        raise HTTPException(
            status_code=500,
            detail=f"Error processing question: {str(e)}"
        )