"""
Milestone 4 — Embedding and retrieval for The Unofficial Guide.

Loads the chunks built in ingest.py, embeds them locally with
all-MiniLM-L6-v2, and stores them in a persistent ChromaDB collection. Provides
retrieve() for semantic search over the stored reviews.

Matches planning.md > Retrieval Approach:
  - embedding model: all-MiniLM-L6-v2 (local, no API cost)
  - vector store: ChromaDB (persistent), cosine distance
  - top-k: 5

This milestone does NOT call Groq or build any UI.
"""
from chromadb import PersistentClient
from sentence_transformers import SentenceTransformer

from ingest import build_all_chunks

CHROMA_PATH = "chroma_db"
COLLECTION_NAME = "unofficial_guide"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

# Load the embedding model once at import. sentence-transformers downloads the
# model on first use (cached afterward).
_model = SentenceTransformer(EMBEDDING_MODEL)

# Persistent client so embeddings survive between runs. We pass embeddings to
# ChromaDB ourselves (no embedding_function), so the collection just stores the
# vectors we give it. cosine distance matches the planning.md retrieval design.
_client = PersistentClient(path=CHROMA_PATH)
_collection = _client.get_or_create_collection(
    name=COLLECTION_NAME,
    metadata={"hnsw:space": "cosine"},
)


def _embed(texts):
    """Embed a list of strings, returning plain Python lists for ChromaDB."""
    return _model.encode(texts, show_progress_bar=False).tolist()


def build_index():
    """
    Embed all chunks and store them in ChromaDB.

    Skips work if the collection is already populated, so re-running the script
    doesn't duplicate chunks. To force a rebuild, delete the chroma_db/ folder.
    """
    chunks = build_all_chunks()

    existing = _collection.count()
    if existing >= len(chunks):
        print(
            f"Collection '{COLLECTION_NAME}' already populated "
            f"({existing} chunks). Skipping embedding."
        )
        print("To rebuild, delete the chroma_db/ folder and re-run.")
        return

    print(f"Embedding {len(chunks)} chunks with {EMBEDDING_MODEL}...")
    documents = [c["text"] for c in chunks]
    embeddings = _embed(documents)

    _collection.add(
        ids=[c["chunk_id"] for c in chunks],
        documents=documents,
        metadatas=[c["metadata"] for c in chunks],
        embeddings=embeddings,
    )
    print(f"Stored {_collection.count()} chunks in '{COLLECTION_NAME}'.")


def retrieve(query, n_results=5):
    """
    Semantic search over the stored review chunks.

    Returns a list of dicts (most to least relevant) with: text, professor,
    course (only when the chunk has one), source_file, chunk_type, distance.
    Returns [] if the collection is empty.
    """
    if _collection.count() == 0:
        return []

    query_embedding = _embed([query])
    results = _collection.query(
        query_embeddings=query_embedding,
        n_results=n_results,
        include=["documents", "metadatas", "distances"],
    )

    # query() nests one list per query string; we only sent one query -> [0].
    documents = results["documents"][0]
    metadatas = results["metadatas"][0]
    distances = results["distances"][0]

    output = []
    for text, meta, distance in zip(documents, metadatas, distances):
        item = {
            "text": text,
            "professor": meta.get("professor", "Unknown"),
            "source_file": meta.get("source_file", "Unknown"),
            "chunk_type": meta.get("chunk_type", "Unknown"),
            "distance": distance,
        }
        if "course" in meta:
            item["course"] = meta["course"]
        output.append(item)
    return output


def main():
    build_index()

    test_queries = [
        "What do students say about Michael Lanners' teaching style and his use of Zybooks?",
        "According to reviews, why are Daniel Cliburn's COMP 53 midterms considered difficult?",
        "What grading leniency does Afsoon Zowj offer students?",
    ]

    for query in test_queries:
        print("\n" + "=" * 78)
        print(f"QUERY: {query}")
        print("=" * 78)
        results = retrieve(query, n_results=5)
        for rank, r in enumerate(results, start=1):
            course = r.get("course", "(n/a)")
            print(f"\n[{rank}] distance={r['distance']:.3f}  "
                  f"professor={r['professor']}  course={course}")
            print(f"    source_file={r['source_file']}  chunk_type={r['chunk_type']}")
            preview = r["text"][:400].replace("\n", " ")
            print(f"    text: {preview}...")


if __name__ == "__main__":
    main()
