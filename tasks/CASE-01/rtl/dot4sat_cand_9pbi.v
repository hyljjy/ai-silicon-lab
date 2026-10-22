// CASE-01 candidate: three-stage pipeline, latency L = 3.
// Stage 1: register operands. Stage 2: register four signed 16x16 products.
// Stage 3: exact 34-bit sum, saturate to 32-bit signed, register output.
// Valid bits are cleared by synchronous active-high reset at every stage.
// Data registers are not reset (data is don't-care when valid is 0).
module dot4sat (
    input  wire        clk,
    input  wire        rst,
    input  wire        in_valid,
    input  wire [63:0] in_a,
    input  wire [63:0] in_b,
    output reg         out_valid,
    output reg  [31:0] out_data
);

    // stage 1 registers
    reg [63:0] a_r;
    reg [63:0] b_r;
    reg        v1;

    // stage 2 registers
    reg signed [31:0] p0_r;
    reg signed [31:0] p1_r;
    reg signed [31:0] p2_r;
    reg signed [31:0] p3_r;
    reg               v2;

    wire signed [15:0] a0 = a_r[15:0];
    wire signed [15:0] a1 = a_r[31:16];
    wire signed [15:0] a2 = a_r[47:32];
    wire signed [15:0] a3 = a_r[63:48];
    wire signed [15:0] b0 = b_r[15:0];
    wire signed [15:0] b1 = b_r[31:16];
    wire signed [15:0] b2 = b_r[47:32];
    wire signed [15:0] b3 = b_r[63:48];

    wire signed [31:0] p0 = a0 * b0;
    wire signed [31:0] p1 = a1 * b1;
    wire signed [31:0] p2 = a2 * b2;
    wire signed [31:0] p3 = a3 * b3;

    // full range is [-4294836224, 4294967296]: needs 34 signed bits
    wire signed [33:0] sum = p0_r + p1_r + p2_r + p3_r;

    localparam signed [33:0] SMAX = 34'sd2147483647;
    localparam signed [33:0] SMIN = -34'sd2147483648;

    wire [31:0] sat = (sum > SMAX) ? 32'h7FFF_FFFF :
                      (sum < SMIN) ? 32'h8000_0000 : sum[31:0];

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
