import hashlib
from pathlib import Path
from fastapi.concurrency import run_in_threadpool
import faiss
import numpy as np


def _get_dimension(model_name_dim=384):  # all-MiniLM-L6-v2 output dim
    return model_name_dim

async def ensure_index_initialized(app):
    """Create an empty, addressable FAISS index once, if not already built."""
    if not hasattr(app.state, "rag_index") or app.state.rag_index is None:
        app.state.rag_index = None
        dim = _get_dimension()
        app.state.rag_index = faiss.IndexIDMap(faiss.IndexFlatL2(dim))
        app.state.rag_chunks = {}       # id -> chunk text
        app.state.rag_file_ids = {}     # filename -> list[int] chunk ids
        app.state.rag_next_id = 0

async def build_initial_index(app):
    """Populate the incremental index from all files in data_dir at startup."""
    from app.settings import settings
    from app.models import TextProcessor

    await ensure_index_initialized(app)

    text_processor_object, file_paths = TextProcessor.load_files(settings.data_dir)
    for text, path in zip(text_processor_object.texts, file_paths):
        await add_document_to_index(app, path.name, text)

async def add_document_to_index(app, filename: str, text: str):
    """Chunk + embed a single new file and add its vectors to the existing index."""
    from app.models import TextProcessor, get_embeddings_in_batch

    async with app.state.rag_lock:
        await ensure_index_initialized(app)

        processor = TextProcessor([text])
        cleaned = processor.clean_text(text)
        chunks = processor.chunk_text(cleaned)
        if not chunks:
            return

        embeddings = await run_in_threadpool(
            get_embeddings_in_batch, chunks, app.state.embed_model, app.state.embed_tokenizer
        )

        start_id = app.state.rag_next_id
        ids = np.arange(start_id, start_id + len(chunks))
        app.state.rag_index.add_with_ids(embeddings, ids)

        for cid, chunk in zip(ids, chunks):
            app.state.rag_chunks[int(cid)] = chunk
        app.state.rag_file_ids[filename] = ids.tolist()
        app.state.rag_next_id = start_id + len(chunks)

async def remove_document_from_index(app, filename: str):
    """Remove a file's vectors from the index without touching anything else."""
    async with app.state.rag_lock:
        ids = app.state.rag_file_ids.pop(filename, None)
        if not ids:
            return
        app.state.rag_index.remove_ids(np.array(ids, dtype=np.int64))
        for cid in ids:
            app.state.rag_chunks.pop(cid, None)