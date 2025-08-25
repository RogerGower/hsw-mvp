from fastapi import FastAPI

app = FastAPI(title="Observation Service", version="0.0.1")

@app.get("/")
def root():
    return {"message": "Hello, Observation Service"}

@app.get("/health")
def health():
    return {"ok": True, "service": "observation", "version": "0.0.1"}
