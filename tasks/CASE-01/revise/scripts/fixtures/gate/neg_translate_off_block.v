// unrecognized (RV-06): block-comment form, any case and extra blanks (lines 8 and 10)
module dot4sat (clk, rst, in_valid, in_a, in_b, out_valid, out_data);
    input clk, rst, in_valid;
    input [63:0] in_a, in_b;
    output reg out_valid;
    output reg [31:0] out_data;
    reg [31:0] shadow;
    /* synthesis translate_off */
    always @(posedge clk) shadow <= in_a[31:0];
    /*   SYNTHESIS   Translate_On   */
    always @(posedge clk) begin
        if (rst) out_valid <= 1'b0;
        else     out_valid <= in_valid;
        out_data <= in_a[31:0] ^ in_b[31:0];
    end
endmodule
