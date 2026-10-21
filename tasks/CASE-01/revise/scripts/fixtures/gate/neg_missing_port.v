// G1: in_valid is missing
module dot4sat (clk, rst, in_a, in_b, out_valid, out_data);
    input clk, rst;
    input [63:0] in_a, in_b;
    output reg out_valid;
    output reg [31:0] out_data;
    always @(posedge clk) begin
        if (rst) out_valid <= 1'b0;
        else     out_valid <= 1'b1;
        out_data <= in_a[31:0] ^ in_b[31:0];
    end
endmodule
