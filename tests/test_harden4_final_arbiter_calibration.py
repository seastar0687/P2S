from tests.test_final_arbiter import _bundle, _finding
from p2s_core.reviewers.final_arbiter import FinalArbiter


def test_harden4_arbiter_matrix():
    arbiter = FinalArbiter()
    assert arbiter.decide(_bundle([_finding("medium", False)])).status == "pass"
    assert arbiter.decide(_bundle([_finding("low", True)])).status == "human_check"
    assert arbiter.decide(_bundle([_finding("medium", True)])).status == "human_check"
    assert arbiter.decide(_bundle([_finding("high", True)])).status == "human_check"
    assert arbiter.decide(_bundle([_finding("critical", True)])).status == "reject"
    assert arbiter.decide(_bundle([], pass_gate=False)).status == "human_check"
