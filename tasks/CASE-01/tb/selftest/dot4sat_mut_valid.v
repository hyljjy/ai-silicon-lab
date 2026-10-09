// SELF-TEST MUTANT (spec 3.6, valid misalignment): out_valid is one cycle late, data unchanged (L stays 1
// in the cfg). Must make the TB fail.
module dot4sat (
    input  wire        clk,
    input  wire        rst,
    input  wire        in_valid,
    input  wire [63:0] in_a,
    input  wire [63:0] in_b,
    output reg         out_valid,
    output reg  [31:0] out_data
);
    wire signed [31:0] p0 = $signed(in_a[15:0])  * $signed(in_b[15:0]);
    wire signed [31:0] p1 = $signed(in_a[31:16]) * $signed(in_b[31:16]);
    wire signed [31:0] p2 = $signed(in_a[47:32]) * $signed(in_b[47:32]);
    wire signed [31:0] p3 = $signed(in_a[63:48]) * $signed(in_b[63:48]);
    wire signed [33:0] sum = p0 + p1 + p2 + p3;
    wire [31:0] sat = (sum > 34'sd2147483647) ? 32'h7FFF_FFFF :
                      (sum < -34'sd2147483648) ? 32'h8000_0000 : sum[31:0];
    reg v1;
    always @(posedge clk) begin
        if (rst) begin v1 <= 1'b0; out_valid <= 1'b0; end
        else     begin v1 <= in_valid; out_valid <= v1; end   // BUG: one extra cycle on valid only
        out_data <= sat;
    end
endmodule
