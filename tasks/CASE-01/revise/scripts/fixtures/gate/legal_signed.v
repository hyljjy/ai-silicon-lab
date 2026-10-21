// legal: $signed / $unsigned are not in the lint list
module dot4sat (
    input  wire        clk,
    input  wire        rst,
    input  wire        in_valid,
    input  wire [63:0] in_a,
    input  wire [63:0] in_b,
    output reg         out_valid,
    output reg  [31:0] out_data
);
    wire signed [31:0] p0 = $signed(in_a[15:0]) * $signed(in_b[15:0]);
    wire [31:0] u = $unsigned(p0);
    always @(posedge clk) begin
        if (rst) out_valid <= 1'b0;
        else     out_valid <= in_valid;
        out_data <= u;
    end
endmodule
