// unrecognized (RV-06): an extra port hidden from Yosys by translate_off / translate_on (lines 7 and 9)
module dot4sat (clk, rst, in_valid, in_a, in_b, out_valid, out_data, dbg);
    input clk, rst, in_valid;
    input [63:0] in_a, in_b;
    output reg out_valid;
    output reg [31:0] out_data;
    // synopsys translate_off
    output dbg;
    // synopsys translate_on
    always @(posedge clk) begin
        if (rst) out_valid <= 1'b0;
        else     out_valid <= in_valid;
        out_data <= in_a[31:0] ^ in_b[31:0];
    end
endmodule
