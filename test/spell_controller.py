from typing import List, Union

from cocotb.triggers import ClockCycles, RisingEdge

REG_PC = 0
REG_SP = 1
REG_EXEC = 2
REG_STACK_TOP = 3


class SpellController:
    def __init__(self, dut):
        self._dut = dut
        self._dut.i_run.value = 0
        self._dut.i_step.value = 0
        self._dut.i_load.value = 0
        self._dut.i_dump.value = 0
        self._dut.i_shift_in.value = 0
        self._dut.i_reg_sel.value = 0

    async def ensure_cpu_stopped(self):
        if self._dut.o_cpu_stop.value == 0:
            await RisingEdge(self._dut.o_cpu_stop)
    
    def stopped(self):
        return self._dut.o_cpu_stop.value == 0

    def sleeping(self):
        return self._dut.o_cpu_sleep.value == 1

    async def write_reg(self, reg: int, value: int):
        for i in range(8):
            self._dut.i_shift_in.value = (value >> (7 - i)) & 1
            await ClockCycles(self._dut.clk, 1)
        self._dut.i_reg_sel.value = reg
        self._dut.i_load.value = 1
        await ClockCycles(self._dut.clk, 1)
        self._dut.i_load.value = 0
        await ClockCycles(self._dut.clk, 1)

    async def read_reg(self, reg: int):
        self._dut.i_reg_sel.value = reg
        self._dut.i_dump.value = 1
        await ClockCycles(self._dut.clk, 1)
        self._dut.i_dump.value = 0
        await ClockCycles(self._dut.clk, 1)
        value = 0
        for i in range(8):
            await ClockCycles(self._dut.clk, 1)
            value |= self._dut.o_shift_out.value << (7 - i)
        return value

    async def execute(self, wait=True):
        await self.ensure_cpu_stopped()
        self._dut.i_run.value = 1
        self._dut.i_step.value = 0
        await ClockCycles(self._dut.clk, 1)
        self._dut.i_run.value = 0
        await ClockCycles(self._dut.clk, 1)
        if wait:
            await self.ensure_cpu_stopped()

    async def single_step(self):
        await self.ensure_cpu_stopped()
        self._dut.i_run.value = 1
        self._dut.i_step.value = 1
        await ClockCycles(self._dut.clk, 1)
        self._dut.i_step.value = 0
        self._dut.i_run.value = 0
        await ClockCycles(self._dut.clk, 1)
        await self.ensure_cpu_stopped()

    async def exec_opcode(self, opcode: Union[int, str]):
        int_opcode = ord(opcode) if type(opcode) == str else int(opcode)
        await self.ensure_cpu_stopped()
        await self.write_reg(REG_EXEC, int_opcode)
        await self.ensure_cpu_stopped()

    async def read_stack_top(self):
        return await self.read_reg(REG_STACK_TOP)

    async def push(self, value: int):
        await self.ensure_cpu_stopped()
        await self.write_reg(REG_STACK_TOP, value)

    async def read_pc(self):
        return await self.read_reg(REG_PC)

    async def set_pc(self, value: int):
        await self.write_reg(REG_PC, value)

    async def read_sp(self):
        return await self.read_reg(REG_SP)

    async def set_sp(self, value: int):
        await self.write_reg(REG_SP, value)

    async def set_sp_read_stack(self, index: int):
        await self.set_sp(index)
        return await self.read_stack_top()

    async def write_progmem(self, addr: int, value: Union[int, str]):
        """
        Writes a value to progmem by executing an instruction on the CPU.
        """
        int_value = ord(value) if type(value) == str else int(value)
        await self.push(int_value)
        await self.push(addr)
        await self.exec_opcode("!")

    async def write_program(self, opcodes: List[Union[int, str]], offset=0):
        for index, opcode in enumerate(opcodes):
            await self.write_progmem(offset + index, opcode)
