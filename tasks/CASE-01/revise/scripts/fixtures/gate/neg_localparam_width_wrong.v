// G1: out_data width by localparam expression is 31, not 32
module dot4sat (clk, rst, in_valid, in_a, in_b, out_valid, out_data);
    localparam LANE = 16;
    localparam OW = 2 * LANE - 1;
    input clk, rst, in_valid;
    input [63:0] in_a, in_b;
    output reg out_valid;
    output reg [OW-1:0] out_data;
    always @(posedge clk) begin
        if (rst) out_valid <= 1'b0;
        else     out_valid <= in_valid;
        out_data <= in_a[30:0] ^ in_b[30:0];
    end
endmodule
