from agentic.core.idempotency import compute_dedup_key


def test_same_inputs_same_key():
    k1 = compute_dedup_key("DATA-042", "baac.evidently", "staging", "2026-09-30")
    k2 = compute_dedup_key("DATA-042", "baac.evidently", "staging", "2026-09-30")
    assert k1 == k2


def test_different_window_different_key():
    k1 = compute_dedup_key("DATA-042", "baac.evidently", "staging", "2026-09-30")
    k2 = compute_dedup_key("DATA-042", "baac.evidently", "staging", "2026-10-01")
    assert k1 != k2
