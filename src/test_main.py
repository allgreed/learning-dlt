from src.proto import Block
from src.main import pack_block, unpack_block


def test_pack_unpack():
    b = Block(hash="bcb8d59b37c026d55c6eddc81058c5465036cf14d9630ce7ffbbac14cbff21fc", hashedContent={"nonce": 1, "prev_hash": "bcb8d59b37c026d55c6eddc81058c5465036cf14d9630ce7ffbbac14cbff21fc", "timestamp": 1, "transactions": [{"from_ac": "0977846f7b582cf027519210e7c4d182af92780204ff1d827fdc6557b14ff231fab77a2f90889b4d832febc2f2de270d08a14b772f3c002283e0d573e643c247", "to_ac": "0977846f7b582cf027519210e7c4d182af92780204ff1d827fdc6557b14ff231fab77a2f90889b4d832febc2f2de270d08a14b772f3c002283e0d573e643c247"}]})

    unpacked = unpack_block(b)
    assert b == pack_block(unpacked)
