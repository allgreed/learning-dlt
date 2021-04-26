import asyncio
from concurrent.futures import ThreadPoolExecutor


class UserInterfaceIOC:
    async def execute(self):
        action = await ainput("Choose one of: [t]ransaction, [h]istory, [l]edger, [b]alance and hit enter\n")
        if action.startswith("t"):
            receipient = await ainput("Type username [and hit enter]: ")

            try:
                self.transfer()
            except ValueError as e:
                print(e) 

        elif action.startswith("h"):
            print("==========================")
            for entry in self.history():
                print(entry)
            print("==========================")

        elif action.startswith("l"):
            print("= {0:^7} =  | = {1:^7} =".format("ACCOUNT", "BALANCE"))
            for account, balance in self.ledger().items():
                print("{0:>12} | {1:>10}".format(account, f"{balance} SBB"))
            print("==========================")

        elif action.startswith("b"):
            username, balance = self.balance()
            print(f"% BALANCE for {username} %")
            print(f"{balance} SBB")
            print("%%%%%%%%%%%%%%%%%%")

        else:
            pass


async def ainput(prompt: str = ''):
    """https://gist.github.com/delivrance/675a4295ce7dc70f0ce0b164fcdbd798"""
    with ThreadPoolExecutor(1, 'ainput') as executor:
        return (await asyncio.get_event_loop().run_in_executor(executor, input, prompt)).rstrip()
