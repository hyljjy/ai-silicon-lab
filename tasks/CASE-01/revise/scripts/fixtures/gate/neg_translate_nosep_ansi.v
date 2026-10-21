// unrecognized (RV-06): ANSI port dbg hidden from Yosys by translate comments without a separator (lines 10, 12, 13, 15)
module dot4sat (
    input  wire        clk,
    input  wire        rst,
    input  wire        in_valid,
    input  wire [63:0] in_a,
    input  wire [63:0] in_b,
    output reg         out_valid,
    output reg  [31:0] out_data
//synopsystranslate_off
    , output wire dbg
//synopsystranslate_on
/*synthesistranslate_off*/
    , output wire dbg2
/*synthesistranslate_on*/
);
    always @(posedge clk) begin
        if (rst) out_valid <= 1'b0;
        else     out_valid <= in_valid;
        out_data <= in_a[31:0] ^ in_b[31:0];
    end
endmodule
