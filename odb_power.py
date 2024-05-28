#
# OpenDB script for custom Power for DFFRAM macro instances
#
# Copyright (c) 2023 Sylvain Munaut <tnt@246tNt.com>
# Copyright (c) 2024 Tiny Tapeout LTD
# SPDX-License-Identifier: Apache-2.0
#

import odb
import click

from reader import click_odb


@click.option(
    "--macro-x-pos", type=float, multiple=True, help="X positions of the RAM32 macro"
)
@click.command()
@click_odb
def power(reader, macro_x_pos: list[int]):
    # Create ground / power nets
    tech = reader.db.getTech()
    vpwr_net = reader.block.findNet("VPWR")
    vgnd_net = reader.block.findNet("VGND")
    met4 = tech.findLayer("met4")
    vpwr_wire = vpwr_net.getSWires()[0]
    vgnd_wire = vgnd_net.getSWires()[0]
    vpwr_bterm = vpwr_net.getBTerms()[0]
    vgnd_bterm = vgnd_net.getBTerms()[0]
    vpwr_bpin = vpwr_bterm.getBPins()[0]
    vgnd_bpin = vgnd_bterm.getBPins()[0]
    for x_pos in macro_x_pos:
        for i in range(3):
            x = int(x_pos * 1000) + 18280 + i * 153600
            odb.dbSBox_create(vpwr_wire, met4, x, 7880, x + 1600, 223280, "STRIPE")
            odb.dbBox_create(vpwr_bpin, met4, x, 7880, x + 1600, 223280)
        for i in range(2):
            x = int(x_pos * 1000) + 95080 + i * 153600
            odb.dbSBox_create(vgnd_wire, met4, x, 7880, x + 1600, 223280, "STRIPE")
            odb.dbBox_create(vgnd_bpin, met4, x, 7880, x + 1600, 223280)

    # PDN adds two shorter VPWR/VGND stripes on the right side, so extend them to full height in order to pass precheck
    odb.dbSBox_create(vpwr_wire, met4, 1357580, 2480, 1359180, 223280, "STRIPE")
    odb.dbBox_create(vpwr_bpin, met4, 1357580, 2480, 1359180, 223280)
    odb.dbSBox_create(vgnd_wire, met4, 1360340, 2480, 1361940, 223280, "STRIPE")
    odb.dbBox_create(vgnd_bpin, met4, 1360340, 2480, 1361940, 223280)


if __name__ == "__main__":
    power()
