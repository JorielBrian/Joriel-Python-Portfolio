import os
from fastapi import FastAPI  # pyright: ignore[reportMissingImports]
from fastapi.middleware.cors import CORSMiddleware  # pyright: ignore[reportMissingImports]

from .routers import projects, qualifications, skills, content

app = FastAPI(title="Joriel Portfolio API", version="0.1.0")

# Comma-separated list in env, e.g.:
# CORS_ORIGINS=http://localhost:3000,https://jorielbriansudario.vercel.app
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


@app.get("/health")
def health():
    return {"status": "ok"}
