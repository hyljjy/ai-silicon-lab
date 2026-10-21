// legal: non-ANSI port widths given by localparam expressions
module dot4sat (clk, rst, in_valid, in_a, in_b, out_valid, out_data);
    localparam LANE = 16;
    localparam LANES = 4;
    localparam IW = LANE * LANES;
    localparam OW = 2 * LANE;
    input clk, rst, in_valid;
    input [IW-1:0] in_a, in_b;
    output reg out_valid;
    output reg [OW-1:0] out_data;
    wire signed [33:0] sum = $signed(in_a[15:0]) * $signed(in_b[15:0]) + $signed(in_a[31:16]) * $signed(in_b[31:16])
                           + $signed(in_a[47:32]) * $signed(in_b[47:32]) + $signed(in_a[63:48]) * $signed(in_b[63:48]);
    always @(*) begin
    end
    always @(posedge clk) begin
        if (rst) out_valid <= 1'b0;
        else     out_valid <= in_valid;
        out_data <= (sum > 34'sd2147483647) ? 32'h7FFF_FFFF : (sum < -34'sd2147483648) ? 32'h8000_0000 : sum[OW-1:0];
    end
endmodule
