module mac (input clk, input rst, input [7:0] a, b, output reg [17:0] acc);
  reg [7:0] ra, rb;
  always @(posedge clk) begin
    if (rst) begin ra <= 0; rb <= 0; acc <= 0; end
    else begin ra <= a; rb <= b; acc <= acc + ra * rb; end
  end
endmodule
