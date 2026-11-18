"""Bonus: the Inspect AI scorers agree with lab9.graders row by row.
Skipped when inspect_ai is not installed (pip install -r bonus/requirements-bonus.txt)."""
import pytest

pytest.importorskip("inspect_ai")


@pytest.fixture
def clean_shapes():
    """inspect_port registers the lab9 variants and only_<bug> shapes in the global SHAPES registry;
    put it back so later tests still see only the four Lab 8 shapes."""
    from lab8.shapes import SHAPES

    before = dict(SHAPES)
    yield
    SHAPES.clear()
    SHAPES.update(before)


def test_inspect_scorers_match_lab9_on_both_verdicts(clean_shapes):
    from bonus import inspect_port

    # `fixed` gives the all-pass verdicts; each single bug flips one scorer to the failing verdict
    # (leaky_trace -> secret_leak, sibling_refund -> approval_bypass, misreport -> reply amount).
    rc = inspect_port.main(["--shapes", "fixed", "--single-bugs", "leaky_trace,sibling_refund,misreport"])
    assert rc == 0
