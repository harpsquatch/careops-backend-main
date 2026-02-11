from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine, Base
from routers import patients, visits, workers, accounts

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="CareOps API", version="0.1.0")

# CORS — allow the React dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount routers
app.include_router(patients.router)
app.include_router(visits.router)
app.include_router(workers.router)
app.include_router(accounts.router)


@app.get("/health")
def health():
    return {"status": "ok"}

