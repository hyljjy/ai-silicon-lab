// legal: ANSI header, wire/reg declarations, two-stage pipeline (L = 2)
module dot4sat (
    input  wire        clk,
    input  wire        rst,
    input  wire        in_valid,
    input  wire [63:0] in_a,
    input  wire [63:0] in_b,
    output reg         out_valid,
    output reg  [31:0] out_data
);
    reg signed [31:0] p0, p1, p2, p3;
    reg               v1;
    wire signed [33:0] sum = p0 + p1 + p2 + p3;
    localparam signed [33:0] SMAX = 34'sd2147483647;
    localparam signed [33:0] SMIN = -34'sd2147483648;
    always @(posedge clk) begin
        if (rst) v1 <= 1'b0;
        else     v1 <= in_valid;
        p0 <= $signed(in_a[15:0])  * $signed(in_b[15:0]);
        p1 <= $signed(in_a[31:16]) * $signed(in_b[31:16]);
        p2 <= $signed(in_a[47:32]) * $signed(in_b[47:32]);
        p3 <= $signed(in_a[63:48]) * $signed(in_b[63:48]);
    end
    always @(posedge clk) begin
        if (rst) out_valid <= 1'b0;
        else     out_valid <= v1;
        out_data <= (sum > SMAX) ? 32'h7FFF_FFFF : (sum < SMIN) ? 32'h8000_0000 : sum[31:0];
    end
endmodule
