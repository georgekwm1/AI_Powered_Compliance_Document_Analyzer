from http import client
import re
from gensim.utils import simple_preprocess
from textblob import TextBlob
# from langdetect import detect
import pdfplumber
import fitz  # PyMuPDF
from pathlib import Path



class TextProcessor:
    def __init__(self, texts, directory=None):
        self.texts = texts
        self.directory = directory

    # Load text files
    @classmethod
    def load_files(cls, directory):
        """Load text files from a specified directory and return an instance of TextProcessor."""
        text_data = [] # sample: ["Text of document 1", "Text of document 2", ...]
        file_paths = []

        # Use pathlib.Path to dynamically list all .txt files in directory
        for filepath in Path(directory).rglob("*.*"):
            if filepath.suffix.lower() == ".txt":
                text = filepath.read_text(encoding="utf-8", errors="ignore")
                text_data.append(text)
                file_paths.append(filepath)
            elif filepath.suffix.lower() == ".pdf":
                with pdfplumber.open(filepath) as pdf:
                    text = ""
                    for page in pdf.pages:
                        text += page.extract_text()
                    text_data.append(text)
                    file_paths.append(filepath)
        print("Loaded {} documents from {}".format(len(file_paths), directory))
        return cls(text_data, directory), file_paths

    def clean_text(self, text):
        """Clean the text by removing special characters and digits, and converting to lowercase."""
        # Remove special characters and digits
        if not text:
            return ""
        text = re.sub(r'[^a-zA-Z\s]', '', text)
        # Convert to lowercase
        text = text.lower()
        print("Cleaned text: ", text[:100])  # Print first 100 characters of cleaned text
        return text

    def detect_language(self, text):
        """Detect the language of the text using langdetect."""
        try:
            print("Detecting language for text: ", text[:100])  # Print first 100 characters of text for language detection
            return detect(text)
        except:
            return "unknown"

    def tokenize_text(self, text):
        """Tokenize the text into words using NLTK's word_tokenize."""
        from nltk.tokenize import word_tokenize
        if not text:
            return []
        print("Tokenizing text: ", text[:100])  # Print first 100 characters of text for tokenization
        return word_tokenize(text)

    def chunk_text(self, text, chunk_size=100):
        """Chunk the text into smaller pieces of specified size (in words)."""
        if not text:
            return []
        words = self.tokenize_text(text)
        chunked_texts = []
        for i in range(0, len(words), chunk_size):
            chunked_texts.append(' '.join(words[i:i + chunk_size]))
        print("Chunked text into {} chunks.".format(len(chunked_texts)))  # Print number of chunks created
        return chunked_texts
        # return [' '.join(words[i:i + chunk_size]) for i in range(0, len(words), chunk_size)]

    def correct_spelling(self, text):
        """Correct spelling in the text using TextBlob."""
        blob = TextBlob(text)
        print("Correcting spelling for text: ", text[:100])  # Print first 100 characters of text for spelling correction
        return str(blob.correct())

    def analyze_sentiment(self, text):
        """Analyze the sentiment of the text using TextBlob."""
        if not text:
            return 0.0, 0.0
        blob = TextBlob(text)
        return blob.sentiment.polarity, blob.sentiment.subjectivity

    def process_texts(self):
        """Process the loaded texts: clean, detect language, chunk, and analyze sentiment."""
        processed_data = []
        cleaned_texts = []
        for text in self.texts:
            cleaned_text = self.clean_text(text)

            print("Cleaned text: ", cleaned_text[:100])  # Print first 100 characters of cleaned text
            # corrected_text = self.correct_spelling(cleaned_text)

            # print("Corrected text: ", corrected_text[:100])  # Print first 100 characters of corrected text
            # language = self.detect_language(cleaned_text)
            chunked_texts = self.chunk_text(cleaned_text) # sample: ["Chunk 1 text", "Chunk 2 text", ...]
            # print("Detected language: ", language)  # Print detected language
            polarity, subjectivity = self.analyze_sentiment(cleaned_text)
            processed_data.append({
                "original_text": text,
                "cleaned_text": cleaned_text,
                # "corrected_text": corrected_text,
                'chunked_texts': chunked_texts,
                # "language": language,
                "polarity": polarity,
                "subjectivity": subjectivity
            })
            cleaned_texts.append(cleaned_text)
        print("Processed {} texts.".format(len(processed_data)))  # Print number of processed texts
        return processed_data, cleaned_texts


def aggregate_chunked_texts(processed_data):
    """Aggregate all chunked texts from the processed data into a single list."""
    all_chunked_texts = []
    for data in processed_data:
        all_chunked_texts.extend(data['chunked_texts'])
    print("Aggregated {} chunked texts.".format(len(all_chunked_texts)))  # Print number of aggregated chunked texts
    return all_chunked_texts

def initialize_embedding_model_and_tokenizer():
    """Initialize the embedding model and tokenizer."""

    from transformers import AutoModel, AutoTokenizer
    tokenizer = AutoTokenizer.from_pretrained("sentence-transformers/all-MiniLM-L6-v2")
    model = AutoModel.from_pretrained("sentence-transformers/all-MiniLM-L6-v2")
    print("Initialized embedding model: all-MiniLM-L6-v2")  # Print model initialization message
    return model, tokenizer

def get_embeddings_in_batch(texts, model, tokenizer, batch_size=32):
    """Get embeddings for a list of texts in batches."""
    import numpy as np
    if not texts:
        # Gracefully handle empty chunks instead of passing empty list to np.vstack
        raise ValueError("No text chunks available. Ensure documents are loaded in the data directory.")
    all_embeddings = []
    for i in range(0, len(texts), batch_size):
        batch_texts = texts[i:i+batch_size]
        inputs = tokenizer(batch_texts, padding=True, truncation=True, return_tensors="pt")
        outputs = model(**inputs)
        embeddings = outputs.last_hidden_state[:, 0, :]  # Use the [CLS] token representation
        all_embeddings.append(embeddings.detach().numpy())
    return np.vstack(all_embeddings) # Stack all embeddings vertically to create a single array

def get_query_embedding(query, model, tokenizer):
    """Get embedding for a single query."""
    inputs = tokenizer([query], padding=True, truncation=True, return_tensors="pt")
    outputs = model(**inputs)
    query_embedding = outputs.last_hidden_state[:, 0, :].detach().numpy()  # Use the [CLS] token representation
    return query_embedding

def vector_database_setup(embeddings):
    """Set up a FAISS vector database with the given embeddings."""
    import faiss
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatL2(dimension)  # L2 distance for similarity search
    index.add(embeddings)
    print("Vector database setup complete with {} embeddings.".format(index.ntotal))  # Print number of embeddings added to the index
    return index

def retrieve_relevant_chunks(query, model, tokenizer, index, chunk_map, k=5):
    embedding = get_query_embedding(query, model, tokenizer)
    distances, indices = index.search(embedding, k)
    relevant_chunks = [chunk_map[idx] for idx in indices[0] if idx in chunk_map]
    return relevant_chunks, distances[0]

def generate_response(query, context, max_new_tokens=100):
    import anthropic
    import os
    from app.settings import settings
    api_key = settings.api_key

    client = anthropic.Anthropic(api_key=api_key)
    message = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=max_new_tokens,
        messages=[{
            "role": "user",
            "content": f"User query: {query}\n\nContext:\n{context}\n\nAnswer:"
        }]
    )
    return message.content[0].text