# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: © 2024 Tiny Tapeout LTD
# Author: Uri Shaked

"""
Simulates a 23LC512 SPI SRAM chip
"""

from cocotbext.spi import SpiSlaveBase, SpiBus, SpiConfig

# Instructions
INST_WRITE = 0x02
INST_READ = 0x03
INST_EDIO = 0x3B
INST_EQIO = 0x38
INST_RSTIO = 0xFF
INST_RDMR = 0x05
INST_WRMR = 0x01


class SRAM23LC512(SpiSlaveBase):
    def __init__(self, bus: SpiBus):
        self._config = SpiConfig(cpol=True, cpha=True)
        self.buffer = bytearray(64 * 1024)
        super().__init__(bus)

    async def _transaction(self, frame_start, frame_end):
        await frame_start
        self.idle.clear()

        instruction = int(await self._shift(8))

        if instruction == INST_WRITE:
            address = int(await self._shift(16))
            data = int(await self._shift(8))
            self.buffer[address] = data

        elif instruction == INST_READ:
            address = int(await self._shift(16))
            await self._shift(8, tx_word=self.buffer[address])

        else:
            raise ValueError(f"Unsupported instruction code: 0x{instruction:02x}")

        await frame_end
