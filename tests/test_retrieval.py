from tooling_showcase.retrieval import build_chunks, query_chunks


def test_query_chunks_prefers_matching_chunk():
    chunks = build_chunks(
        {
            "a.txt": "router handles deterministic tool selection\nsecond line",
            "b.txt": "audio pipeline and wake word handling\nsecond line",
        },
        max_lines_per_chunk=2,
    )
    selected = query_chunks(chunks, "deterministic router tool")
    assert selected
    assert selected[0].label == "a.txt"
