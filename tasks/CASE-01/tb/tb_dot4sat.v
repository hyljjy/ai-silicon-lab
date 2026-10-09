`timescale 1ns/1ps
// CASE-01 testbench (spec 2.1-2.5, 3.5). Must be the FIRST file on the iverilog command line so that
// a netlist without `timescale inherits 1ns/1ps.
// plusargs (all required except WATCHDOG; integers must be plain decimal):
//   +VEC=<vectors.txt> +NVEC=<lines in the file> +L=<1..LMAX> +LMAX=<1..3> +EXP=<expected checked> [+WATCHDOG=<cycles>]
// Vector file: exactly one line per rising edge, 12 space-separated fields:
//   rst valid a0 a1 a2 a3 b0 b1 b2 b3 y tag   (rst/valid: 0|1, a/b: 4 lowercase hex, y: 8 lowercase hex, tag <= 64 chars)
// On F_n the TB first checks O_(n+1), then drives the inputs sampled at R_(n+1).
module tb;
  localparam integer MAXC = 1 << 20;   // max timeline length (vectors + drain)
  localparam integer LB = 512;         // max line length in bytes, newline included
  localparam integer TB_ = 80;         // max token length in bytes

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

  integer L, LMAX, EXP, NVEC, WATCHDOG, fd, n_total, checked, drain_left, line_no, cnt;
  reg [8*LB-1:0] line;
  reg [8*TB_-1:0] t0, t1, t2, t3, t4, t5, t6, t7, t8, t9, t10, t11, t12;
  reg [8*256-1:0] vecfile;
  reg eof;

  task automatic fail(input string msg);
    begin
      $display("SIM FAIL %s", msg);
      $fatal(1, "%s", msg);
    end
  endtask

  function automatic integer tok_len(input [8*TB_-1:0] t);   // tokens are right-aligned, zero-padded
    integer i;
    begin
      tok_len = 0;
      for (i = 0; i < TB_; i = i + 1)
        if (t[8*i +: 8] != 8'h00) tok_len = i + 1;
    end
  endfunction

  function automatic bit is_hex(input [8*TB_-1:0] t, input integer n);   // exactly n chars of [0-9a-f]
    integer i;
    reg [7:0] c;
    begin
      is_hex = (tok_len(t) == n);
      for (i = 0; i < n; i = i + 1) begin
        c = t[8*i +: 8];
        if (!((c >= "0" && c <= "9") || (c >= "a" && c <= "f"))) is_hex = 1'b0;
      end
    end
  endfunction

  function automatic integer to_uint(input [8*TB_-1:0] t);   // plain decimal, 1..9 digits; -1 if malformed
    integer i, n;
    reg [7:0] c;
    begin
      n = tok_len(t);
      to_uint = (n >= 1 && n <= 9) ? 0 : -1;
      for (i = n - 1; i >= 0 && to_uint >= 0; i = i - 1) begin
        c = t[8*i +: 8];
        if (c >= "0" && c <= "9") to_uint = to_uint * 10 + (c - "0");
        else to_uint = -1;
      end
    end
  endfunction

  function automatic integer plus_uint(input string name);   // required decimal plusarg; -1 if missing/malformed
    reg [8*TB_-1:0] s;
    begin
      s = 0;
      if (!$value$plusargs({name, "=%s"}, s)) plus_uint = -1;
      else plus_uint = to_uint(s);
    end
  endfunction

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

  task automatic drive(input bit rst_v, input bit valid_v, input [63:0] a, input [63:0] b, input [31:0] y);
    begin
      if (n_total >= MAXC) fail("timeline longer than MAXC");
      rst = rst_v; in_valid = valid_v; in_a = a; in_b = b;
      h_rst[n_total] = rst_v; h_valid[n_total] = valid_v; h_y[n_total] = y;
      n_total = n_total + 1;
    end
  endtask

  task automatic parse_and_drive;
    reg [15:0] a0, a1, a2, a3, b0, b1, b2, b3;
    reg [31:0] y;
    bit r, v;
    begin
      t0 = 0; t1 = 0; t2 = 0; t3 = 0; t4 = 0; t5 = 0; t6 = 0; t7 = 0; t8 = 0; t9 = 0; t10 = 0; t11 = 0; t12 = 0;
      if (line[7:0] != 8'h0A) fail($sformatf("line %0d: missing newline or longer than %0d bytes", line_no, LB - 1));
      cnt = $sscanf(line, "%s %s %s %s %s %s %s %s %s %s %s %s %s",
                    t0, t1, t2, t3, t4, t5, t6, t7, t8, t9, t10, t11, t12);
      if (cnt != 12) fail($sformatf("line %0d: %0d fields, need exactly 12", line_no, cnt < 0 ? 0 : cnt));
      if (t0 != "0" && t0 != "1") fail($sformatf("line %0d: bad rst field", line_no));
      if (t1 != "0" && t1 != "1") fail($sformatf("line %0d: bad valid field", line_no));
      if (!(is_hex(t2, 4) && is_hex(t3, 4) && is_hex(t4, 4) && is_hex(t5, 4) && is_hex(t6, 4) &&
            is_hex(t7, 4) && is_hex(t8, 4) && is_hex(t9, 4) && is_hex(t10, 8)))
        fail($sformatf("line %0d: operand/expected field is not lowercase hex of the exact width", line_no));
      if (tok_len(t11) == 0 || tok_len(t11) > 64) fail($sformatf("line %0d: tag missing or longer than 64", line_no));
      r = (t0 == "1"); v = (t1 == "1");
      if (line_no <= 4 && !r) fail("first 4 vectors must hold rst=1 (spec 2.4)");
      cnt = $sscanf(t2, "%h", a0); cnt = $sscanf(t3, "%h", a1); cnt = $sscanf(t4, "%h", a2);
      cnt = $sscanf(t5, "%h", a3); cnt = $sscanf(t6, "%h", b0); cnt = $sscanf(t7, "%h", b1);
      cnt = $sscanf(t8, "%h", b2); cnt = $sscanf(t9, "%h", b3); cnt = $sscanf(t10, "%h", y);
      if (^{a0, a1, a2, a3, b0, b1, b2, b3, y} === 1'bx) fail($sformatf("line %0d: unknown value", line_no));
      drive(r, v, {a3, a2, a1, a0}, {b3, b2, b1, b0}, y);
    end
  endtask

  task automatic drive_next;
    begin
      if (!eof) begin
        line = 0;
        if ($fgets(line, fd) == 0) begin
          eof = 1'b1;
          if (line_no != NVEC) fail($sformatf("vector file has %0d lines, manifest says %0d", line_no, NVEC));
        end else begin
          line_no = line_no + 1;
          parse_and_drive();
        end
      end
      if (eof) begin
        drive(1'b0, 1'b0, 64'd0, 64'd0, 32'd0);    // drain cycle (spec 3.5)
        drain_left = drain_left - 1;
      end
    end
  endtask

  initial begin
    eof = 1'b0; checked = 0; n_total = 0; line_no = 0;
    vecfile = 0;
    if (!$value$plusargs("VEC=%s", vecfile)) fail("missing +VEC");
    L = plus_uint("L"); LMAX = plus_uint("LMAX"); EXP = plus_uint("EXP"); NVEC = plus_uint("NVEC");
    if (L < 0) fail("missing or malformed +L");
    if (LMAX < 0) fail("missing or malformed +LMAX");
    if (EXP < 0) fail("missing or malformed +EXP");
    if (NVEC < 0) fail("missing or malformed +NVEC");
    if ($test$plusargs("WATCHDOG=")) begin
      WATCHDOG = plus_uint("WATCHDOG");
      if (WATCHDOG <= 0) fail("malformed +WATCHDOG");
    end else WATCHDOG = MAXC;
    if (LMAX < 1 || LMAX > 3) fail($sformatf("LMAX=%0d outside 1..3", LMAX));
    if (L < 1 || L > LMAX) fail($sformatf("L=%0d outside 1..LMAX=%0d", L, LMAX));
    if (EXP <= 0) fail("EXP must be > 0");
    if (NVEC < 5) fail("NVEC must be >= 5");
    drain_left = LMAX + 1;
    fd = $fopen(vecfile, "r");
    if (fd == 0) fail("cannot open vector file");
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
