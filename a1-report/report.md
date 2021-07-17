# Assignment 1 report - Olgierd Kasprowicz

## SBB completion

Working commit hash: `94a4f22bff3cfd7395fc15eddf8f043690d8b9e7`

![](./start.png)
![](./more-blocks.png)

## Blocktime calculations

Working commit hash: `6a94bb55619b9b0048b0971c2815abf2198af93d`

I had to make some tweaks in order to automate the testing -> see `run-timing-test`

The target is average block time of 10 seconds for 20 blocks, so 200s for total.
There is 0.5% error margin because of the measuring interval (I'm sampling the blocks every 1 second, because otherwise most of the CPU is tied in the busy-loop)

### Results

| #zeros |   time   | Δtarget |
|:------:|:--------:|:-------:|
|    2   |   2.5s   |  ~197s  |
|    3   |  9.505s  |  ~190s  |
|    4   |  87.612s |  ~112s  |
|    5   | 1653.36s |  ~1453s |

### Conclusion

Since the target_delta function has two intervals, one monotoincially decreasing and the other monotoincially increasing I conclude that no further tests are required, global minimum was found and the final parameters are:
- 4 zeros 
- 4381ms per block on average

## Well-defined binary encoding

The binary encoding differes from "JSON" encoding only by how the payload is coded. For non-parametrizable messges the digests would be identical in both encodings.

All different encodings will be defined as their respective payloads, since it's the only thing that differs
```
<payload> = ?
```

Whenever length / count is mentioned it's part of the protocol to have at least as many elements of said length as the declared by the message for a message to be valid. *Example: flopnax_count = 2; it's expected that the message contains at least 2 flopnaxes, ideally exactly 2 flopnaxes. Whatever the flopnax might be.*

### Parametrized messages

#### Count

```
<payload> ::=  <count> 
<count>   ::=  network-endian 4 byte unsigned integer
```

Example payload:
```
GetCount(count=8)
32 00 05 63 00 00 00 08 33
```

Payload breakdown
*note: I'll only do this once, since it's very much the same as during what was used for SBB*
```
32 -> initial
00 05 -> payload length
63 -> command code
00 00 00 08 -> <payload> = <count> = number 8 in this case
33 -> terminal
```

#### BlockHashes

```
<payload> ::=  <length> <hashes>
<hashes>  ::=  "" | <_hashes>
<_hashes> ::=  <hash> | <hash> <_hashes>
<length>  ::=  network-endian 4 byte unsigned integer
<hash>    ::=  32 bytes of sha256 digest
```

Example payloads
```
BlockHashes(hashes=[])
32 00 05 68 00 00 00 00 33

BlockHashes(hashes=['bcb8d59b37c026d55c6eddc81058c5465036cf14d9630ce7ffbbac14cbff21fc'])
32 00 25 68 00 00 00 01 bc b8 d5 9b 37 c0 26 d5 5c 6e dd c8 10 58 c5 46 50 36 cf 14 d9 63 0c e7 ff bb ac 14 cb ff 21 fc 33
```

#### BlockHashes

```
<payload> ::=  <hash>
<hash>    ::=  32 bytes of sha256 digest
```

Example payloads
```
ReqBlock(hash='bcb8d59b37c026d55c6eddc81058c5465036cf14d9630ce7ffbbac14cbff21fc')
32 00 21 72 bc b8 d5 9b 37 c0 26 d5 5c 6e dd c8 10 58 c5 46 50 36 cf 14 d9 63 0c e7 ff bb ac 14 cb ff 21 fc 33
```

#### ExistingBlock / NewBlock

Those two are groupeed together, since they only differ by the command code and both have complex encoding

```
<payload>          ::=  <hash> <prev_hash> <nonce> <timestamp> <trancation_count> <transactions>
<transactions>     ::=  <trn> | <trn> <transactions>
<trn>              ::=  <to_ac> <from_ac>
<to_ac>            ::=  64 bytes of receipient public key
<from_ac>          ::=  64 bytes of sender public key
<hash>             ::=  32 bytes of sha256 digest
<prev_hash>        ::=  32 bytes of sha256 digest
<nonce>            ::=  network-endian 4 byte unsigned integer
<timestamp>        ::=  network-endian 4 byte unsigned integer
<trancation_count> ::=  network-endian 4 byte unsigned integer
```

Example payloads
```
ExistingBlock(block=Block(hash='bcb8d59b37c026d55c6eddc81058c5465036cf14d9630ce7ffbbac14cbff21fc', hashedContent=HashedContent(nonce=1, prev_hash='bcb8d59b37c026d55c6eddc81058c5465036cf14d9630ce7ffbbac14cbff21fc', timestamp=1, transactions=[Transaction(from_ac='0977846f7b582cf027519210e7c4d182af92780204ff1d827fdc6557b14ff231fab77a2f90889b4d832febc2f2de270d08a14b772f3c002283e0d573e643c247', to_ac='0977846f7b582cf027519210e7c4d182af92780204ff1d827fdc6557b14ff231fab77a2f90889b4d832febc2f2de270d08a14b772f3c002283e0d573e643c247')])))
32 00 cd 78 bc b8 d5 9b 37 c0 26 d5 5c 6e dd c8 10 58 c5 46 50 36 cf 14 d9 63 0c e7 ff bb ac 14 cb ff 21 fc bc b8 d5 9b 37 c0 26 d5 5c 6e dd c8 10 58 c5 46 50 36 cf 14 d9 63 0c e7 ff bb ac 14 cb ff 21 fc 00 00 00 01 00 00 00 01 00 00 00 01 09 77 84 6f 7b 58 2c f0 27 51 92 10 e7 c4 d1 82 af 92 78 02 04 ff 1d 82 7f dc 65 57 b1 4f f2 31 fa b7 7a 2f 90 88 9b 4d 83 2f eb c2 f2 de 27 0d 08 a1 4b 77 2f 3c 00 22 83 e0 d5 73 e6 43 c2 47 09 77 84 6f 7b 58 2c f0 27 51 92 10 e7 c4 d1 82 af 92 78 02 04 ff 1d 82 7f dc 65 57 b1 4f f2 31 fa b7 7a 2f 90 88 9b 4d 83 2f eb c2 f2 de 27 0d 08 a1 4b 77 2f 3c 00 22 83 e0 d5 73 e6 43 c2 47 33

NewBlock(block=Block(hash='bcb8d59b37c026d55c6eddc81058c5465036cf14d9630ce7ffbbac14cbff21fc', hashedContent=HashedContent(nonce=1, prev_hash='bcb8d59b37c026d55c6eddc81058c5465036cf14d9630ce7ffbbac14cbff21fc', timestamp=1, transactions=[Transaction(from_ac='0977846f7b582cf027519210e7c4d182af92780204ff1d827fdc6557b14ff231fab77a2f90889b4d832febc2f2de270d08a14b772f3c002283e0d573e643c247', to_ac='0977846f7b582cf027519210e7c4d182af92780204ff1d827fdc6557b14ff231fab77a2f90889b4d832febc2f2de270d08a14b772f3c002283e0d573e643c247'), Transaction(from_ac='0977846f7b582cf027519210e7c4d182afe2780204ff1d827fdc6557b14ff231fab77a2f90889b4d832febc2f2de270d08a14b772f3c002283e0d573e643c247', to_ac='0977846f7b582cf027519210e7c4d182af92780204ff1d827fdc6557b14ff231fab77a2f90889b4d832febc2f2de270d08a14b772f3c002283e0d573e643e247')])))
32 01 4d 7a bc b8 d5 9b 37 c0 26 d5 5c 6e dd c8 10 58 c5 46 50 36 cf 14 d9 63 0c e7 ff bb ac 14 cb ff 21 fc bc b8 d5 9b 37 c0 26 d5 5c 6e dd c8 10 58 c5 46 50 36 cf 14 d9 63 0c e7 ff bb ac 14 cb ff 21 fc 00 00 00 01 00 00 00 01 00 00 00 02 09 77 84 6f 7b 58 2c f0 27 51 92 10 e7 c4 d1 82 af 92 78 02 04 ff 1d 82 7f dc 65 57 b1 4f f2 31 fa b7 7a 2f 90 88 9b 4d 83 2f eb c2 f2 de 27 0d 08 a1 4b 77 2f 3c 00 22 83 e0 d5 73 e6 43 c2 47 09 77 84 6f 7b 58 2c f0 27 51 92 10 e7 c4 d1 82 af 92 78 02 04 ff 1d 82 7f dc 65 57 b1 4f f2 31 fa b7 7a 2f 90 88 9b 4d 83 2f eb c2 f2 de 27 0d 08 a1 4b 77 2f 3c 00 22 83 e0 d5 73 e6 43 c2 47 09 77 84 6f 7b 58 2c f0 27 51 92 10 e7 c4 d1 82 af e2 78 02 04 ff 1d 82 7f dc 65 57 b1 4f f2 31 fa b7 7a 2f 90 88 9b 4d 83 2f eb c2 f2 de 27 0d 08 a1 4b 77 2f 3c 00 22 83 e0 d5 73 e6 43 c2 47 09 77 84 6f 7b 58 2c f0 27 51 92 10 e7 c4 d1 82 af 92 78 02 04 ff 1d 82 7f dc 65 57 b1 4f f2 31 fa b7 7a 2f 90 88 9b 4d 83 2f eb c2 f2 de 27 0d 08 a1 4b 77 2f 3c 00 22 83 e0 d5 73 e6 43 e2 47 33
```
