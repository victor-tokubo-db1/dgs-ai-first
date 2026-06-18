from __future__ import annotations

from dataclasses import asdict, is_dataclass
from typing import Any


DEFAULT_SYSTEM_PROMPT = """Voce e um assistente de atendimento da NovaTech.
Regras obrigatorias:
1) Responda apenas com base nos chunks fornecidos.
2) Sempre cite fonte e secao usadas.
3) Nunca invente prazos, valores ou politicas.
4) Se nao houver informacao suficiente, diga explicitamente e recomende escalar para supervisor.
5) Em caso de conflito entre fontes, informe o conflito e priorize documentos normativos/contratuais.
Formato: resposta objetiva e citacoes de fonte.
"""


def _get_value(chunk: Any, key: str, default: Any = None) -> Any:
    """Extrai atributo/chave de chunk em formato dataclass ou dict."""
    if isinstance(chunk, dict):
        return chunk.get(key, default)

    if is_dataclass(chunk):
        data = asdict(chunk)
        return data.get(key, default)

    return getattr(chunk, key, default)


def build_prompt(
    question: str,
    retrieved_chunks: list[Any],
    system_prompt: str | None = None,
) -> str:
    """Monta prompt completo (system prompt + chunks + pergunta)."""
    if not isinstance(question, str) or not question.strip():
        raise ValueError("question deve ser uma string nao vazia")
    if not isinstance(retrieved_chunks, list):
        raise ValueError("retrieved_chunks deve ser uma lista")

    header = system_prompt or DEFAULT_SYSTEM_PROMPT

    if not retrieved_chunks:
        context_block = "[CONTEXTO] Nenhum chunk recuperado."
    else:
        lines: list[str] = []
        for idx, chunk in enumerate(retrieved_chunks, start=1):
            metadata = _get_value(chunk, "metadata", {}) or {}
            source = metadata.get("source_document", "N/A")
            section = metadata.get("secao", "N/A")
            score = float(_get_value(chunk, "similarity_score", 0.0))
            chunk_id = _get_value(chunk, "chunk_id", "N/A")
            text = str(_get_value(chunk, "text", "")).strip()

            lines.append(f"[CHUNK {idx}]")
            lines.append(f"Fonte: {source}")
            lines.append(f"Secao: {section}")
            lines.append(f"Score: {score:.4f}")
            lines.append(f"ChunkID: {chunk_id}")
            lines.append("Conteudo:")
            lines.append(text)
            lines.append("")
        context_block = "\n".join(lines).strip()

    return (
        f"{header}\n\n"
        "=== CONTEXTO RECUPERADO ===\n"
        f"{context_block}\n"
        "=== FIM DO CONTEXTO ===\n\n"
        "Pergunta do atendente:\n"
        f"{question.strip()}\n\n"
        "Responda agora, citando as fontes usadas."
    )
