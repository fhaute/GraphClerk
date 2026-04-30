from __future__ import annotations

from app.services.query_intent_service import QueryIntentService


def test_query_intent_explain_patterns() -> None:
    svc = QueryIntentService()
    assert svc.classify("What is a graph?").intent.intent_type == "explain"
    assert svc.classify("How does retrieval work?").intent.intent_type == "explain"


def test_query_intent_compare_locate_summarize_debug_recommend() -> None:
    svc = QueryIntentService()
    assert svc.classify("Compare A vs B").intent.intent_type == "compare"
    assert svc.classify("Where is the config file?").intent.intent_type == "locate"
    assert svc.classify("Summarize the document").intent.intent_type == "summarize"
    assert svc.classify("Why does this fail?").intent.intent_type == "debug"
    assert svc.classify("Should I use Postgres?").intent.intent_type == "recommend"


def test_query_intent_unknown_and_empty() -> None:
    svc = QueryIntentService()
    long_generic = "word " * 30
    assert svc.classify(long_generic).intent.intent_type == "unknown"
    assert svc.classify("   ").intent.intent_type == "unknown"
