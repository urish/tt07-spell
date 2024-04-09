// SPDX-FileCopyrightText: © 2021 Uri Shaked <uri@wokwi.com>
// SPDX-License-Identifier: MIT

`default_nettype none

module spell_mem (
    input wire rst_n,
    input wire clk,
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
    output wire [7:0] io_oe  // out enable bar (low active)
);

  wire code_select = select && !memory_type_data;

  wire data_select = select && memory_type_data;
  wire data_mem_select = data_select && (addr < 8'h20 || addr >= 8'h60);
  wire data_io_select = data_select && (addr >= 8'h20 && addr < 8'h60);

  wire mem_select = code_select || data_mem_select;

  wire io_data_ready;
  wire internal_data_ready;
  assign data_ready = io_data_ready | internal_data_ready;

  wire [7:0] io_data_out;
  wire [7:0] internal_data_out;

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

  spell_mem_internal mem_internal (
      .rst_n(rst_n),
      .clk(clk),
      .select(mem_select),
      .addr(addr),
      .data_in(data_in),
      .memory_type_data(memory_type_data),
      .write(write),
      .data_out(internal_data_out),
      .data_ready(internal_data_ready)
  );

  always @(*) begin
    if (data_io_select) begin
      data_out = io_data_out;
    end else begin
      data_out = internal_data_out;
    end
  end

endmodule
