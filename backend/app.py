from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import logging
from pydantic import BaseModel
from retrieval.generate import generate

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

@app.get("/health")
def health():
    return {"status": "ok"}

class SearchRequest(BaseModel):
    query: str

origins = [
    'https://www.outage-oracle.ca',
    'https://outage-oracle.ca',
    'http://localhost:5173'
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post('/search')
def search(req: SearchRequest):
    if not req.query.strip():
        raise HTTPException(status_code=400, detail="Empty Query submitted")

    if len(req.query) > 500:
        raise HTTPException(status_code=413, detail="Too large Query submitted")

    try:
        result = generate(req.query)
                        
    except Exception as e:
        logger.error(f"Relevant incident document retrieval failed: {e}")
        raise HTTPException(status_code=500, detail="Retrieval failed")
                
    logger.info(f"Successfully retrieved document")
    return result