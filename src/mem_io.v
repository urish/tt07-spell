// SPDX-FileCopyrightText: © 2021 Uri Shaked <uri@wokwi.com>
// SPDX-License-Identifier: MIT

`default_nettype none

module spell_mem_io (
    input wire rst_n,
    input wire clk,
    input wire select,
    input wire [7:0] addr,
    input wire [7:0] data_in,
    input wire write,
    output reg [7:0] data_out,
    output reg data_ready,

    /* porta */
    output reg [7:0] porta_out,
    output reg [7:0] porta_oe,   // out enable (active high)

    /* porta */
    input  wire [7:0] portb_in,
    output reg  [7:0] portb_out,
    output reg  [7:0] portb_oe    // out enable (active high)
);

  localparam REG_PINB = 8'h36;
  localparam REG_DDRB = 8'h37;
  localparam REG_PORTB = 8'h38;
  localparam REG_PINA = 8'h39;
  localparam REG_DDRA = 8'h3a;
  localparam REG_PORTA = 8'h3b;

  reg past_write;

  always @(posedge clk) begin
    if (~rst_n) begin
      porta_out  <= 8'b00000000;
      porta_oe   <= 8'b00000000;
      portb_out  <= 8'b00000000;
      portb_oe   <= 8'b00000000;
      data_out   <= 8'b0;
      data_ready <= 1'b0;
      past_write <= 1'b0;
    end else begin
      past_write <= select & write;
      if (select) begin
        data_out   <= 8'b0;
        data_ready <= 1'b1;

        case (addr)
          REG_PINB: begin
            if (write) begin
              if (~past_write) portb_out <= portb_out ^ data_in;
            end else begin
              data_out <= portb_in;
            end
          end
          REG_DDRB: begin
            if (write) begin
              portb_oe <= data_in;
            end else begin
              data_out <= portb_oe;
            end
          end
          REG_PORTB: begin
            if (write) begin
              portb_out <= data_in;
            end else begin
              data_out <= portb_out;
            end
          end
          REG_PINA: begin
            if (write) begin
              if (~past_write) porta_out <= porta_out ^ data_in;
            end else begin
              data_out <= 8'h00;
            end
          end
          REG_DDRA: begin
            if (write) begin
              porta_oe <= data_in;
            end else begin
              data_out <= porta_oe;
            end
          end
          REG_PORTA: begin
            if (write) begin
              porta_out <= data_in;
            end else begin
              data_out <= porta_out;
            end
          end
          default: begin
            if (~write) data_out <= 8'hff;
          end
        endcase
      end else data_ready <= 1'b0;
    end
  end
endmodule
