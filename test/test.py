# SPDX-FileCopyrightText: © 2023 Uri Shaked <uri@tinytapeout.com>
# SPDX-License-Identifier: MIT

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles
from spell_controller import SpellController


async def reset(dut):
    dut._log.info("Reset")
    dut.ena.value = 1
    dut.ui_in.value = 0
    dut.uio_in.value = 0
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 10)
    dut.rst_n.value = 1


@cocotb.test()
async def test_add(dut):
    spell = SpellController(dut)
    clock = Clock(dut.clk, 10, units="us")
    cocotb.start_soon(clock.start())
    await reset(dut)

    # Write a program that adds two numbers, then goes to sleep
    await spell.write_progmem(0, 42)
    await spell.write_progmem(1, 58)
    await spell.write_progmem(2, "+")
    await spell.write_progmem(3, "z")

    await spell.execute()

    assert await spell.read_pc() == 4
    assert await spell.read_sp() == 1
    assert await spell.read_stack_top() == 100  # The sum


@cocotb.test()
async def test_sub(dut):
    spell = SpellController(dut)
    clock = Clock(dut.clk, 10, units="us")
    cocotb.start_soon(clock.start())
    await reset(dut)

    await spell.write_program([66, 55, "-", "z"])
    await spell.execute()

    assert await spell.read_pc() == 4
    assert await spell.read_sp() == 1
    assert await spell.read_stack_top() == 11  # The difference


@cocotb.test()
async def test_bitwise(dut):
    spell = SpellController(dut)
    clock = Clock(dut.clk, 10, units="us")
    cocotb.start_soon(clock.start())
    await reset(dut)

    await spell.write_program(
        [0x88, 0xF0, "&", 0x88, 0xF0, "|", 0x88, 0xF0, "^", 0x88, ">", 0x88, "<", "z"]
    )
    await spell.execute()

    assert await spell.read_pc() == 14
    assert await spell.read_sp() == 5
    assert await spell.set_sp_read_stack(5) == 0x10  # 0x88 << 1
    assert await spell.set_sp_read_stack(4) == 0x44  # 0x88 >> 1
    assert await spell.set_sp_read_stack(3) == 0x78  # 0x88 ^ 0xf0
    assert await spell.set_sp_read_stack(2) == 0xF8  # 0x88 | 0xf0
    assert await spell.set_sp_read_stack(1) == 0x80  # 0x88 & 0xf0


@cocotb.test()
async def test_dup(dut):
    spell = SpellController(dut)
    clock = Clock(dut.clk, 10, units="us")
    cocotb.start_soon(clock.start())
    await reset(dut)

    await spell.write_program([12, "2", "z"])
    await spell.execute()

    assert await spell.read_pc() == 3
    assert await spell.read_sp() == 2
    assert await spell.read_stack_top() == 12

    await spell.set_sp(1)
    assert await spell.read_sp() == 1
    assert await spell.read_stack_top() == 12


@cocotb.test()
async def test_exchange(dut):
    spell = SpellController(dut)
    clock = Clock(dut.clk, 10, units="us")
    cocotb.start_soon(clock.start())
    await reset(dut)

    await spell.write_program([89, 96, "x", "z"])
    await spell.execute()

    assert await spell.read_pc() == 4
    assert await spell.read_sp() == 2
    assert await spell.read_stack_top() == 89

    await spell.set_sp(1)
    assert await spell.read_sp() == 1
    assert await spell.read_stack_top() == 96


@cocotb.test()
async def test_jmp(dut):
    spell = SpellController(dut)
    clock = Clock(dut.clk, 10, units="us")
    cocotb.start_soon(clock.start())
    await reset(dut)

    await spell.write_program([22, "="])
    await spell.single_step()
    await spell.single_step()

    assert await spell.read_pc() == 22
    assert await spell.read_sp() == 0


@cocotb.test()
async def test_loop(dut):
    spell = SpellController(dut)
    clock = Clock(dut.clk, 10, units="us")
    cocotb.start_soon(clock.start())
    await reset(dut)

    await spell.write_program([2, 1, "@"])
    await spell.single_step()
    await spell.single_step()
    await spell.single_step()

    assert await spell.read_pc() == 1
    assert await spell.read_sp() == 1
    assert await spell.read_stack_top() == 1

    await spell.single_step()
    await spell.single_step()
    assert await spell.read_pc() == 1
    assert await spell.read_sp() == 1
    assert await spell.read_stack_top() == 0

    await spell.single_step()
    await spell.single_step()
    assert await spell.read_pc() == 3
    assert await spell.read_sp() == 0


