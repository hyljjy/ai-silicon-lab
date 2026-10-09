`timescale 1ns/1ps
// CASE-01 testbench (spec 2.1-2.5, 3.5). Must be the FIRST file on the iverilog command line so that
// a netlist without `timescale inherits 1ns/1ps.
// plusargs: +VEC=<vectors.txt> +L=<1..LMAX> +LMAX=<1..3> +EXP=<expected checked count> [+WATCHDOG=<cycles>]
// On F_n the TB first checks O_(n+1), then drives the inputs sampled at R_(n+1).
module tb;
  localparam integer MAXC = 1 << 20;   // max timeline length (vectors + drain)

  reg clk = 1'b0;
  always #5 clk = ~clk;                // 10 ns period, 5 ns half period (spec 3.5: > 1 ns)

  reg         rst = 1'b1;
  reg         in_valid = 1'b0;
  reg  [63:0] in_a = 64'd0;
  reg  [63:0] in_b = 64'd0;
  wire        out_valid;
  wire [31:0] out_data;

  dot4sat dut (.clk(clk), .rst(rst), .in_valid(in_valid), .in_a(in_a), .in_b(in_b),
               .out_valid(out_valid), .out_data(out_data));

  reg        h_rst   [0:MAXC-1];       // rst sampled at R_n
  reg        h_valid [0:MAXC-1];       // in_valid sampled at R_n
  reg [31:0] h_y     [0:MAXC-1];       // reference f(a[n], b[n]) from the vector file

  integer L, LMAX, EXP, WATCHDOG, fd, n_total, checked, drain_left, line_no;
  integer f_rst, f_valid, r;
  reg [15:0] a0, a1, a2, a3, b0, b1, b2, b3;
  reg [31:0] f_y;
  reg [8*64-1:0] f_tag;
  string vecfile;
  reg eof;

  task automatic fail(input string msg);
    begin
      $display("SIM FAIL %s", msg);
      $fatal(1, "%s", msg);
    end
  endtask

  // spec 2.3: O_k.valid = valid[k-L] AND rst[j] == 0 for all j in [k-L, k-1]
  function automatic bit expected_valid(input integer k);
    integer n, j;
    begin
      n = k - L;
      expected_valid = 1'b0;
      if (n >= 0) begin
        expected_valid = h_valid[n];
        for (j = n; j < k; j = j + 1)
          if (h_rst[j]) expected_valid = 1'b0;
      end
    end
  endfunction

  task automatic check_obs(input integer k);
    bit ev;
    begin
      ev = expected_valid(k);
      if (out_valid !== ev)
        fail($sformatf("VALID MISMATCH at O_%0d: got %b expected %b", k, out_valid, ev));
      if (ev) begin
        if (out_data !== h_y[k-L])
          fail($sformatf("DATA MISMATCH at O_%0d (input edge %0d): got %h expected %h",
                         k, k - L, out_data, h_y[k-L]));
        checked = checked + 1;
      end
    end
  endtask

  task automatic drive(input integer rst_v, input integer valid_v, input [63:0] a, input [63:0] b,
                       input [31:0] y);
    begin
      if (n_total >= MAXC) fail("timeline longer than MAXC");
      rst = rst_v[0]; in_valid = valid_v[0]; in_a = a; in_b = b;
      h_rst[n_total] = rst_v[0]; h_valid[n_total] = valid_v[0]; h_y[n_total] = y;
      n_total = n_total + 1;
    end
  endtask

  task automatic drive_next;
    begin
      if (!eof) begin
        r = $fscanf(fd, "%d %d %h %h %h %h %h %h %h %h %h %s\n",
                    f_rst, f_valid, a0, a1, a2, a3, b0, b1, b2, b3, f_y, f_tag);
        if (r == -1) eof = 1'b1;
        else begin
          line_no = line_no + 1;
          if (r != 12) fail($sformatf("vector parse error at line %0d (%0d fields)", line_no, r));
          if (f_rst !== 0 && f_rst !== 1) fail($sformatf("bad rst at line %0d", line_no));
          if (f_valid !== 0 && f_valid !== 1) fail($sformatf("bad valid at line %0d", line_no));
          if (line_no <= 4 && f_rst != 1) fail("first 4 vectors must hold rst=1 (spec 2.4)");
          drive(f_rst, f_valid, {a3, a2, a1, a0}, {b3, b2, b1, b0}, f_y);
        end
      end
      if (eof) begin
        if (line_no == 0) fail("empty vector file");
        drive(0, 0, 64'd0, 64'd0, 32'd0);           // drain cycle (spec 3.5)
        drain_left = drain_left - 1;
      end
    end
  endtask

  initial begin
    eof = 1'b0; checked = 0; n_total = 0; line_no = 0;
    if (!$value$plusargs("VEC=%s", vecfile)) fail("missing +VEC");
    if (!$value$plusargs("L=%d", L)) fail("missing +L");
    if (!$value$plusargs("LMAX=%d", LMAX)) fail("missing +LMAX");
    if (!$value$plusargs("EXP=%d", EXP)) fail("missing +EXP");
    if (!$value$plusargs("WATCHDOG=%d", WATCHDOG)) WATCHDOG = MAXC;
    if (LMAX < 1 || LMAX > 3) fail($sformatf("LMAX=%0d outside 1..3", LMAX));
    if (L < 1 || L > LMAX) fail($sformatf("L=%0d outside 1..LMAX=%0d", L, LMAX));
    if (EXP <= 0) fail("EXP must be > 0");
    drain_left = LMAX + 1;
    fd = $fopen(vecfile, "r");
    if (fd == 0) fail({"cannot open vector file ", vecfile});
    drive_next();                                    // inputs for R_0, before the first rising edge
    forever begin
      @(negedge clk);                                // F_(n_total-1)
      check_obs(n_total);                            // O_(n_total)
      if (eof && drain_left == 0) begin
        if (checked == 0) fail("no transaction checked");
        if (checked != EXP) fail($sformatf("checked %0d != expected %0d", checked, EXP));
        $display("SIM PASS checked=%0d", checked);
        $finish;
      end
      drive_next();
    end
  end

  initial begin
    #1;
    #(10.0 * (WATCHDOG + 16));
    fail("watchdog timeout");
  end
endmodule
