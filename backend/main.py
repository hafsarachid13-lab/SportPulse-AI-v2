from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import os
import logging

# ✅ Import BOTH routers
from controllers.review_controller import router as review_router
from views.review_routes import router as legacy_routes

# ── Logging ─────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)

# ── App Init ────────────────────────────────────────
app = FastAPI(
    title="Sports Press Review API",
    version="1.0.0"
)

# ── ✅ CORS FIX (VERY IMPORTANT) ────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # change to frontend URL in prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Static folder for PDFs ─────────────────────────
BASE_DIR = os.path.dirname(__file__)
STATIC_PDF_DIR = os.path.join(BASE_DIR, "static_pdfs")
os.makedirs(STATIC_PDF_DIR, exist_ok=True)

app.mount("/static", StaticFiles(directory=STATIC_PDF_DIR), name="static")

# ── Include routes ─────────────────────────────────
app.include_router(review_router) # Handles /review/*
app.include_router(legacy_routes) # Fallback for /news and /sources

# ── Dashboard (optional) ───────────────────────────
@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    html_path = os.path.join(BASE_DIR, "views", "index.html")
    if os.path.exists(html_path):
        with open(html_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse("<h1>Dashboard not found</h1>")

# ── Health check ───────────────────────────────────
@app.get("/health")
async def health():
    return {"status": "ok"}

# ── Run server ─────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
