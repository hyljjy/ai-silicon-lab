// legal: comments that mention translate_off in the middle of the text are ordinary comments (RV-06)
module dot4sat (clk, rst, in_valid, in_a, in_b, out_valid, out_data);
    input clk, rst, in_valid;
    input [63:0] in_a, in_b;
    output reg out_valid;
    output reg [31:0] out_data;
    // no synopsys translate_off is used in this file
    /* note: synthesis translate_on would be refused */
    // synopsys_translate_off is not the form either
    always @(posedge clk) begin
        if (rst) out_valid <= 1'b0;
        else     out_valid <= in_valid;
        out_data <= in_a[31:0] ^ in_b[31:0];
    end
endmodule
