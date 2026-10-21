// legal (RV-07): non-ANSI module with the net declaration "wire clk;" of the header port clk
module dot4sat (clk, rst, in_valid, in_a, in_b, out_valid, out_data);
    input clk, rst, in_valid;
    input [63:0] in_a, in_b;
    output out_valid;
    output [31:0] out_data;
    wire clk;
    reg out_valid;
    reg [31:0] out_data;
    always @(posedge clk) begin
        if (rst) out_valid <= 1'b0;
        else     out_valid <= in_valid;
        out_data <= in_a[31:0] ^ in_b[31:0];
    end
endmodule
