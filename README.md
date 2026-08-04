# AI Powered Compliance Document Analyzer

Simple FastAPI app to upload, index, and query compliance documents using embeddings.

## Project structure

- `app/` — FastAPI application code
  - `main.py` — app entrypoint
  - `views.py` — API endpoints
  - `models.py` — text processing, embeddings, FAISS index
  - `settings.py` — configuration (data dir, API keys)
- `requirements.txt` — Python dependencies
- `Dockerfile`, `docker-compose.yml` — container setup
- `Procedures_and_Standards_vehicles_explosives/` — sample documents directory

## Prerequisites

- Python 3.11
- Docker & Docker Compose (if using containers)

## Local setup (without Docker)

1. Create and activate a virtual environment:

```bash
python -m venv .venv
.venv\Scripts\activate    # Windows
source .venv/bin/activate   # macOS / Linux
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Start the app:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## Docker

The provided `Dockerfile` already downloads the NLTK tokenizer during build. Rebuild and run:

```bash
docker compose build --no-cache web
docker compose up -d
```

Quick one-off inside a running container (temporary):

```bash
docker compose exec web sh
python -m nltk.downloader punkt_tab
```

Note: downloading inside the container is transient unless persisted in a volume; prefer the Dockerfile build step.

## API Endpoints

- POST `/upload_documents` — multipart file upload. Example:

```bash
curl -X POST "http://localhost:8000/upload_documents" \
  -F "files=@./Procedures_and_Standards_vehicles_explosives/example.txt"
```

- GET `/list_documents` — list filenames in the data directory:

```bash
curl http://localhost:8000/list_documents
```

- GET `/get_document/{filename}` — return file contents

```bash
curl http://localhost:8000/get_document/example.txt
```

- DELETE `/delete_document/{filename}` — delete a file

```bash
curl -X DELETE http://localhost:8000/delete_document/example.txt
```

- POST `/query_ai` — query the indexed documents.

Current implementation expects `query` as a URL query parameter (e.g. `POST /query_ai?query=What+is+policy+X`). Example:

```bash
curl -X POST "http://localhost:8000/query_ai?query=What%20is%20the%20policy%20on%20X"
```

If you change the endpoint to accept a JSON body (recommended for longer text), use a Pydantic model with `{"query":"..."}` as the POST body.

## Notes and troubleshooting

- NLTK resource `punkt_tab` is required for sentence/token tokenizers. The Dockerfile includes a step to download it; if you see a `LookupError: Resource 'punkt_tab' not found`, rebuild the image or download it inside the container.
- `transformers` v5 removed TensorFlow-backed `TFAutoModel`. If you see `ImportError: cannot import name 'TFAutoModel'`, update the code to use `sentence-transformers` (recommended) or switch to PyTorch `AutoModel` and update tensor handling to `return_tensors="pt"` and use `.detach().numpy()`.
- Responses must be JSON serializable — convert NumPy arrays to lists (e.g. `distances.tolist()`) before returning via FastAPI.

## Where to look next

- API handlers: [app/views.py](app/views.py)
- Text processing and embeddings: [app/models.py](app/models.py)
- Settings (data directory, API keys): [app/settings.py](app/settings.py)

If you want, I can:
- Update the `/query_ai` endpoint to accept a JSON body with a Pydantic model
- Replace the embeddings code to use `SentenceTransformer.encode()`
- Add basic tests or an example notebook showing upload → query flow

---
Created by GitHub Copilot assistant
