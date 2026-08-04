import os
from dotenv import load_dotenv
load_dotenv() 
from contextlib import asynccontextmanager
from fastapi import FastAPI
from tortoise.contrib.fastapi import register_tortoise
from fastapi.middleware.cors import CORSMiddleware
from app.models import initialize_embedding_model_and_tokenizer
import asyncio

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.embed_model = None
    app.state.embed_tokenizer = None
    app.state.rag_index = None          # faiss index, built lazily/invalidated
    app.state.rag_chunks = None         # list[str] aligned with the index
    app.state.rag_signature = None      # fingerprint of data_dir contents
    app.state.rag_lock = asyncio.Lock() # guards rebuilds
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