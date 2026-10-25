// CASE-01 candidate rev2: three-stage pipeline, latency L = 3.
// No signed declarations anywhere (avoid signed nets in the synthesized netlist).
// Stage 1: register operands. Stage 2: register four 16x16 signed products.
// Stage 3: exact 34-bit sum, saturate to 32-bit signed, register output.
// Valid bits are cleared by synchronous active-high reset at every stage.
module dot4sat (
    input  wire        clk,
    input  wire        rst,
    input  wire        in_valid,
    input  wire [63:0] in_a,
    input  wire [63:0] in_b,
    output reg         out_valid,
    output reg  [31:0] out_data
);

    reg [63:0] a_r;
    reg [63:0] b_r;
    reg        v1;

    reg [31:0] p0_r;
    reg [31:0] p1_r;
    reg [31:0] p2_r;
    reg [31:0] p3_r;
    reg        v2;

    // signed 16x16 products; true value fits in 32-bit two's complement
    wire [31:0] p0 = $signed(a_r[15:0])  * $signed(b_r[15:0]);
    wire [31:0] p1 = $signed(a_r[31:16]) * $signed(b_r[31:16]);
    wire [31:0] p2 = $signed(a_r[47:32]) * $signed(b_r[47:32]);
    wire [31:0] p3 = $signed(a_r[63:48]) * $signed(b_r[63:48]);

    // exact 34-bit two's complement sum via explicit sign extension
    wire [33:0] e0 = {{2{p0_r[31]}}, p0_r};
    wire [33:0] e1 = {{2{p1_r[31]}}, p1_r};
    wire [33:0] e2 = {{2{p2_r[31]}}, p2_r};
    wire [33:0] e3 = {{2{p3_r[31]}}, p3_r};
    wire [33:0] sum = e0 + e1 + e2 + e3;

    // s > 2^31-1  <=> non-negative and sum[32:31] != 00
    // s < -2^31   <=> negative and sum[32:31] != 11
    wire ovf_pos = ~sum[33] & (sum[32] | sum[31]);
    wire ovf_neg =  sum[33] & ~(sum[32] & sum[31]);

    wire [31:0] sat = ovf_pos ? 32'h7FFF_FFFF :
                      ovf_neg ? 32'h8000_0000 : sum[31:0];

    always @(posedge clk) begin
        if (rst) begin
            v1        <= 1'b0;
            v2        <= 1'b0;
            out_valid <= 1'b0;
        end else begin
            v1        <= in_valid;
            v2        <= v1;
            out_valid <= v2;
        end
        a_r      <= in_a;
        b_r      <= in_b;
        p0_r     <= p0;
        p1_r     <= p1;
        p2_r     <= p2;
        p3_r     <= p3;
        out_data <= sat;
    end

endmodule
