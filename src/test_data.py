import pytest
import functools
from src.data import *

@pytest.fixture
def quick_mine():
    return functools.partial(Block._mine, is_nonce_found_fn=lambda n: True)
    
def test_mine_empty_genesis(quick_mine):
    bi = BlockIntent.genesis(transactions=[])
    genesis = Block.mine_from_intent(bi, mine_fn=quick_mine)


# def test_incoming_unapproved_transfers_dont_affect_balance():
    # s = State()
    # t = TransferRequiringApproval(123, 456, "ab", "cd")

    # assert s.incorporate(t)

    # assert s.balance("cd") == 0
