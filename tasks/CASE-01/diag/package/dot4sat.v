// CASE-01 baseline (spec 1, D1): four signed 16x16 products summed exactly, saturated to 32-bit signed.
// Output registered only; latency L = 1. Synchronous active-high reset clears out_valid.
// out_data is not reset and has no enable (spec 2.4: data is don't-care when out_valid = 0).
module dot4sat (
    input  wire        clk,
    input  wire        rst,
    input  wire        in_valid,
    input  wire [63:0] in_a,
    input  wire [63:0] in_b,
    output reg         out_valid,
    output reg  [31:0] out_data
);

    wire signed [15:0] a0 = in_a[15:0];
    wire signed [15:0] a1 = in_a[31:16];
    wire signed [15:0] a2 = in_a[47:32];
    wire signed [15:0] a3 = in_a[63:48];
    wire signed [15:0] b0 = in_b[15:0];
    wire signed [15:0] b1 = in_b[31:16];
    wire signed [15:0] b2 = in_b[47:32];
    wire signed [15:0] b3 = in_b[63:48];

    wire signed [31:0] p0 = a0 * b0;
    wire signed [31:0] p1 = a1 * b1;
    wire signed [31:0] p2 = a2 * b2;
    wire signed [31:0] p3 = a3 * b3;

    // full range is [-4294836224, 4294967296]: needs 34 signed bits
    wire signed [33:0] sum = p0 + p1 + p2 + p3;

    localparam signed [33:0] SMAX = 34'sd2147483647;
    localparam signed [33:0] SMIN = -34'sd2147483648;

    wire [31:0] sat = (sum > SMAX) ? 32'h7FFF_FFFF :
                      (sum < SMIN) ? 32'h8000_0000 : sum[31:0];

    always @(posedge clk) begin
        if (rst) out_valid <= 1'b0;
        else     out_valid <= in_valid;
        out_data <= sat;
    end

endmodule
