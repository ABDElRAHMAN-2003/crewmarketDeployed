from fastapi import FastAPI
from fastapi.responses import JSONResponse
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))
from marketcompare.main import run
import uvicorn

app = FastAPI(title="Market Comparison API", version="1.0.0")

@app.get("/")
def root():
    return {"message": "Market Comparison API is running"}

@app.get("/run/market")
def run_market_crew():
    try:
        report = run()
        return JSONResponse(content=report)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

@app.get("/health")
def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run("index:app", host="0.0.0.0", port=8003, reload=True)