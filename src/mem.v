// SPDX-FileCopyrightText: © 2021 Uri Shaked <uri@wokwi.com>
// SPDX-License-Identifier: MIT

`default_nettype none
//
`timescale 1ns / 1ps

module spell_mem (
    input wire rst_n,
    input wire clk,
    input wire sram_enable,
    input wire select,
    input wire [7:0] addr,
    input wire [7:0] data_in,
    input wire memory_type_data,
    input wire write,
    output reg [7:0] data_out,
    output wire data_ready,

    /* IO */
    input  wire [7:0] io_in,
    output wire [7:0] io_out,
    output wire [7:0] io_oe,  // out enable bar (low active)

    /* Wishbone OpenRAM */
    input wire [31:0] sram_dat_i,
    input wire sram_ack_i,
    output wire sram_cyc_o,
    output wire sram_stb_o,
    output wire sram_we_o,
    output wire [3:0] sram_sel_o,
    output wire [9:0] sram_addr_o,
    output wire [31:0] sram_dat_o
);

  wire code_select = select && !memory_type_data;

  wire data_select = select && memory_type_data;
  wire data_mem_select = data_select && (addr < 8'h20 || addr >= 8'h60);
  wire data_io_select = data_select && (addr >= 8'h20 && addr < 8'h60);

  wire mem_select = code_select || data_mem_select;
  wire sram_select = mem_select && sram_enable;

  wire [1:0] sram_byte_index = addr[1:0];
  assign sram_cyc_o  = sram_select;
  assign sram_stb_o  = sram_select;
  assign sram_we_o   = write;
  assign sram_sel_o  = 1 << sram_byte_index;
  assign sram_addr_o = {1'b0, data_select, addr[7:2], 2'b00};
  assign sram_dat_o  = {data_in, data_in, data_in, data_in};

  wire io_data_ready;
  wire dff_data_ready;
  assign data_ready = io_data_ready | dff_data_ready | (sram_select && sram_ack_i);

  wire [7:0] io_data_out;
  wire [7:0] dff_data_out;
  wire [7:0] sram_data_out;

  spell_mem_io mem_io (
      .rst_n(rst_n),
      .clk(clk),
      .select(data_io_select),
      .addr(addr),
      .data_in(data_in),
      .write(write),
      .data_out(io_data_out),
      .data_ready(io_data_ready),

      /* IO */
      .io_in (io_in),
      .io_out(io_out),
      .io_oe(io_oe)
  );

  spell_mem_dff mem_dff (
      .rst_n(rst_n),
      .clk(clk),
      .select(!sram_select && mem_select),
      .addr(addr),
      .data_in(data_in),
      .memory_type_data(memory_type_data),
      .write(write),
      .data_out(dff_data_out),
      .data_ready(dff_data_ready)
  );

  always @(*) begin
    if (data_io_select) begin
      data_out = io_data_out;
    end else if (sram_enable) begin
      case (sram_byte_index)
        0: data_out = sram_dat_i[7:0];
        1: data_out = sram_dat_i[15:8];
        2: data_out = sram_dat_i[23:16];
        3: data_out = sram_dat_i[31:24];
      endcase
    end else begin
      data_out = dff_data_out;
    end
  end

endmodule
