/*
 * Copyright (c) 2026 Malik
 * SPDX-License-Identifier: Apache-2.0
 *
 * TinyTapeout IHP 26a — Gate-Level 8-bit Unsigned MAC with Ripple-Carry Accumulator
 *
 * Wraps a combinational MAC unit (y = a*b + c) from ML-guided design-space
 * exploration into a TinyTapeout-compatible clocked interface.
 *
 * The inner MAC is a structurally-optimized gate-level netlist produced by
 * approximate/exact arithmetic synthesis exploration.
 *
 * IO Protocol:
 *   ui_in[7:0]  — data input (operand A or B)
 *   uo_out[7:0] — data output (accumulator readout)
 *   uio_in[2:0] — command:
 *     3'b000 = NOP
 *     3'b001 = Load operand A from ui_in
 *     3'b010 = Load operand B from ui_in → triggers MAC (acc = a*b + acc)
 *     3'b011 = Read acc[7:0]   (LSB)
 *     3'b100 = Read acc[15:8]  (MSB lower)
 *     3'b101 = Read acc[16]    (carry/overflow bit)
 *     3'b110 = Clear accumulator
 *     3'b111 = Load accumulator LSB from ui_in (preload mode)
 *   uio_out[0]  — busy (high for 1 cycle after MAC)
 *   uio_out[1]  — overflow (acc[16] set)
 */

`default_nettype none

module tt_um_malik_mac_ripple (
    input  wire [7:0] ui_in,
    output wire [7:0] uo_out,
    input  wire [7:0] uio_in,
    output wire [7:0] uio_out,
    output wire [7:0] uio_oe,
    input  wire       ena,
    input  wire       clk,
    input  wire       rst_n
);

    // IO direction: uio[2:0] input (cmd), rest input
    // uio_out[1:0] output (busy, overflow)
    assign uio_oe = 8'b0000_0011;

    // =========================================================
    // Commands
    // =========================================================
    wire [2:0] cmd = uio_in[2:0];

    localparam CMD_NOP       = 3'b000;
    localparam CMD_LOAD_A    = 3'b001;
    localparam CMD_LOAD_B_GO = 3'b010;
    localparam CMD_READ_LSB  = 3'b011;
    localparam CMD_READ_MSB  = 3'b100;
    localparam CMD_READ_OVF  = 3'b101;
    localparam CMD_CLEAR     = 3'b110;
    localparam CMD_PRELOAD   = 3'b111;

    // =========================================================
    // Registers
    // =========================================================
    reg [7:0]  op_a;        // Operand A
    reg [7:0]  op_b;        // Operand B
    reg [16:0] acc;         // 17-bit accumulator (matches MAC output width)
    reg        busy;

    // =========================================================
    // Instantiate the gate-level combinational MAC
    // y[16:0] = a[7:0] * b[7:0] + c[15:0]
    // =========================================================
    wire [16:0] mac_result;

    mac_8b_unsigned_and_accum_ripple_carry u_mac (
        .a(op_a),
        .b(op_b),
        .c(acc[15:0]),      // feed back lower 16 bits of accumulator
        .y(mac_result)
    );

    // =========================================================
    // Main sequential logic
    // =========================================================
    always @(posedge clk) begin
        if (!rst_n) begin
            op_a <= 8'd0;
            op_b <= 8'd0;
            acc  <= 17'd0;
            busy <= 1'b0;
        end else if (ena) begin
            busy <= 1'b0;

            case (cmd)
                CMD_LOAD_A: begin
                    op_a <= ui_in;
                end

                CMD_LOAD_B_GO: begin
                    op_b <= ui_in;
                    // MAC result will be valid combinationally on next read
                    // but we register it for clean timing
                    acc  <= mac_result;
                    busy <= 1'b1;
                end

                CMD_CLEAR: begin
                    acc <= 17'd0;
                end

                CMD_PRELOAD: begin
                    // Allow loading a value into the accumulator LSB
                    // (useful for chaining or testing)
                    acc[7:0] <= ui_in;
                end

                default: ;  // NOP, READ — no state change
            endcase
        end
    end

    // =========================================================
    // Output mux
    // =========================================================
    reg [7:0] data_out;
    always @(*) begin
        case (cmd)
            CMD_READ_LSB: data_out = acc[7:0];
            CMD_READ_MSB: data_out = acc[15:8];
            CMD_READ_OVF: data_out = {7'b0, acc[16]};
            default:       data_out = acc[7:0];
        endcase
    end

    assign uo_out = data_out;

    // =========================================================
    // Status
    // =========================================================
    assign uio_out[0] = busy;
    assign uio_out[1] = acc[16];  // overflow / carry bit
    assign uio_out[7:2] = 6'b0;

endmodule
