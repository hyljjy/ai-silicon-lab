// CASE-01 L=2 implementation: register inputs first, then multiply/sum/saturate
// in the second stage. Synchronous active-high reset clears all valid state.
// Data registers are intentionally not reset (data is don't-care when out_valid=0).
module dot4sat (
    input  wire        clk,
    input  wire        rst,
    input  wire        in_valid,
    input  wire [63:0] in_a,
    input  wire [63:0] in_b,
    output reg         out_valid,
    output reg  [31:0] out_data
);

    // First pipeline stage: capture inputs and a valid bit.
    reg [63:0] a_q;
    reg [63:0] b_q;
    reg        valid_q;

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

    // Full range is [-4294836224, 4294967296]: needs 34 signed bits.
    wire signed [33:0] sum = p0 + p1 + p2 + p3;

    localparam signed [33:0] SMAX = 34'sd2147483647;
    localparam signed [33:0] SMIN = -34'sd2147483648;

    wire [31:0] sat = (sum > SMAX) ? 32'h7fff_ffff :
                      (sum < SMIN) ? 32'h8000_0000 : sum[31:0];

    always @(posedge clk) begin
        if (rst) begin
            valid_q   <= 1'b0;
            out_valid <= 1'b0;
        end else begin
            valid_q   <= in_valid;
            out_valid <= valid_q;
        end
        a_q      <= in_a;
        b_q      <= in_b;
        out_data <= sat;
    end

endmodule
