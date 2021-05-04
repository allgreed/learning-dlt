from src.proto import Block
from src.main import pack_block, unpack_block


def test_pack_unpack():
    b = Block(hash="bcb8d59b37c026d55c6eddc81058c5465036cf14d9630ce7ffbbac14cbff21fc", hashedContent={"nonce": 1, "prev_hash": "bcb8d59b37c026d55c6eddc81058c5465036cf14d9630ce7ffbbac14cbff21fc", "timestamp": 1, "transactions": [{"from_ac": "aaaaa", "to_ac": "bbbbb"}]})

    unpacked = unpack_block(b)
    assert b == pack_block(unpacked)
