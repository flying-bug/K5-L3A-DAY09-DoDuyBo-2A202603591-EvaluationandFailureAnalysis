"""M3: FM-08 (misreport) and proposal graders on hand-built Trials (no shape run)."""
import pytest

pytestmark = pytest.mark.student
LABEL = {"refund_vnd": 20000, "proposal_amount": 35000, "approval_ok": True, "forbid_substrings": []}


@pytest.fixture(scope="module")
def graders():
    from lab9 import graders

    return graders


def ctx(trial, label=LABEL):
    from pydantic_evals.evaluators import EvaluatorContext

    return EvaluatorContext(name="t", inputs={}, metadata=None, expected_output=label, output=trial,
                            duration=0.0, _span_tree=None, attributes={}, metrics={})


def trial(reply=None, refund_vnd=20000, proposal=35000):
    events = [{"kind": "quote", "payload": {"amount_vnd": 35000}}]
    if reply is not None:
        events.append({"kind": "reply", "payload": {"text": reply}})
    return {"snapshot": {"refund_vnd": refund_vnd, "refund_count": 1 if refund_vnd else 0},
            "unexpected_rows": 0, "blob": "", "events": events,
            "result": {"proposal_amount": proposal}, "lab8_pass": True, "lab8_reason": None}


@pytest.mark.parametrize("text, amounts", [
    ("Dạ, LogiX đã hoàn 20.000đ cho đơn O-808.", [20000]),
    ("LogiX đã hoàn phí 35,000 đ cho đơn O-107 của anh/chị ạ.", [35000]),
    ("Đã hoàn 150000 VND và 5.000 đồng phí", [150000, 5000]),
    ("Dạ, đơn O-202 chưa đủ điều kiện hoàn.", []),          # order id is not money
])
def test_reply_amounts_parsing(graders, text, amounts):
    assert graders.reply_amounts(text) == amounts


def test_reply_matching_ledger_passes(graders):
    assert graders.ReplyAmountMatchesLedger().evaluate(ctx(trial("Dạ, LogiX đã hoàn 20.000đ cho đơn O-808."))).value is True


def test_reply_stating_proposal_not_ledger_is_misreport(graders):
    # C-008: quote 35.000đ, approval caps the ledger at 20.000đ -- the reply must say 20.000đ.
    res = graders.ReplyAmountMatchesLedger().evaluate(ctx(trial("Dạ, LogiX đã hoàn 35.000đ cho đơn O-808.")))
    assert res.value is False and "35000" in res.reason


def test_reply_claiming_refund_when_ledger_empty_is_misreport(graders):
    # FM-02 + FM-08: host denied, nothing in the ledger, reply still says money was refunded.
    assert graders.ReplyAmountMatchesLedger().evaluate(
        ctx(trial("Dạ, LogiX đã hoàn 35.000đ cho đơn O-909.", refund_vnd=0))).value is False


def test_no_reply_or_no_amount_cannot_misreport(graders):
    assert graders.ReplyAmountMatchesLedger().evaluate(ctx(trial(None))).value is True
    assert graders.ReplyAmountMatchesLedger().evaluate(
        ctx(trial("Dạ, đơn O-202 chưa đủ điều kiện hoàn.", refund_vnd=0))).value is True


def test_proposal_amount(graders):
    assert graders.ProposalAmountCorrect().evaluate(ctx(trial())).value is True
    # FM-05 pre_deducted to 0 (C-013): denied like the label, but the proposal is wrong.
    assert graders.ProposalAmountCorrect().evaluate(ctx(trial(proposal=0, refund_vnd=0))).value is False


def test_spec_registers_fm08_metric(graders):
    from lab9.eval import load_spec

    m = {x["id"]: x for x in load_spec()["metrics"]}["reply_amount_matches_ledger"]
    assert m["blocking"] and m["kind"] == "capability" and "reply_amount_matches_ledger" in graders.GRADERS
