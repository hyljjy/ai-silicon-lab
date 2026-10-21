// legal: parameter, `define, `timescale, clk and $fopen in comments and strings are not misread
/* parameter W = 3; `include "x.v" always @(negedge clk) #5 initial
   $fopen("f") $value$plusargs */
module dot4sat (
    input  wire        clk,   // the clk port; parameter in a comment
    input  wire        rst,
    input  wire        in_valid,
    input  wire [63:0] in_a,
    input  wire [63:0] in_b,
    output reg         out_valid,
    output reg  [31:0] out_data
);
    localparam [8*18-1:0] TAG = "parameter `x \"clk";   /* synthesis keep */
    wire [31:0] x = in_a[31:0] ^ in_b[31:0]; // clk `timescale $fopen
    always @(posedge clk) begin
        if (rst) out_valid <= 1'b0;
        else     out_valid <= in_valid;
        out_data <= x;
    end
endmodule
