from fastapi import Request
from app.main import app
from app.settings import settings
from app.models import (TextProcessor, aggregate_chunked_texts, initialize_embedding_model_and_tokenizer, 
                        get_embeddings_in_batch, vector_database_setup, retrieve_relevant_chunks, 
                        generate_response)
from app.rag_cache import add_document_to_index, ensure_index_initialized, remove_document_from_index
import pdfplumber
from fastapi import FastAPI, Depends, HTTPException, status
from pathlib import Path
from fastapi import Depends, HTTPException, status
from typing import List
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from fastapi import UploadFile, File, BackgroundTasks
import secrets
import json
import logging
from io import BytesIO

logging.basicConfig(level=logging.INFO)

class QueryRequest(BaseModel):
    query: str


@app.post("/upload_documents")
async def upload_documents(files: List[UploadFile] = File(...), req: Request = None):
    data_dir = Path(settings.data_dir)
    data_dir.mkdir(parents=True, exist_ok=True)
    for f in files:
        if f.content_type not in ["text/plain", "application/pdf"]:
            raise HTTPException(status_code=400, detail="Unsupported file type. Only .txt and .pdf files are supported.")
        
        content = await f.read()
        (data_dir / f.filename).write_bytes(content)
        if f.content_type == "text/plain":
            text = content.decode("utf-8", errors="ignore")
        elif f.content_type == "application/pdf":
            with pdfplumber.open(BytesIO(content)) as pdf:
                text = ""
                for page in pdf.pages:
                    text += page.extract_text()
        await add_document_to_index(req.app, f.filename, text)
    return {"message": "Documents uploaded and indexed successfully."}

@app.get("/list_documents")
@app.get("/list_documents/")
async def list_documents():
    """List all documents in the data directory."""
    data_dir = Path(settings.data_dir)
    # log full path of data_dir for debugging
    print("data_dir raw:", repr(settings.data_dir))
    print("data_dir resolved:", Path(settings.data_dir).resolve())
    logging.info("Data directory path: %s", data_dir.resolve())
    if not data_dir.exists():
        raise HTTPException(status_code=404, detail="Data directory not found.")
    
    documents = [f.name for f in data_dir.iterdir() if f.is_file()]
    return {"documents": documents}

@app.get("/get_document/")
async def get_document(filename: str):
    """Retrieve a specific document by filename."""
    file_path = Path(settings.data_dir) / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Document not found.")
    if file_path.suffix.lower() == ".txt":
        return {"filename": filename, "content": file_path.read_text(encoding="utf-8", errors="ignore")}
    elif file_path.suffix.lower() == ".pdf":
        with pdfplumber.open(file_path) as pdf:
            text = ""
            for page in pdf.pages:
                text += page.extract_text()
        return {"filename": filename, "content": text}
    else:
        raise HTTPException(status_code=400, detail="Unsupported file type. Only .txt and .pdf files are supported.")

@app.delete("/delete_document/")
async def delete_document(filename: str, req: Request = None):
    file_path = Path(settings.data_dir) / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Document not found.")
    file_path.unlink()
    await remove_document_from_index(req.app, filename)
    return {"message": f"Document {filename} deleted successfully."}

@app.post("/query_ai")
async def query_ai(request: QueryRequest, req: Request):
    """Query the AI model with a specific question."""
    query = request.query
    embed_model, embed_tokenizer = req.app.state.embed_model, req.app.state.embed_tokenizer
    await ensure_index_initialized(req.app)
    index, all_chunked_texts = req.app.state.rag_index, req.app.state.rag_chunks

    # Retrieve relevant chunks based on the query
    context, distances = retrieve_relevant_chunks(
        query, embed_model, embed_tokenizer,
        index, all_chunked_texts,
    )
    
    response = generate_response(query, context)
    return {"query": query, "response": response, "distances": distances.tolist()}

async def get_embed_model(app):
    if app.state.embed_model is None:
        async with app.state.rag_lock:
            if app.state.embed_model is None:
                app.state.embed_model, app.state.embed_tokenizer = initialize_embedding_model_and_tokenizer()
    return app.state.embed_model, app.state.embed_tokenizer