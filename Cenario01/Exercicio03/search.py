from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import chromadb
from sentence_transformers import SentenceTransformer

from ingest import COLLECTION_NAME, EMBEDDING_MODEL_NAME
from prompt_builder import build_prompt


@dataclass
class SearchResult:
    chunk_id: str
    text: str
    metadata: dict[str, Any]
    distance: float
    similarity_score: float


def search_similar_chunks(
    question: str,
    n_results: int = 5,
    base_dir: Path | None = None,
) -> list[SearchResult]:
    """Busca os N chunks mais similares para uma pergunta no ChromaDB."""
    if not isinstance(question, str) or not question.strip():
        raise ValueError("question deve ser uma string nao vazia")
    if not isinstance(n_results, int) or n_results <= 0:
        raise ValueError("n_results deve ser um inteiro maior que zero")

    work_dir = base_dir or Path(__file__).resolve().parent
    db_path = work_dir / "chroma_db"

    if not db_path.exists():
        raise FileNotFoundError(f"ChromaDB nao encontrado em: {db_path}")

    client = chromadb.PersistentClient(path=str(db_path))
    collection = client.get_collection(name=COLLECTION_NAME)

    model = SentenceTransformer(EMBEDDING_MODEL_NAME)
    query_embedding = model.encode([question.strip()], normalize_embeddings=True).tolist()

    raw = collection.query(
        query_embeddings=query_embedding,
        n_results=n_results,
        include=["documents", "metadatas", "distances"],
    )

    ids = raw.get("ids", [[]])[0]
    docs = raw.get("documents", [[]])[0]
    metas = raw.get("metadatas", [[]])[0]
    distances = raw.get("distances", [[]])[0]

    results: list[SearchResult] = []
    for chunk_id, text, metadata, distance in zip(ids, docs, metas, distances):
        similarity = max(0.0, min(1.0, 1.0 - float(distance)))
        results.append(
            SearchResult(
                chunk_id=chunk_id,
                text=text,
                metadata=metadata or {},
                distance=float(distance),
                similarity_score=similarity,
            )
        )

    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="Busca semantica no ChromaDB")
    parser.add_argument("question", type=str, help="Pergunta para busca")
    parser.add_argument("-n", "--n-results", type=int, default=5, help="Top N chunks")
    parser.add_argument(
        "--build-prompt",
        action="store_true",
        help="Monta o prompt completo com os chunks recuperados",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Arquivo de saida para salvar o prompt montado",
    )
    args = parser.parse_args()

    matches = search_similar_chunks(args.question, n_results=args.n_results)

    if args.build_prompt:
        full_prompt = build_prompt(args.question, matches)
        if args.output:
            output_path = Path(args.output)
            output_path.write_text(full_prompt, encoding="utf-8")
            print(f"Prompt salvo em: {output_path}")
        else:
            print(full_prompt)
        return

    print(f"Pergunta: {args.question}")
    print(f"Resultados: {len(matches)}")
    print()

    for i, item in enumerate(matches, start=1):
        print(f"[{i}] score={item.similarity_score:.4f} distance={item.distance:.4f}")
        print(f"    fonte={item.metadata.get('source_document', 'N/A')}")
        print(f"    secao={item.metadata.get('secao', 'N/A')}")
        preview = item.text.replace("\n", " ")[:220]
        print(f"    trecho={preview}...")
        print()


if __name__ == "__main__":
    main()
