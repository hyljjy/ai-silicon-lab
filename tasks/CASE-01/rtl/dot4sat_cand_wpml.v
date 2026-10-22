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

    // First pipeline stage: register the four products.
    reg signed [31:0] p0_q;
    reg signed [31:0] p1_q;
    reg signed [31:0] p2_q;
    reg signed [31:0] p3_q;

    // Second pipeline stage: exact 34-bit sum and saturation.
    wire signed [33:0] s0 = p0_q;
    wire signed [33:0] s1 = p1_q;
    wire signed [33:0] s2 = p2_q;
    wire signed [33:0] s3 = p3_q;
    wire signed [33:0] sum = s0 + s1 + s2 + s3;

    localparam signed [33:0] SMAX = 34'sd2147483647;
    localparam signed [33:0] SMIN = -34'sd2147483648;

    wire [31:0] sat = (sum > SMAX) ? 32'h7fff_ffff :
                      (sum < SMIN) ? 32'h8000_0000 : sum[31:0];

    // Valid pipeline: one internal delay stage plus the output register.
    reg valid_q;

    always @(posedge clk) begin
        if (rst) begin
            valid_q   <= 1'b0;
            out_valid <= 1'b0;
        end else begin
            valid_q   <= in_valid;
            out_valid <= valid_q;
        end
        p0_q <= p0;
        p1_q <= p1;
        p2_q <= p2;
        p3_q <= p3;
        out_data <= sat;
    end

endmodule
