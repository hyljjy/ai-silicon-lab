// TC001 baseline: 4 路点积 + 饱和累加器，单周期实现。
// 功能正确，但乘法、加法树、累加、饱和全部在同一拍内完成。
module dotacc (
    input  wire        clk,
    input  wire        rst_n,
    input  wire        in_valid,
    output wire        in_ready,
    input  wire        in_clear,
    input  wire [63:0] in_a,
    input  wire [63:0] in_b,
    output reg         out_valid,
    input  wire        out_ready,
    output wire [31:0] out_data
);

    wire signed [15:0] a0 = in_a[15:0];
    wire signed [15:0] a1 = in_a[31:16];
    wire signed [15:0] a2 = in_a[47:32];
    wire signed [15:0] a3 = in_a[63:48];
    wire signed [15:0] b0 = in_b[15:0];
    wire signed [15:0] b1 = in_b[31:16];
    wire signed [15:0] b2 = in_b[47:32];
    wire signed [15:0] b3 = in_b[63:48];

    wire signed [31:0] p0 = a0 * b0;
    wire signed [31:0] p1 = a1 * b1;
    wire signed [31:0] p2 = a2 * b2;
    wire signed [31:0] p3 = a3 * b3;

    wire signed [33:0] sum = p0 + p1 + p2 + p3;

    reg  signed [31:0] acc;
    wire signed [31:0] base  = in_clear ? 32'sd0 : acc;
    wire signed [34:0] total = base + sum;

    wire        in_range = (total[34:31] == 4'b0000) || (total[34:31] == 4'b1111);
    wire [31:0] sat      = in_range  ? total[31:0] :
                           total[34] ? 32'h8000_0000 : 32'h7FFF_FFFF;

    wire fire = in_valid && in_ready;

    assign in_ready = !out_valid || out_ready;
    assign out_data = acc;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            acc       <= 32'sd0;
            out_valid <= 1'b0;
        end else begin
            if (fire) begin
                acc       <= sat;
                out_valid <= 1'b1;
            end else if (out_ready) begin
                out_valid <= 1'b0;
            end
        end
    end

endmodule
