from app.main import app
from app.settings import settings
from app.models import *
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

logging.basicConfig(level=logging.INFO)

class QueryRequest(BaseModel):
    query: str

class FileNameRequest(BaseModel):
    filename: str


@app.post("/upload_documents")
async def upload_documents(files: List[UploadFile] = File(...)):
    for f in files:
        content = await f.read()
        (Path(settings.data_dir) / f.filename).write_bytes(content)
    
    return {"message": "Documents uploaded and processed successfully."}

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
async def get_document(request: FileNameRequest):
    """Retrieve a specific document by filename."""
    filename = request.filename
    file_path = Path(settings.data_dir) / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Document not found.")
    return {"filename": filename, "content": file_path.read_text()}

@app.delete("/delete_document/")
async def delete_document(request: FileNameRequest):
    filename = request.filename
    """Delete a specific document by filename."""
    file_path = Path(settings.data_dir) / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Document not found.")
    file_path.unlink()
    return {"message": f"Document {filename} deleted successfully."}

@app.post("/query_ai")
async def query_ai(request: QueryRequest):
    query = request.query
    """Query the AI model with a specific question."""
    # Instantiate the TextProcessor and load documents
    text_processor_object, _ = TextProcessor.load_files(settings.data_dir)

    # Process the texts and prepare them for AI querying
    processed_data, cleaned_text = text_processor_object.process_texts()

    # Get the aggregated chunked texts for AI model input
    all_chunked_texts = aggregate_chunked_texts(processed_data)

    # initialize the embedding model and tokenizer
    model, tokenizer = initialize_embedding_model_and_tokenizer()

    # Get embeddings for the aggregated chunked texts
    embeddings = get_embeddings_in_batch(all_chunked_texts, model, tokenizer)

    # Set up the vector database with the embeddings
    index = vector_database_setup(embeddings)

    # Retrieve relevant chunks based on the query
    context, distances = retrieve_relevant_chunks(query, model, tokenizer, index, all_chunked_texts)
    
    response = generate_response(query, context)
    return {"query": query, "response": response, "distances": distances.tolist()}