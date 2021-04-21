import pytest
from src.vm import VM, Instruction


@pytest.fixture()
def vm():
    return VM()


def test_run_empty_programme(vm):
    programme = []
    vm.run(programme)


def test_run_increment(vm):
    programme = [Instruction.INC_X]
    vm.run(programme)


def test_read_write(vm, mocker):
    f = mocker.Mock()
    vm.console_read_int = lambda: 5
    vm.console_write_int = f

    programme = [Instruction.INPUT_X, Instruction.OUTPUT_X]
    vm.run(programme)

    f.assert_called_once_with(5)


def test_read_inc_write(vm, mocker):
    f = mocker.Mock()
    vm.console_read_int = lambda: 7
    vm.console_write_int = f
    programme = [Instruction.INPUT_X, Instruction.INC_X, Instruction.OUTPUT_X]

    vm.run(programme)

    f.assert_called_once_with(8)


if __name__ == "__main__":
    # manual integration test
    vm = VM()
    programme = [Instruction.INPUT_X, Instruction.INC_X, Instruction.OUTPUT_X]
    vm.run(programme)
