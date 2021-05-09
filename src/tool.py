import src.proto as Protocol
from src.coms import Net
from src.main import pack_block
from src.data import Block


host = "127.0.0.1"


def main():
    net = Net(this=(host, 1234))
    for m in [
        Protocol.GetCount(),
        Protocol.NewBlock(Protocol.Block(
            hash='34f693fa012ca131b901138afcefb469015d98b96d42b1116f30b11fa2823232', hashedContent=Protocol.HashedContent(nonce=0, prev_hash='2939c31054438090c95a0778a7872a78159144b81e0dd706a4d4ca9d820094f2', timestamp=1620583814, transactions=[Protocol.Transaction(from_ac='0', to_ac='92128270f1661bd75f833f3b6d17d873404ccd64b5b7db4af001a5196c9e1a08c9a70a97ff15a9193be8bb64b83ef9a4cd02466c06414836b7f5b10a62bd335b')])
        )),
        Protocol.GetCount(),
    ]:
        net.broadcast(m)

if __name__ == "__main__":
    main()
