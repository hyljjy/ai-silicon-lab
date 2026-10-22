// CASE-01 candidate: input-registered pipeline, latency L = 2.
// Stage 1 registers in_a/in_b/in_valid; stage 2 computes products, exact 34-bit sum,
// saturation and registers the output. Synchronous active-high reset clears both
// valid pipeline stages; data registers are not reset (spec 2.4).
module dot4sat (
    input  wire        clk,
    input  wire        rst,
    input  wire        in_valid,
    input  wire [63:0] in_a,
    input  wire [63:0] in_b,
    output reg         out_valid,
    output reg  [31:0] out_data
);

    reg [63:0] a_q;
    reg [63:0] b_q;
    reg        v_q;

    wire signed [15:0] a0 = a_q[15:0];
    wire signed [15:0] a1 = a_q[31:16];
    wire signed [15:0] a2 = a_q[47:32];
    wire signed [15:0] a3 = a_q[63:48];
    wire signed [15:0] b0 = b_q[15:0];
    wire signed [15:0] b1 = b_q[31:16];
    wire signed [15:0] b2 = b_q[47:32];
    wire signed [15:0] b3 = b_q[63:48];

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
        a_q      <= in_a;
        b_q      <= in_b;
        out_data <= sat;
        if (rst) begin
            v_q       <= 1'b0;
            out_valid <= 1'b0;
        end else begin
            v_q       <= in_valid;
            out_valid <= v_q;
        end
    end

endmodule
