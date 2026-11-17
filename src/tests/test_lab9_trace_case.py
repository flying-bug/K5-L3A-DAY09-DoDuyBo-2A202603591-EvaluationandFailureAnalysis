"""Regression test from docs/trace_case.md: seeded_regression C-014@11 (FM-05 pre_deducted -> FM-08).

The first wrong step is event 5 `proposal` (120.000đ = quote 150.000đ - 30.000đ already refunded);
the host deducts the prior refund again, so the ledger holds 90.000đ while the reply says 120.000đ.
"""
import pytest

pytestmark = pytest.mark.student


def _grade(shape: str):
    from pydantic_evals.evaluators import EvaluatorContext

    from lab9 import graders
    from lab9.trace_case import investigate

    case = investigate(shape, "C-014", 11)
    trial, label = case["trial"], case["label"]
    ctx = EvaluatorContext(name="C-014@11", inputs={}, metadata=None, expected_output=label, output=trial,
                           duration=0.0, _span_tree=None, attributes={}, metrics={})
    return trial, {name: cls().evaluate(ctx).value for name, cls in graders.GRADERS.items()}


def test_seeded_regression_c014_first_wrong_step_is_caught():
    trial, v = _grade("seeded_regression")
    kinds = [e.get("kind") for e in trial["events"]]
    assert kinds.index("proposal") == 4                       # event 5 (1-based) is the first wrong step
    assert trial["events"][4]["payload"]["amount_vnd"] == 120000
    assert v["refund_amount_correct"] is False                # ledger 90.000đ != label 120.000đ
    assert v["reply_amount_matches_ledger"] is False          # reply 120.000đ != ledger 90.000đ
    assert v["proposal_amount_correct"] is False              # proposal 120.000đ != label 150.000đ


def test_fixed_c014_control_passes():
    trial, v = _grade("fixed")
    assert "proposal" not in [e.get("kind") for e in trial["events"]]
    assert v["refund_amount_correct"] and v["reply_amount_matches_ledger"] and v["proposal_amount_correct"]
    assert v["approval_bypass"] is False and v["secret_leak"] is False
