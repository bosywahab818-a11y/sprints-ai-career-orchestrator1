
from pathlib import Path

from langchain_chroma import Chroma
from langchain_core.embeddings import Embeddings
from sentence_transformers import SentenceTransformer


PROJECT_ROOT = Path(__file__).resolve().parents[2]

DB_PATH = PROJECT_ROOT / "data" / "chroma_db"


class LocalEmbeddings(Embeddings):
    """Original Sprints curriculum embedding model."""

    def __init__(self):
        self.model = SentenceTransformer(
            "sentence-transformers/all-MiniLM-L6-v2"
        )

    def embed_documents(self, texts):
        return self.model.encode(
            texts,
            normalize_embeddings=True
        ).tolist()

    def embed_query(self, text):
        return self.model.encode(
            text,
            normalize_embeddings=True
        ).tolist()


def load_curriculum_db():
    if not (DB_PATH / "chroma.sqlite3").exists():
        raise FileNotFoundError(
            f"Existing curriculum database not found: {DB_PATH}"
        )

    embeddings = LocalEmbeddings()

    db = Chroma(
        collection_name="sprints_curriculum",
        embedding_function=embeddings,
        persist_directory=str(DB_PATH)
    )

    count = db._collection.count()

    if count == 0:
        raise RuntimeError(
            "The curriculum collection is empty."
        )

    return db


vector_db = load_curriculum_db()
