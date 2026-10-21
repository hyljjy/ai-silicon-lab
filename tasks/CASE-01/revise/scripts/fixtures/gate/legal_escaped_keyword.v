// legal: escaped identifiers that spell keywords are identifiers, never keywords
module dot4sat (
    input  wire        clk,
    input  wire        rst,
    input  wire        in_valid,
    input  wire [63:0] in_a,
    input  wire [63:0] in_b,
    output reg         out_valid,
    output reg  [31:0] out_data
);
    wire [31:0] \begin  = in_a[31:0] ^ in_b[31:0];
    wire \parameter  = in_valid;
    wire \module  = rst;
    always @(posedge clk) begin
        if (\module ) out_valid <= 1'b0;
        else          out_valid <= \parameter ;
        out_data <= \begin ;
    end
endmodule