# Note: this test takes relatively long time to run, so you may want to skip it
@cocotb.test()
async def test_delay(dut):
    delay_ms_cycles = 10000 # Hardcoded value for now

    spell = SpellController(dut)
    clock = Clock(dut.clk, 10, units="us")
    cocotb.start_soon(clock.start())
    await reset(dut)

    await spell.write_program([10, ",", "z"])
    await spell.execute(False)

    await ClockCycles(dut.clk, 9 * delay_ms_cycles)
    assert await spell.read_pc() == 2
    assert dut.o_cpu_wait_delay.value == 1

    await ClockCycles(dut.clk, 2 * delay_ms_cycles)
    assert await spell.read_pc() == 3
    assert await spell.read_sp() == 0


@cocotb.test()
async def test_sleep(dut):
    spell = SpellController(dut)
    clock = Clock(dut.clk, 10, units="us")
    cocotb.start_soon(clock.start())
    await reset(dut)

    await spell.write_progmem(0, "z")
    await spell.execute()

    assert await spell.read_pc() == 1
    assert await spell.read_sp() == 0
    assert spell.sleeping()


@cocotb.test()
async def test_stop(dut):
    spell = SpellController(dut)
    clock = Clock(dut.clk, 10, units="us")
    cocotb.start_soon(clock.start())
    await reset(dut)

    await spell.write_progmem(0, 0xFF)
    await spell.execute()

    assert await spell.read_pc() == 1
    assert await spell.read_sp() == 0
    assert not spell.sleeping()


@cocotb.test()
async def test_code_mem_read(dut):
    spell = SpellController(dut)
    clock = Clock(dut.clk, 10, units="us")
    cocotb.start_soon(clock.start())
    await reset(dut)

    await spell.write_program([4, "?", "z", 0, 45])
    await spell.execute()

    assert await spell.read_pc() == 3
    assert await spell.read_sp() == 1
    assert await spell.read_stack_top() == 45


@cocotb.test()
async def test_code_mem_write(dut):
    spell = SpellController(dut)
    clock = Clock(dut.clk, 10, units="us")
    cocotb.start_soon(clock.start())
    await reset(dut)

    await spell.write_program([5, 3, "!", "z", "z"])
    await spell.execute()

    assert await spell.read_pc() == 5
    assert await spell.read_sp() == 1
    assert await spell.read_stack_top() == 5  # TODO WTF?


@cocotb.test()
async def test_data_mem(dut):
    spell = SpellController(dut)
    clock = Clock(dut.clk, 10, units="us")
    cocotb.start_soon(clock.start())
    await reset(dut)

    await spell.write_program([10, 4, "w", 15, 4, "r", "z"])  # why 15?
    await spell.execute()

    assert await spell.read_pc() == 7
    assert await spell.read_sp() == 2
    assert await spell.read_stack_top() == 10


@cocotb.test()
async def test_io(dut):
    PIN = 0x36
    DDR = 0x37
    PORT = 0x38

    spell = SpellController(dut)
    clock = Clock(dut.clk, 10, units="us")
    cocotb.start_soon(clock.start())
    await reset(dut)

    await spell.push(0xF0)
    await spell.push(DDR)
    await spell.exec_opcode("w")
    assert dut.uio_oe.value == 0xF0

    await spell.push(0x30)
    await spell.push(PORT)
    await spell.exec_opcode("w")
    assert dut.uio_out.value == 0x30

    await spell.push(0x50)
    await spell.push(PIN)
    await spell.exec_opcode("w")
    assert dut.uio_out.value == 0x60

    dut.uio_in.value = 0x7A
    await spell.push(PIN)
    await spell.exec_opcode("r")
    assert await spell.read_sp() == 1
    assert await spell.read_stack_top() == 0x7A


@cocotb.test()
async def test_io_pin_reg(dut):
    PIN = 0x36

    spell = SpellController(dut)
    clock = Clock(dut.clk, 10, units="us")
    cocotb.start_soon(clock.start())
    await reset(dut)

    await spell.write_program([0xF0, PIN, "w", 0x55, PIN, "w", "z"])
    await spell.execute()
    assert dut.uio_out.value == 0xA5  # 0xf0 ^ 0x55


@cocotb.test()
async def test_intg_multiply(dut):
    """
    SPELL integration test: multiplies two numbers
    """
    spell = SpellController(dut)
    clock = Clock(dut.clk, 10, units="us")
    cocotb.start_soon(clock.start())
    await reset(dut)

    # fmt: off
    await spell.write_program([
        10, 11,
        1, 'w',
        0, 'x',
        'x', 1, 'r', '+',
        'x', 6, '@',
        1, 'r', '-',
        'z',    
    ])
    # fmt: on

    await spell.execute()

    assert await spell.read_sp() == 1
    assert await spell.read_stack_top() == 110
