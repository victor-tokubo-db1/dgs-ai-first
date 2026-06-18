from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import chromadb
from chromadb.api.models.Collection import Collection
from sentence_transformers import SentenceTransformer


# Documentos do Anexo A disponiveis na raiz do workspace.
DOC_FILENAMES = [
    "POL-001-politica-devolucao.md",
    "PROC-042-frete-especial-v1.md",
    "PROC-042-v2-frete-especial-revisado.md",
    "SLA-2024-tabela-sla-clientes.md",
    "FAQ-atendimento.md",
]

COLLECTION_NAME = "novatech_docs"
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
MAX_WORDS_PER_CHUNK = 420
OVERLAP_WORDS = 60

HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$", re.MULTILINE)
META_LINE_RE = re.compile(r"^\*\*(.+?)\*\*:\s*(.+?)\s*$")


@dataclass
class Chunk:
    id: str
    text: str
    metadata: dict[str, Any]


def count_words(text: str) -> int:
    return len(re.findall(r"\S+", text))


def split_markdown_sections(markdown_text: str) -> list[tuple[str, str]]:
    """Divide o markdown por headings preservando hierarquia da secao."""
    matches = list(HEADING_RE.finditer(markdown_text))
    if not matches:
        body = markdown_text.strip()
        return [("documento_completo", body)] if body else []

    sections: list[tuple[str, str]] = []
    stack: list[str] = []

    for idx, match in enumerate(matches):
        level = len(match.group(1))
        title = match.group(2).strip()

        while len(stack) >= level:
            stack.pop()
        stack.append(title)

        start = match.end()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(markdown_text)
        body = markdown_text[start:end].strip()
        if body:
            sections.append((" > ".join(stack), body))

    return sections


def split_long_text(text: str, max_words: int, overlap_words: int) -> list[str]:
    words = text.split()
    if len(words) <= max_words:
        return [text.strip()]

    chunks: list[str] = []
    start = 0
    while start < len(words):
        end = min(start + max_words, len(words))
        chunks.append(" ".join(words[start:end]).strip())
        if end == len(words):
            break
        start = max(end - overlap_words, 0)

    return chunks


def extract_metadata(markdown_text: str, filename: str) -> dict[str, str]:
    metadata = {
        "source_document": filename,
        "versao": "",
        "data": "",
        "responsavel": "",
        "classificacao": "",
        "prioridade_fonte": "baixa",
    }

    if filename.startswith(("POL-", "PROC-", "SLA-")):
        metadata["prioridade_fonte"] = "alta"

    for line in markdown_text.splitlines()[:60]:
        line = line.strip()
        match = META_LINE_RE.match(line)
        if not match:
            continue

        key = match.group(1).strip().lower()
        value = match.group(2).strip()

        if "vers" in key:
            metadata["versao"] = value
        elif "atualiza" in key or "emiss" in key:
            metadata["data"] = value
        elif "respons" in key:
            metadata["responsavel"] = value
        elif "classifica" in key or "status" in key:
            metadata["classificacao"] = value

    return metadata


def generate_chunk_id(filename: str, section: str, index: int, text: str) -> str:
    base = f"{filename}|{section}|{index}|{text[:120]}"
    return hashlib.sha1(base.encode("utf-8")).hexdigest()


def build_document_chunks(doc_path: Path) -> list[Chunk]:
    markdown_text = doc_path.read_text(encoding="utf-8")
    doc_metadata = extract_metadata(markdown_text, doc_path.name)
    sections = split_markdown_sections(markdown_text)

    chunks: list[Chunk] = []
    for section_path, section_text in sections:
        section_parts = split_long_text(
            section_text,
            max_words=MAX_WORDS_PER_CHUNK,
            overlap_words=OVERLAP_WORDS,
        )

        for index, part in enumerate(section_parts):
            chunk = Chunk(
                id=generate_chunk_id(doc_path.name, section_path, index, part),
                text=part,
                metadata={
                    **doc_metadata,
                    "secao": section_path,
                    "chunk_index_secao": str(index),
                    "chunk_words": str(count_words(part)),
                    "file_path": str(doc_path),
                },
            )
            chunks.append(chunk)

    return chunks


def get_or_create_collection(db_path: Path, collection_name: str) -> Collection:
    client = chromadb.PersistentClient(path=str(db_path))
    return client.get_or_create_collection(name=collection_name, metadata={"hnsw:space": "cosine"})


def clear_collection(collection: Collection) -> None:
    existing = collection.count()
    if existing == 0:
        return

    ids = collection.get(include=[]).get("ids", [])
    if ids:
        collection.delete(ids=ids)


def ingest_documents(base_dir: Path) -> None:
    db_path = base_dir / "chroma_db"
    collection = get_or_create_collection(db_path, COLLECTION_NAME)
    clear_collection(collection)

    model = SentenceTransformer(EMBEDDING_MODEL_NAME)

    total_chunks = 0
    for filename in DOC_FILENAMES:
        doc_path = base_dir.parent / filename
        if not doc_path.exists():
            print(f"[AVISO] Documento nao encontrado: {doc_path}")
            continue

        chunks = build_document_chunks(doc_path)
        if not chunks:
            print(f"[AVISO] Nenhum chunk gerado para: {filename}")
            continue

        documents = [c.text for c in chunks]
        embeddings = model.encode(documents, normalize_embeddings=True).tolist()

        collection.add(
            ids=[c.id for c in chunks],
            documents=documents,
            metadatas=[c.metadata for c in chunks],
            embeddings=embeddings,
        )

        total_chunks += len(chunks)
        print(f"[OK] {filename}: {len(chunks)} chunks")

    print("\nIngestao finalizada")
    print(f"Colecao: {COLLECTION_NAME}")
    print(f"Total de chunks: {total_chunks}")
    print(f"Chroma path: {db_path}")


if __name__ == "__main__":
    # Arquivo esperado dentro de Exercicio03.
    # Documentos fonte estao um nivel acima (raiz do workspace).
    working_dir = Path(__file__).resolve().parent
    ingest_documents(working_dir)
