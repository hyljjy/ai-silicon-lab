// SELF-TEST MUTANT (P1 M3): out_valid is correct but out_data is unknown (X). Must make the TB fail.
module dot4sat (
    input  wire        clk,
    input  wire        rst,
    input  wire        in_valid,
    input  wire [63:0] in_a,
    input  wire [63:0] in_b,
    output reg         out_valid,
    output reg  [31:0] out_data
);
    always @(posedge clk) begin
        if (rst) out_valid <= 1'b0;
        else     out_valid <= in_valid;
        out_data <= 32'hxxxx_xxxx;    // BUG: data never computed
    end
endmodule
