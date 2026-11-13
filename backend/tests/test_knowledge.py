import pytest

from app.config import Settings
from app.rag.kb import KnowledgeBase
from app.rag.loader import parse_document


def test_documents_load(kb_lex):
    info = kb_lex.info()
    assert info["documents"] >= 15 and info["chunks"] > 30
    assert "reduce the data size" in kb_lex.always_text.lower()      # company guidance is always-on
    ids = [h["id"] for h in kb_lex.search("refresh", k=50)]
    assert len(ids) == len(set(ids))


def test_header_is_required():
    with pytest.raises(ValueError):
        parse_document("no header here")


@pytest.mark.parametrize("query,doc", [
    ("Timeout error", "refresh-timeout"),
    ("An error occurred while processing", "refresh-processing-error"),
    ("The credentials provided for the data source are invalid", "credentials-invalid-or-expired"),
    ("Gateway is offline", "gateway-offline-or-unmapped"),
    ("The key didn't match any rows in the table", "schema-change-column-not-found"),
    ("user sees all rows view as shows everything RLS not working", "rls-testing-and-troubleshooting"),
])
def test_keyword_search_finds_the_right_document(kb_lex, query, doc):
    assert kb_lex.search(query)[0]["doc_id"] == doc


def test_search_cleans_noise_from_errors(kb_lex):
    noisy = "Timeout error at 11:13:40 AM on 9/28/2026 activity 3f2504e0-4f89-11d3-9a0c-0305e82c3301"
    assert kb_lex.search(noisy)[0]["doc_id"] == "refresh-timeout"


def test_unfamiliar_text_is_not_reported_as_relevant(kb_lex):
    assert not any(h["relevant"] for h in kb_lex.search("xqzv 0x8F2A91B3 qrz"))
    assert not any(h["relevant"] for h in kb_lex.search("Error code 0x8F2A91B3 in module QRZ"))


def test_hybrid_search_with_embeddings(kb_emb, keyed):
    hits = kb_emb.search("Timeout error")
    assert hits and kb_emb.info()["retrieval"] == "embeddings"
    assert (keyed.data_dir / "embeddings.json").exists()


def test_embedding_cache_is_reused(keyed):
    calls = []

    def counting(texts):
        calls.append(len(texts))
        from conftest import fake_embed
        return fake_embed(texts)

    KnowledgeBase(keyed, embed_fn=counting).search("timeout")
    first = sum(calls)
    calls.clear()
    KnowledgeBase(keyed, embed_fn=counting).search("timeout")
    assert first > 30 and sum(calls) == 1        # second time: only the query is embedded


def test_search_falls_back_to_keywords_when_embeddings_fail(keyed):
    def broken(texts):
        raise RuntimeError("model not allowed")

    kb = KnowledgeBase(keyed, embed_fn=broken)
    assert kb.search("Timeout error")[0]["doc_id"] == "refresh-timeout"
    assert kb.info()["retrieval"] == "keyword"


def test_no_key_means_keyword_search(keyless):
    assert KnowledgeBase(keyless).info()["retrieval"] == "keyword"
