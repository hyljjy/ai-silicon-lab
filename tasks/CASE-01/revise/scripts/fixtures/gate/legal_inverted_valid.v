// legal: inverted valid encoding (invalid1 = 1 means no transaction), wire with assignment
module dot4sat (
    input  wire        clk,
    input  wire        rst,
    input  wire        in_valid,
    input  wire [63:0] in_a,
    input  wire [63:0] in_b,
    output reg         out_valid,
    output reg  [31:0] out_data
);
    reg invalid1;
    reg [31:0] d1;
    wire [31:0] x = in_a[31:0] ^ in_b[31:0];
    always @(posedge clk) begin
        invalid1  <= rst | ~in_valid;
        out_valid <= ~rst & ~invalid1;
        d1 <= x;
        out_data <= d1;
    end
endmodule
