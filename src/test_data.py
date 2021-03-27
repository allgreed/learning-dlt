from src.data import *


def test_unapproved_transactions_dont_affect_balance():
    s = State()
    ledger_reference = s.ledger
    t = TransactionRequiringApproval(123, "ab", "cd", 456)

    assert s.incorporate(t)

    assert s.ledger == ledger_reference


def test_approved_transactions_are_the_same_as_ordinary_transactions():
    s, s_reference = State(), State()
    t_reference = Transaction(123, "ab", "cd", timestamp=456)

    t0 = TransactionRequiringApproval(123, "ab", "cd", timestamp=456)
    t1 = TransactionApproval(789, approved_trn=123, timestamp=457)

    assert s_reference.incorporate(t_reference)
    assert s.incorporate(t0)
    assert s.incorporate(t1)

    assert s_reference.ledger == s.ledger
