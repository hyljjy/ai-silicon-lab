// G1: an extra port ready
module dot4sat (clk, rst, in_valid, in_a, in_b, out_valid, out_data, ready);
    input clk, rst, in_valid;
    input [63:0] in_a, in_b;
    output reg out_valid;
    output reg [31:0] out_data;
    output ready;
    assign ready = 1'b1;
    always @(posedge clk) begin
        if (rst) out_valid <= 1'b0;
        else     out_valid <= in_valid;
        out_data <= in_a[31:0] ^ in_b[31:0];
    end
endmodule
