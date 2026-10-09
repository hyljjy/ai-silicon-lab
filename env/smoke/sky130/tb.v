module tb;
  reg clk = 0, rst = 1; reg [7:0] a, b; wire [17:0] acc;
  mac dut(.clk(clk), .rst(rst), .a(a), .b(b), .acc(acc));
  always #5 clk = ~clk;
  initial begin
    a = 3; b = 4; #12 rst = 0;
    #40;
    if (acc == 12*3) $display("SIM PASS acc=%0d", acc); else $display("SIM FAIL acc=%0d", acc);
    $finish;
  end
endmodule
