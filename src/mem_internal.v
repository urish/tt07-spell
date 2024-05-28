// SPDX-FileCopyrightText: © 2021-2024 Uri Shaked <uri@wokwi.com>
// SPDX-License-Identifier: MIT

`default_nettype none

module spell_mem_internal (
    input wire rst_n,
    input wire clk,
    input wire select,
    input wire [7:0] addr,
    input wire [7:0] data_in,
    input wire memory_type_data,
    input wire write,
    output wire [7:0] data_out,
    output reg data_ready
);

  localparam data_mem_size = 32;

  wire code_mem_lo_sel = !memory_type_data && addr[7] == 1'b0;
  wire code_mem_hi_sel = !memory_type_data && addr[7] == 1'b1;

  reg code_mem_ready;
  reg [4:0] code_mem_init_addr;

  wire [4:0] code_mem_addr = code_mem_ready ? addr[6:2] : code_mem_init_addr;
  wire [31:0] code_mem_lo_do;
  wire [31:0] code_mem_hi_do;
  wire [31:0] code_mem_di = code_mem_ready ? {data_in, data_in, data_in, data_in} : 32'hffffffff;
  wire [31:0] code_mem_do = code_mem_lo_sel ? code_mem_lo_do : code_mem_hi_do;

  wire [4:0] word_index = {addr[1:0], 3'b000};
  wire [7:0] code_mem_out = code_mem_do[word_index+:8];
  reg [7:0] data_mem_out;
  wire [7:0] data_out_byte = memory_type_data ? data_mem_out : code_mem_out;
  assign data_out = data_ready ? data_out_byte : 8'bx;


  wire we = select && write;
  wire [3:0] we_sel = we ? (1 << addr[1:0]) : 0;
  wire [3:0] code_mem_we0 = code_mem_ready ? we_sel : 4'b1111;

  RAM32 code_mem_lo (
      .CLK(clk),
      .EN0(rst_n),
      .WE0(code_mem_lo_sel || !code_mem_ready ? code_mem_we0 : 4'b0000),
      .A0 (code_mem_addr),
      .Di0(code_mem_di),
      .Do0(code_mem_lo_do)
  );

  RAM32 code_mem_hi (
      .CLK(clk),
      .EN0(rst_n),
      .WE0(code_mem_hi_sel || !code_mem_ready ? code_mem_we0 : 4'b0000),
      .A0 (code_mem_addr),
      .Di0(code_mem_di),
      .Do0(code_mem_hi_do)
  );

  localparam data_mem_bits = $clog2(data_mem_size);
  reg [7:0] data_mem[data_mem_size-1:0];
  wire [data_mem_bits-1:0] data_addr = addr[data_mem_bits-1:0];

  reg [1:0] cycles;

  integer i;

  always @(posedge clk) begin
    if (~rst_n) begin
      cycles <= 0;
      data_ready <= 0;
      data_mem_out <= 0;
      for (i = 0; i < data_mem_size; i++) data_mem[i] <= 8'h00;
      code_mem_ready <= 0;
      code_mem_init_addr <= 0;
    end else begin
      if (!code_mem_ready) begin
        code_mem_init_addr <= code_mem_init_addr + 1;
        if (code_mem_init_addr == 5'b11111) begin
          code_mem_ready <= 1;
        end
      end else if (!select) begin
        data_ready <= 1'b0;
`ifdef SPELL_INTERNAL_MEM_DELAY
        cycles <= 2'b11;
`endif  /* SPELL_INTERNAL_MEM_DELAY */
      end else if (cycles > 0) begin
        cycles <= cycles - 1;
      end else begin
        data_ready <= 1'b1;
        if (write) begin
          if (memory_type_data && addr < data_mem_size) begin
            data_mem[data_addr] <= data_in;
          end
        end else begin
          data_mem_out <= 8'h00;
          if (memory_type_data && addr < data_mem_size) begin
            data_mem_out <= data_mem[data_addr];
          end
        end
      end
    end
  end
endmodule
