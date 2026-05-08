from p2s_core.models import PaperChunk
from p2s_core.services.claim_extraction import select_chunks_for_claim_extraction


def chunk(chunk_id, section_type, tokens):
    return PaperChunk(
        chunk_id=chunk_id,
        section_id=chunk_id.replace("chunk", "section"),
        section_type=section_type,
        text="x " * tokens,
        token_estimate=tokens,
    )


def test_select_chunks_prioritizes_core_paper_sections_under_budget():
    chunks = [
        chunk("chunk_009", "unknown", 100),
        chunk("chunk_003", "method", 100),
        chunk("chunk_001", "abstract", 100),
        chunk("chunk_004", "result", 100),
        chunk("chunk_002", "introduction", 100),
    ]

    selected = select_chunks_for_claim_extraction(chunks, max_source_tokens=300)

    assert [item.chunk_id for item in selected] == ["chunk_001", "chunk_002", "chunk_003"]


def test_select_chunks_keeps_at_least_one_chunk():
    selected = select_chunks_for_claim_extraction([chunk("chunk_001", "unknown", 1000)], max_source_tokens=10)

    assert [item.chunk_id for item in selected] == ["chunk_001"]
