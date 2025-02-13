# Spell "SPELL" on the Tiny Tapeout demo board's 7-segment display
#
# Uses the Tiny Tapeout MicroPython SDK: https://github.com/TinyTapeout/tt-micropython-firmware/
# Author: Uri Shaked

from ttboard.demoboard import DemoBoard
from ttboard.mode import RPMode
import ttboard.cocotb.dut


REG_PC = 0
REG_SP = 1
REG_EXEC = 2
REG_STACK_TOP = 3


class SpellController(ttboard.cocotb.dut.DUT):
    def __init__(self, tt: DemoBoard):
        super().__init__("Spell")
        self.tt = tt
        self.i_run = self.new_bit_attribute("i_run", tt.ui_in, 0)
        self.i_step = self.new_bit_attribute("i_step", tt.ui_in, 1)
        self.i_load = self.new_bit_attribute("i_load", tt.ui_in, 2)
        self.i_dump = self.new_bit_attribute("i_dump", tt.ui_in, 3)
        self.i_shift_in = self.new_bit_attribute("i_shift_in", tt.ui_in, 4)
        self.i_reg_sel = self.new_slice_attribute("i_reg_sel", tt.ui_in, 6, 5)

        self.o_cpu_sleep = self.new_bit_attribute("o_cpu_sleep", tt.uo_out, 0)
        self.o_cpu_stop = self.new_bit_attribute("o_cpu_stop", tt.uo_out, 1)
        self.o_wait_delay = self.new_bit_attribute("o_wait_delay", tt.uo_out, 2)
        self.o_shift_out = self.new_bit_attribute("o_shift_out", tt.uo_out, 3)

        self.i_run.value = 0
        self.i_step.value = 0
        self.i_load.value = 0
        self.i_dump.value = 0
        self.i_shift_in.value = 0
        self.i_reg_sel.value = 0

    def ensure_cpu_stopped(self):
        while int(self.o_cpu_stop) == 0:
            self.tt.clock_project_once()

    def stopped(self):
        return int(self.o_cpu_stop) == 0

    def sleeping(self):
        return int(self.o_cpu_stop) == 1

    def write_reg(self, reg: int, value: int):
        for i in range(8):
            self.i_shift_in.value = (value >> (7 - i)) & 1
            self.tt.clock_project_once()
        self.i_reg_sel.value = reg
        self.i_load.value = 1
        self.tt.clock_project_once()
        self.i_load.value = 0
        self.tt.clock_project_once()

    def read_reg(self, reg: int):
        self.i_reg_sel.value = reg
        self.i_dump.value = 1
        self.tt.clock_project_once()
        self.i_dump.value = 0
        value = 0
        for i in range(8):
            self.tt.clock_project_once()
            value |= int(self.o_shift_out) << (7 - i)
        return value

    def execute(self, wait=True):
        self.ensure_cpu_stopped()
        self.i_run.value = 1
        self.i_step.value = 0
        self.tt.clock_project_once()
        self.i_run.value = 0
        self.tt.clock_project_once()
        if wait:
            self.ensure_cpu_stopped()

    def single_step(self):
        self.ensure_cpu_stopped()
        self.i_run.value = 1
        self.i_step.value = 1
        self.tt.clock_project_once()
        self.i_step.value = 0
        self.i_run.value = 0
        self.tt.clock_project_once()
        self.ensure_cpu_stopped()

    def exec_opcode(self, opcode):
        int_opcode = ord(opcode) if type(opcode) == str else int(opcode)
        self.ensure_cpu_stopped()
        self.write_reg(REG_EXEC, int_opcode)
        self.ensure_cpu_stopped()

    def read_stack_top(self):
        return self.read_reg(REG_STACK_TOP)

    def push(self, value: int):
        self.ensure_cpu_stopped()
        self.write_reg(REG_STACK_TOP, value)

    def read_pc(self):
        return self.read_reg(REG_PC)

    def set_pc(self, value: int):
        self.write_reg(REG_PC, value)

    def read_sp(self):
        return self.read_reg(REG_SP)

    def set_sp(self, value: int):
        self.write_reg(REG_SP, value)

    def set_sp_read_stack(self, index: int):
        self.set_sp(index)
        return self.read_stack_top()

    def write_progmem(self, addr: int, value: Union[int, str]):
        """
        Writes a value to progmem by executing an instruction on the CPU.
        """
        int_value = ord(value) if type(value) == str else int(value)
        self.push(int_value)
        self.push(addr)
        self.exec_opcode("!")

    def write_program(self, opcodes, offset=0):
        for index, opcode in enumerate(opcodes):
            self.write_progmem(offset + index, opcode)


def run():
    global spell
    tt = DemoBoard.get()
    tt.mode = RPMode.ASIC_RP_CONTROL
    tt.shuttle.tt_um_urish_spell.enable()
    spell = SpellController(tt)
    tt.reset_project(True)
    tt.clock_project_once()
    tt.reset_project(False)
    # Find the source code for the test program in spell-spell.spl
    # fmt: off
    test_program = [
       127, 58, 119, 0, 129, 57, 57, 244, 62, 116, 109, 
       59, 119, 250, 44, 0, 59, 119, 25, 44, 11, 64, 3, 61
    ]
    # fmt: on
    spell.write_program(test_program)
    print("Start")
    spell.execute(False)
    tt.clock_project_PWM(10_000_000)  # 10 MHz


run()
