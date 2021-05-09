import pytest
import functools
import dataclasses

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
    block = Block(nonce=5, previous_block_hash="bcb8d59b37c026d55c6eddc81058c5465036cf14d9630ce7ffbbac14cbff21fc", transactions=[], timestamp=1, hash="bcb8d59b37c026d55c6eddc81058c5465036cf14d9630ce7ffbbac14cbff21fc") 
    t = Transaction()

    bi.transactions.append(t)
    assert type(block.transactions) == tuple


def test_genesis_is_genesis(quick_mine):
    bi = BlockIntent.genesis(transactions=[])
    genesis_block = Block.mine_from_intent(bi, mine_fn=quick_mine)
    nbi = BlockIntent.next(genesis_block, transactions=[])
    nbi = BlockIntent.next(genesis_block, transactions=[])

    next_block = Block.mine_from_intent(nbi, mine_fn=quick_mine)

    assert genesis_block.is_genesis
    assert not next_block.is_genesis


def test_difficulty():
    assert Block._is_passed_difficulty("0000dfjlskfjsldkfjslkj")


def test_length():
    c = Chain()
    b = Block(nonce=5, previous_block_hash="bcb8d59b37c026d55c6eddc81058c5465036cf14d9630ce7ffbbac14cbff21fc", transactions=[], timestamp=1, hash="bcb8d59b37c026d55c6eddc81058c5465036cf14d9630ce7ffbbac14cbff21fc")

    assert len(c) == 0

    c.try_incorporate(b)
    assert len(c) == 1

    c.try_incorporate(dataclasses.replace(b, hash="bcb8d59b37c026d55c6eddc81058c5465036cf14d9630ce7ffbbac14cbaaa1aa"))
    assert len(c) == 2


def test_gc_chain_len_1_doesnt_empty_chain():
    c = Chain()
    b = Block(nonce=5, previous_block_hash="0", transactions=[], timestamp=1, hash="bcb8d59b37c026d55c6eddc81058c5465036cf14d9630ce7ffbbac14cbff21fc")
    c.try_incorporate(b)

    c._gc()

    assert len(c) == 1
    assert c.latest_block


def test_gc_doesnt_remove_required_items():
    c = Chain()
    b0 = Block(nonce=5, previous_block_hash="0", transactions=[], timestamp=1, hash="bcb8d59b37c026d55c6eddc81058c5465036cf14d9630ce7ffbbac14cbff21fc")
    b1 = Block(nonce=5, previous_block_hash="bcb8d59b37c026d55c6eddc81058c5465036cf14d9630ce7ffbbac14cbff21fc", transactions=[], timestamp=1, hash="aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa")
    c.try_incorporate(b0)
    c.try_incorporate(b1)

    c._gc()

    assert len(c) == 2
