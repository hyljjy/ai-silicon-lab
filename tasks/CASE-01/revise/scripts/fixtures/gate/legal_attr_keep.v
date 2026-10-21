// legal: attributes (* keep *) are one token and do not take part in the rules
module dot4sat (
    input  wire        clk,
    input  wire        rst,
    input  wire        in_valid,
    input  wire [63:0] in_a,
    input  wire [63:0] in_b,
    output reg         out_valid,
    output reg  [31:0] out_data
);
    (* keep *) wire [31:0] x = in_a[31:0] ^ in_b[31:0];
    (* keep = "parameter clk negedge" *) reg [31:0] y;
    always @(*) begin
        y = x;
    end
    (* full_case *)
    always @(posedge clk) begin
        if (rst) out_valid <= 1'b0;
        else     out_valid <= in_valid;
        out_data <= y;
    end
endmodule
