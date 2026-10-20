import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import projects, qualifications, skills, content, auth, resume

app = FastAPI(title="Joriel Portfolio API", version="0.1.0")

origins = [o.strip() for o in os.environ.get("CORS_ORIGINS", "").split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(projects.router)
app.include_router(qualifications.router)
app.include_router(skills.router)
app.include_router(content.router)
app.include_router(auth.router)
app.include_router(resume.router)


@app.get("/health")
def health():
    return {"status": "ok"}
