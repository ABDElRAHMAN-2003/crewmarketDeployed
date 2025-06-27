# Option A: Use relative imports in api.py
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from .main import run
import uvicorn

app = FastAPI()

@app.get("/run/market")
def run_market_crew():
    report = run()
    return JSONResponse(content=report.model_dump())

# if __name__ == "__main__":
#     uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)