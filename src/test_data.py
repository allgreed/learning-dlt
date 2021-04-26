import pytest
import functools
from src.data import *

@pytest.fixture
def quick_mine():
    return functools.partial(Block._mine, is_nonce_found_fn=lambda n: True)
    
def test_mine_empty_genesis(quick_mine):
    bi = BlockIntent.genesis(transactions=[])
    genesis_block = Block.mine_from_intent(bi, mine_fn=quick_mine)
    assert genesis_block.previous_block_hash == bi.previous_block_hash


def test_intent_has_mutable_transaction_but_not_block():
    bi = BlockIntent.genesis(transactions=[])
    block = Block(nonce=5, previous_block_hash="aaa", transactions=[], timestamp=1, hash="a") 
    t = Transaction()

    bi.transactions.append(t)
    assert type(block.transactions) == tuple


def test_genesis_is_genesis(quick_mine):
    bi = BlockIntent.genesis(transactions=[])
    genesis_block = Block.mine_from_intent(bi, mine_fn=quick_mine)
    nbi = BlockIntent.next(genesis_block, transactions=[])

    next_block = Block.mine_from_intent(nbi, mine_fn=quick_mine)

    assert genesis_block.is_genesis
    assert not next_block.is_genesis


def test_difficulty():
    assert Block._is_passed_difficulty("0000dfjlskfjsldkfjslkj")


# def test_incoming_unapproved_transfers_dont_affect_balance():
    # s = State()
    # t = TransferRequiringApproval(123, 456, "ab", "cd")

    # assert s.incorporate(t)

    # assert s.balance("cd") == 0
