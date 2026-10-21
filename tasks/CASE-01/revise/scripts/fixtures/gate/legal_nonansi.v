// legal: non-ANSI header (port list) with separate port declarations and reg declarations
module dot4sat (clk, rst, in_valid, in_a, in_b, out_valid, out_data);
    input clk;
    input wire rst;
    input in_valid;
    input [63:0] in_a;
    input [63:0] in_b;
    output out_valid;
    output [31:0] out_data;
    reg out_valid;
    reg [31:0] out_data;
    wire signed [31:0] p0 = $signed(in_a[15:0])  * $signed(in_b[15:0]);
    wire signed [31:0] p1 = $signed(in_a[31:16]) * $signed(in_b[31:16]);
    wire signed [31:0] p2 = $signed(in_a[47:32]) * $signed(in_b[47:32]);
    wire signed [31:0] p3 = $signed(in_a[63:48]) * $signed(in_b[63:48]);
    wire signed [33:0] sum;
    assign sum = p0 + p1 + p2 + p3;
    reg [31:0] sat;
    always @* begin
        sat = sum[31:0];
        if (sum > 34'sd2147483647) sat = 32'h7FFF_FFFF;
        else if (sum < -34'sd2147483648) sat = 32'h8000_0000;
    end
    always @(posedge clk) begin
        if (rst) out_valid <= 1'b0;
        else     out_valid <= in_valid;
        out_data <= sat;
    end
endmodule
