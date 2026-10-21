// legal: always @* and always @( * ) combinational blocks with a default assignment
module dot4sat (
    input  wire        clk,
    input  wire        rst,
    input  wire        in_valid,
    input  wire [63:0] in_a,
    input  wire [63:0] in_b,
    output reg         out_valid,
    output reg  [31:0] out_data
);
    reg [31:0] a, b;
    always @* begin
        a = in_a[31:0];
    end
    always @( * ) begin
        b = 32'd0;
        if (in_valid) b = in_b[31:0];
    end
    always @ ( posedge clk ) begin
        if (rst) out_valid <= 1'b0;
        else     out_valid <= in_valid;
        out_data <= a ^ b;
    end
endmodule
