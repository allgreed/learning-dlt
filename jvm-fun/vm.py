from typing import Sequence
from enum import Enum, auto


class Instruction(Enum):
    OUTPUT_X = auto()
    INPUT_X = auto()
    INC_X = auto()


class VM:
    def __init__(self, cwi=None, cri=None):
        self.x = 123
        self.console_write_int = cwi or _console_write_int
        self.console_read_int = cri or _console_read_int

    def exec_OUTPUT_X(self) -> None:
        self.console_write_int(self.x)

    def exec_INPUT_X(self) -> None:
        self.x = self.console_read_int()

    def exec_INC_X(self) -> None:
        self.x += 1

    def execute(self, instruction: Instruction) -> None:
        decode_table = {
            Instruction.OUTPUT_X: self.exec_OUTPUT_X,
            Instruction.INPUT_X: self.exec_INPUT_X,
            Instruction.INC_X: self.exec_INC_X,
        }

        try:
            f = decode_table[instruction]
        except KeyError:
            raise ValueError(f"Unsupported instruction {i}")

        f()

    def run(self, programme: Sequence[Instruction]) -> None:
        for instruction in programme:
            self.execute(instruction)


def _console_read_int() -> int:
    while True:
        try:
            return int(input())
        except ValueError:
            pass


def _console_write_int(x) -> None:
    print(x)
