// V1 hit: sat is not assigned on the reachable path where sum is in range
// L = 2. Author veto contrast sample (protocol 6.3 part 3, 7.3); expected judgment in README.md.
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
    reg  signed [31:0] r0, r1, r2, r3;
    wire signed [33:0] sum = r0 + r1 + r2 + r3;
    reg         [31:0] sat;
    always @* begin
        if (sum > 34'sd2147483647)       sat = 32'h7FFF_FFFF;
        else if (sum < -34'sd2147483648) sat = 32'h8000_0000;
    end
    reg v1;
    always @(posedge clk) begin
        if (rst) begin
            v1        <= 1'b0;
            out_valid <= 1'b0;
        end else begin
            v1        <= in_valid;
            out_valid <= v1;
        end
    end
    always @(posedge clk) begin
        r0 <= p0;
        r1 <= p1;
        r2 <= p2;
        r3 <= p3;
        out_data <= sat;
    end
endmodule
