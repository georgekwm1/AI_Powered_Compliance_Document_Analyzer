import hashlib
from pathlib import Path

def compute_data_signature(data_dir: str) -> str:
    """Cheap fingerprint of directory contents (names + mtimes + sizes)."""
    parts = []
    for f in sorted(Path(data_dir).rglob("*.*")):
        stat = f.stat()
        parts.append(f"{f.name}:{stat.st_mtime_ns}:{stat.st_size}")
    return hashlib.sha256("|".join(parts).encode()).hexdigest()

async def get_or_build_index(app, force_rebuild: bool = False):
    from app.settings import settings
    from app.models import (
        TextProcessor, aggregate_chunked_texts,
        get_embeddings_in_batch, vector_database_setup,
    )

    signature = compute_data_signature(settings.data_dir)

    async with app.state.rag_lock:
        if (
            not force_rebuild
            and app.state.rag_index is not None
            and app.state.rag_signature == signature
        ):
            return app.state.rag_index, app.state.rag_chunks

        # Rebuild only when the directory actually changed (or first call)
        text_processor_object, _ = TextProcessor.load_files(settings.data_dir)
        processed_data, _ = text_processor_object.process_texts()
        all_chunked_texts = aggregate_chunked_texts(processed_data)

        embeddings = get_embeddings_in_batch(
            all_chunked_texts, app.state.embed_model, app.state.embed_tokenizer
        )
        index = vector_database_setup(embeddings)

        app.state.rag_index = index
        app.state.rag_chunks = all_chunked_texts
        app.state.rag_signature = signature
        return index, all_chunked_texts

def invalidate_index(app):
    """Invalidate the current FAISS index, forcing a rebuild on next query."""
    async def _invalidate():
        async with app.state.rag_lock:
            app.state.rag_index = None
            app.state.rag_chunks = None
            app.state.rag_signature = None
    import asyncio
    asyncio.create_task(_invalidate())