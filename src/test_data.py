from src.data import *

    
def test_incoming_unapproved_transfers_dont_affect_balance():
    s = State()
    t = TransferRequiringApproval(123, 456, "ab", "cd")

    assert s.incorporate(t)

    assert s.balance("cd") == 0


def test_outgoing_unapproved_transfers_affect_balance():
    s = State()
    t = TransferRequiringApproval(123, 456, "ab", "cd")

    assert s.incorporate(t)

    assert s.balance("ab") == -1


def test_approved_transfers_are_the_same_as_ordinary_transfers():
    s, s_reference = State(), State()
    t_reference = Transfer(123, 456, "ab", "cd")

    t0 = TransferRequiringApproval(123, 456, "ab", "cd")
    t1 = TransferApproval(789, approved_trn=123, approver="cd", timestamp=457)

    assert s_reference.incorporate(t_reference)
    assert s.incorporate(t0)
    assert s.incorporate(t1)

    assert s_reference.ledger == s.ledger


def test_transfer_from_intent():
    t = Transfer.from_intent(TransferIntent("ab", "cd"), 5)
    assert type(t) is Transfer


def test_transfer_from_intent_pending():
    t = Transfer.from_intent(TransferIntent("ab", "cd", pending=True), 5)
    assert type(t) is TransferRequiringApproval
