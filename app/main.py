import os
from dotenv import load_dotenv
load_dotenv()
import logging
logger = logging.getLogger(__name__)
from contextlib import asynccontextmanager
from fastapi import FastAPI
from tortoise.contrib.fastapi import register_tortoise
from fastapi.middleware.cors import CORSMiddleware
from app.models import initialize_embedding_model_and_tokenizer
from app.rag_cache import get_or_build_index
import asyncio
import nltk
from pathlib import Path

def _ensure_nltk_data():
    try:
        nltk.data.find("tokenizers/punkt_tab")
    except LookupError:
        fallback_dir = Path(os.environ.get("NLTK_DATA_FALLBACK", "/tmp/nltk_data"))
        fallback_dir.mkdir(parents=True, exist_ok=True)
        nltk.download("punkt_tab", download_dir=str(fallback_dir))
        nltk.data.path.append(str(fallback_dir))

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.embed_model = None
    app.state.embed_tokenizer = None
    app.state.rag_index = None          # faiss index, built lazily/invalidated
    app.state.rag_chunks = None         # list[str] aligned with the index
    app.state.rag_signature = None      # fingerprint of data_dir contents
    app.state.rag_lock = asyncio.Lock() # guards rebuilds

    # Ensure NLTK data is available
    _ensure_nltk_data()
    # Preload model + build index at startup, off the event loop
    try:
        app.state.embed_model, app.state.embed_tokenizer = await asyncio.to_thread(
            initialize_embedding_model_and_tokenizer
        )
        await get_or_build_index(app)
        logger.info("RAG index preloaded successfully at startup.")
    except Exception:
        logger.exception("Failed to preload RAG index at startup; will build lazily on first query.")
    yield

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app import views 