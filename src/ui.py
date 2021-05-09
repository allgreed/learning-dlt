import asyncio
from concurrent.futures import ThreadPoolExecutor


class UserInterfaceIOC:
    def __init__(self, you, quarry):
        self.you = you
        self.quarry = quarry

    def alias_account(self, acc):
        trimmed = acc[:8]
        table = {
            self.you: "#you",
            self.quarry: "*quarry",
        }
        return table.get(trimmed, trimmed)

    async def execute(self):
        action = await ainput("Choose one of: [t]ransaction, [h]istory, [l]edger, [b]alance and hit enter\n")
        if action.startswith("t"):
            receipient = await ainput("Type username [and hit enter]: ")

            try:
                self.transfer(receipient)
            except ValueError as e:
                print(e) 

        elif action.startswith("h"):
            total, history = self.history()
            print("=" * 37)
            for i, entry in enumerate(history):
                _from = self.alias_account(entry.from_account)
                _to = self.alias_account(entry.to_account)

                print(f"{total - i - 1:>4} : {_from:<8} -> {_to:<8} :: 1 SBB")
            print("=" * 37)

        elif action.startswith("l"):
            print("= {0:^7} =  | = {1:^7} =".format("ACCOUNT", "BALANCE"))
            for account, balance in self.ledger().items():
                account = self.alias_account(account)
                print("{0:>12} | {1:>10}".format(account[:8], f"{balance} SBB"))
            print("==========================")

        elif action.startswith("b"):
            balance = self.balance()
            print(f"{balance} SBB")

        elif action.startswith("q"):
            self.flip_detailed_logging()

        elif action.startswith("s"):
            self.network_sync()

        else:
            pass


async def ainput(prompt: str = ''):
    """https://gist.github.com/delivrance/675a4295ce7dc70f0ce0b164fcdbd798"""
    with ThreadPoolExecutor(1, 'ainput') as executor:
        return (await asyncio.get_event_loop().run_in_executor(executor, input, prompt)).rstrip()
