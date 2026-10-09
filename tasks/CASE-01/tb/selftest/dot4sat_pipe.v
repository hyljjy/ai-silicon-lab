// SELF-TEST FIXTURE: correct design with latency L = 2 (default) or L = 3 (compile with -DEXTRA2).
// Used only to exercise the TB's L handling and in-flight reset cancellation (spec 3.6). Explicit registers,
// no arrays (arrays make Yosys print "Replacing memory ..." warnings).
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
    reg        v0;
    reg [31:0] d0;
`ifdef EXTRA2
    reg        v1;
    reg [31:0] d1;
`endif
    always @(posedge clk) begin
        v0 <= rst ? 1'b0 : in_valid;
        d0 <= sat;
`ifdef EXTRA2
        v1 <= rst ? 1'b0 : v0;
        d1 <= d0;
        out_valid <= rst ? 1'b0 : v1;
        out_data  <= d1;
`else
        out_valid <= rst ? 1'b0 : v0;
        out_data  <= d0;
`endif
    end
endmodule
