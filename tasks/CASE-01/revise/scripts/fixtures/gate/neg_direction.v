// G1: out_valid declared as input
module dot4sat (clk, rst, in_valid, in_a, in_b, out_valid, out_data);
    input clk, rst, in_valid;
    input [63:0] in_a, in_b;
    input out_valid;
    output reg [31:0] out_data;
    always @(posedge clk) begin
        out_data <= in_a[31:0] ^ in_b[31:0];
    end
endmodule
