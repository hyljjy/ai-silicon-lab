下面是同一个数字电路模块综合后的两次静态时序分析记录（R1 和 R2），以及接口时序的意图说明和分析条件。请阅读全部材料，然后按要求作答。每个文件的每一行前面都标了行号。

=== 文件：intent.md（共 5 行）===
   1| # 接口时序的意图说明（intent.md）
   2| 
   3| - 全部 130 个非时钟输入（`in_a[63:0]`、`in_b[63:0]`、`in_valid`、`rst`）来自同一个上游时钟域的寄存器输出，相对 `clk` 上升沿最晚在 0.2·T 到达（max），最早在 0 到达（min），rise 和 fall 相同，由 `sky130_fd_sc_hd__buf_2` 驱动；T = 27.91 ns，所以 max = 5.5820 ns。
   4| - 全部 33 个输出相对 `clk` 上升沿，外部要求 max = 0.2·T、min = 0，每位负载 C_load = 0.0024 pF。
   5| - 这份意图说明表达的是要求。它不能证明某次运行实际施加了这些约束；是否施加，只能由该次运行的展开约束和覆盖检查证明。
=== 文件结束：intent.md ===

=== 文件：values.txt（共 2 行）===
   1| T_ns = 27.91
   2| C_load_pF = 0.0024
=== 文件结束：values.txt ===

=== 文件：summary_R1.tsv（共 51 行）===
   1| TOPO	in2reg	130
   2| TOPO	reg2reg	0
   3| TOPO	reg2out	33
   4| WS	tt_025C_1v80	max	11.191043075655372
   5| WS	tt_025C_1v80	min	0.09305387279663745
   6| CAT	tt_025C_1v80	in2reg	max	11.191043	in_a[34]	_12026_/D
   7| CAT	tt_025C_1v80	in2reg	min	0.093054	rst	_12058_/D
   8| CAT	tt_025C_1v80	reg2reg	max	NONE
   9| CAT	tt_025C_1v80	reg2reg	min	NONE
  10| CAT	tt_025C_1v80	reg2out	max	22.047794	_12026_/Q	out_data[0]
  11| CAT	tt_025C_1v80	reg2out	min	0.272520	_12026_/Q	out_data[0]
  12| WS	tt_100C_1v80	max	11.32117898139033
  13| WS	tt_100C_1v80	min	0.08983023607005908
  14| CAT	tt_100C_1v80	in2reg	max	11.321179	in_a[34]	_12026_/D
  15| CAT	tt_100C_1v80	in2reg	min	0.089830	rst	_12058_/D
  16| CAT	tt_100C_1v80	reg2reg	max	NONE
  17| CAT	tt_100C_1v80	reg2reg	min	NONE
  18| CAT	tt_100C_1v80	reg2out	max	22.045441	_12026_/Q	out_data[0]
  19| CAT	tt_100C_1v80	reg2out	min	0.278449	_12026_/Q	out_data[0]
  20| WS	ss_100C_1v60	max	-0.6799521138591476
  21| WS	ss_100C_1v60	min	0.18567888030452087
  22| CAT	ss_100C_1v60	in2reg	max	-0.679952	in_a[34]	_12026_/D
  23| CAT	ss_100C_1v60	in2reg	min	0.185679	rst	_12058_/D
  24| CAT	ss_100C_1v60	reg2reg	max	NONE
  25| CAT	ss_100C_1v60	reg2reg	min	NONE
  26| CAT	ss_100C_1v60	reg2out	max	21.742086	_12026_/Q	out_data[0]
  27| CAT	ss_100C_1v60	reg2out	min	0.538051	_12026_/Q	out_data[0]
  28| WS	ss_n40C_1v60	max	-4.172594832200332
  29| WS	ss_n40C_1v60	min	0.18500412836443383
  30| CAT	ss_n40C_1v60	in2reg	max	-4.172595	in_a[34]	_12026_/D
  31| CAT	ss_n40C_1v60	in2reg	min	0.185004	rst	_12058_/D
  32| CAT	ss_n40C_1v60	reg2reg	max	NONE
  33| CAT	ss_n40C_1v60	reg2reg	min	NONE
  34| CAT	ss_n40C_1v60	reg2out	max	21.692432	_12026_/Q	out_data[0]
  35| CAT	ss_n40C_1v60	reg2out	min	0.548442	_12026_/Q	out_data[0]
  36| WS	ff_n40C_1v95	max	15.881204356648498
  37| WS	ff_n40C_1v95	min	0.06347266641938298
  38| CAT	ff_n40C_1v95	in2reg	max	15.881205	in_a[3]	_12026_/D
  39| CAT	ff_n40C_1v95	in2reg	min	0.063473	rst	_12058_/D
  40| CAT	ff_n40C_1v95	reg2reg	max	NONE
  41| CAT	ff_n40C_1v95	reg2reg	min	NONE
  42| CAT	ff_n40C_1v95	reg2out	max	22.154276	_12026_/Q	out_data[0]
  43| CAT	ff_n40C_1v95	reg2out	min	0.173251	_12026_/Q	out_data[0]
  44| WS	ff_100C_1v95	max	15.90284571263497
  45| WS	ff_100C_1v95	min	0.059112952317363035
  46| CAT	ff_100C_1v95	in2reg	max	15.902845	in_a[3]	_12026_/D
  47| CAT	ff_100C_1v95	in2reg	min	0.059113	rst	_12058_/D
  48| CAT	ff_100C_1v95	reg2reg	max	NONE
  49| CAT	ff_100C_1v95	reg2reg	min	NONE
  50| CAT	ff_100C_1v95	reg2out	max	22.143078	_12026_/Q	out_data[0]
  51| CAT	ff_100C_1v95	reg2out	min	0.179844	_12026_/Q	out_data[0]
=== 文件结束：summary_R1.tsv ===

=== 文件：summary_R2.tsv（共 51 行）===
   1| TOPO	in2reg	130
   2| TOPO	reg2reg	0
   3| TOPO	reg2out	33
   4| WS	tt_025C_1v80	max	11.185458209594348
   5| WS	tt_025C_1v80	min	0.09305387279663745
   6| CAT	tt_025C_1v80	in2reg	max	11.185458	in_b[35]	_12026_/D
   7| CAT	tt_025C_1v80	in2reg	min	0.093054	rst	_12058_/D
   8| CAT	tt_025C_1v80	reg2reg	max	NONE
   9| CAT	tt_025C_1v80	reg2reg	min	NONE
  10| CAT	tt_025C_1v80	reg2out	max	22.047794	_12026_/Q	out_data[0]
  11| CAT	tt_025C_1v80	reg2out	min	0.272520	_12026_/Q	out_data[0]
  12| WS	tt_100C_1v80	max	11.317221258240215
  13| WS	tt_100C_1v80	min	0.08983023607005908
  14| CAT	tt_100C_1v80	in2reg	max	11.317222	in_b[35]	_12026_/D
  15| CAT	tt_100C_1v80	in2reg	min	0.089830	rst	_12058_/D
  16| CAT	tt_100C_1v80	reg2reg	max	NONE
  17| CAT	tt_100C_1v80	reg2reg	min	NONE
  18| CAT	tt_100C_1v80	reg2out	max	22.045441	_12026_/Q	out_data[0]
  19| CAT	tt_100C_1v80	reg2out	min	0.278449	_12026_/Q	out_data[0]
  20| WS	ss_100C_1v60	max	-0.687277809672019
  21| WS	ss_100C_1v60	min	0.18567888030452087
  22| CAT	ss_100C_1v60	in2reg	max	-0.687278	in_b[35]	_12026_/D
  23| CAT	ss_100C_1v60	in2reg	min	0.185679	rst	_12058_/D
  24| CAT	ss_100C_1v60	reg2reg	max	NONE
  25| CAT	ss_100C_1v60	reg2reg	min	NONE
  26| CAT	ss_100C_1v60	reg2out	max	21.742086	_12026_/Q	out_data[0]
  27| CAT	ss_100C_1v60	reg2out	min	0.538051	_12026_/Q	out_data[0]
  28| WS	ss_n40C_1v60	max	-4.189726018044011
  29| WS	ss_n40C_1v60	min	0.18500412836443383
  30| CAT	ss_n40C_1v60	in2reg	max	-4.189726	in_b[2]	_12026_/D
  31| CAT	ss_n40C_1v60	in2reg	min	0.185004	rst	_12058_/D
  32| CAT	ss_n40C_1v60	reg2reg	max	NONE
  33| CAT	ss_n40C_1v60	reg2reg	min	NONE
  34| CAT	ss_n40C_1v60	reg2out	max	21.692432	_12026_/Q	out_data[0]
  35| CAT	ss_n40C_1v60	reg2out	min	0.548442	_12026_/Q	out_data[0]
  36| WS	ff_n40C_1v95	max	15.871505448031069
  37| WS	ff_n40C_1v95	min	0.06347266641938298
  38| CAT	ff_n40C_1v95	in2reg	max	15.871506	in_b[2]	_12026_/D
  39| CAT	ff_n40C_1v95	in2reg	min	0.063473	rst	_12058_/D
  40| CAT	ff_n40C_1v95	reg2reg	max	NONE
  41| CAT	ff_n40C_1v95	reg2reg	min	NONE
  42| CAT	ff_n40C_1v95	reg2out	max	22.154276	_12026_/Q	out_data[0]
  43| CAT	ff_n40C_1v95	reg2out	min	0.173251	_12026_/Q	out_data[0]
  44| WS	ff_100C_1v95	max	15.894228605363333
  45| WS	ff_100C_1v95	min	0.059112952317363035
  46| CAT	ff_100C_1v95	in2reg	max	15.894229	in_b[2]	_12026_/D
  47| CAT	ff_100C_1v95	in2reg	min	0.059113	rst	_12058_/D
  48| CAT	ff_100C_1v95	reg2reg	max	NONE
  49| CAT	ff_100C_1v95	reg2reg	min	NONE
  50| CAT	ff_100C_1v95	reg2out	max	22.143078	_12026_/Q	out_data[0]
  51| CAT	ff_100C_1v95	reg2out	min	0.179844	_12026_/Q	out_data[0]
=== 文件结束：summary_R2.tsv ===

=== 文件：path_R1.rpt（共 102 行）===
   1| Startpoint: in_a[34] (input port clocked by clk)
   2| Endpoint: _12026_ (rising edge-triggered flip-flop clocked by clk)
   3| Path Group: clk
   4| Path Type: max
   5| Corner: ss_n40C_1v60
   6| 
   7| Fanout       Cap      Slew     Delay      Time   Description
   8| -------------------------------------------------------------------------------------
   9|                     0.0000    0.0000    0.0000   clock clk (rise edge)
  10|                               0.0000    0.0000   clock network delay (ideal)
  11|                               5.5820    5.5820 ^ input external delay
  12|     17    0.0365    0.3844    0.2730    5.8550 ^ in_a[34] (in)
  13|                     0.3844    0.0000    5.8550 ^ _10564_/A (sky130_fd_sc_hd__and2_0)
  14|      2    0.0050    0.1742    0.4006    6.2556 ^ _10564_/X (sky130_fd_sc_hd__and2_0)
  15|                     0.1742    0.0000    6.2556 ^ _10854_/A (sky130_fd_sc_hd__xnor3_1)
  16|      2    0.0073    0.1346    1.0188    7.2744 v _10854_/X (sky130_fd_sc_hd__xnor3_1)
  17|                     0.1346    0.0000    7.2744 v _10985_/B (sky130_fd_sc_hd__xor3_1)
  18|      2    0.0067    0.1357    0.9736    8.2480 v _10985_/X (sky130_fd_sc_hd__xor3_1)
  19|                     0.1357    0.0000    8.2480 v _10986_/B (sky130_fd_sc_hd__xor2_1)
  20|      2    0.0077    0.4310    0.4475    8.6955 ^ _10986_/X (sky130_fd_sc_hd__xor2_1)
  21|                     0.4310    0.0000    8.6955 ^ _11069_/B (sky130_fd_sc_hd__xor2_1)
  22|      1    0.0023    0.2113    0.4045    9.1000 ^ _11069_/X (sky130_fd_sc_hd__xor2_1)
  23|                     0.2113    0.0000    9.1000 ^ _11071_/C (sky130_fd_sc_hd__nand3_1)
  24|      2    0.0073    0.2040    0.2403    9.3403 v _11071_/Y (sky130_fd_sc_hd__nand3_1)
  25|                     0.2040    0.0000    9.3403 v _11073_/B (sky130_fd_sc_hd__xor3_1)
  26|      2    0.0055    0.1259    0.9973   10.3376 v _11073_/X (sky130_fd_sc_hd__xor3_1)
  27|                     0.1259    0.0000   10.3376 v _11149_/A (sky130_fd_sc_hd__xnor2_1)
  28|      2    0.0078    0.4964    0.5470   10.8846 ^ _11149_/Y (sky130_fd_sc_hd__xnor2_1)
  29|                     0.4964    0.0000   10.8846 ^ _11228_/B (sky130_fd_sc_hd__xnor3_1)
  30|      2    0.0073    0.1346    0.9809   11.8655 v _11228_/X (sky130_fd_sc_hd__xnor3_1)
  31|                     0.1346    0.0000   11.8655 v _11302_/B (sky130_fd_sc_hd__xor3_1)
  32|      2    0.0073    0.1401    0.9794   12.8449 v _11302_/X (sky130_fd_sc_hd__xor3_1)
  33|                     0.1401    0.0000   12.8449 v _11306_/B (sky130_fd_sc_hd__maj3_1)
  34|      2    0.0073    0.1599    0.9433   13.7882 v _11306_/X (sky130_fd_sc_hd__maj3_1)
  35|                     0.1599    0.0000   13.7882 v _11338_/B (sky130_fd_sc_hd__xor3_1)
  36|      2    0.0061    0.1307    0.9799   14.7681 v _11338_/X (sky130_fd_sc_hd__xor3_1)
  37|                     0.1307    0.0000   14.7681 v _11340_/B (sky130_fd_sc_hd__xor2_1)
  38|      2    0.0065    0.3820    0.4077   15.1758 ^ _11340_/X (sky130_fd_sc_hd__xor2_1)
  39|                     0.3820    0.0000   15.1758 ^ _11416_/A1 (sky130_fd_sc_hd__a21oi_1)
  40|      2    0.0067    0.1299    0.2608   15.4366 v _11416_/Y (sky130_fd_sc_hd__a21oi_1)
  41|                     0.1299    0.0000   15.4366 v _11418_/C (sky130_fd_sc_hd__maj3_1)
  42|      2    0.0055    0.1444    0.9285   16.3652 v _11418_/X (sky130_fd_sc_hd__maj3_1)
  43|                     0.1444    0.0000   16.3652 v _11420_/A1 (sky130_fd_sc_hd__o21ai_0)
  44|      2    0.0063    0.4984    0.5449   16.9101 ^ _11420_/Y (sky130_fd_sc_hd__o21ai_0)
  45|                     0.4984    0.0000   16.9101 ^ _11421_/C (sky130_fd_sc_hd__maj3_1)
  46|      2    0.0065    0.1750    0.5349   17.4450 ^ _11421_/X (sky130_fd_sc_hd__maj3_1)
  47|                     0.1750    0.0000   17.4450 ^ _11422_/A2 (sky130_fd_sc_hd__a21oi_1)
  48|      2    0.0067    0.1381    0.1799   17.6249 v _11422_/Y (sky130_fd_sc_hd__a21oi_1)
  49|                     0.1381    0.0000   17.6249 v _11423_/C (sky130_fd_sc_hd__maj3_1)
  50|      2    0.0067    0.1552    0.9453   18.5701 v _11423_/X (sky130_fd_sc_hd__maj3_1)
  51|                     0.1552    0.0000   18.5701 v _11424_/C (sky130_fd_sc_hd__maj3_1)
  52|      2    0.0056    0.1456    0.9406   19.5107 v _11424_/X (sky130_fd_sc_hd__maj3_1)
  53|                     0.1456    0.0000   19.5107 v _11426_/A2 (sky130_fd_sc_hd__o21ai_0)
  54|      2    0.0065    0.5098    0.5289   20.0396 ^ _11426_/Y (sky130_fd_sc_hd__o21ai_0)
  55|                     0.5098    0.0000   20.0396 ^ _11427_/A2 (sky130_fd_sc_hd__a21oi_1)
  56|      2    0.0069    0.1331    0.3197   20.3593 v _11427_/Y (sky130_fd_sc_hd__a21oi_1)
  57|                     0.1331    0.0000   20.3593 v _11428_/C (sky130_fd_sc_hd__maj3_1)
  58|      2    0.0069    0.1564    0.9447   21.3040 v _11428_/X (sky130_fd_sc_hd__maj3_1)
  59|                     0.1564    0.0000   21.3040 v _11429_/C (sky130_fd_sc_hd__maj3_1)
  60|      2    0.0061    0.1494    0.9456   22.2496 v _11429_/X (sky130_fd_sc_hd__maj3_1)
  61|                     0.1494    0.0000   22.2496 v _11430_/A2 (sky130_fd_sc_hd__o21bai_1)
  62|      2    0.0065    0.3918    0.4391   22.6887 ^ _11430_/Y (sky130_fd_sc_hd__o21bai_1)
  63|                     0.3918    0.0000   22.6887 ^ _11431_/A2 (sky130_fd_sc_hd__a21oi_1)
  64|      3    0.0050    0.1137    0.2517   22.9404 v _11431_/Y (sky130_fd_sc_hd__a21oi_1)
  65|                     0.1137    0.0000   22.9404 v _11433_/A2 (sky130_fd_sc_hd__o21ai_0)
  66|      2    0.0065    0.5099    0.5119   23.4524 ^ _11433_/Y (sky130_fd_sc_hd__o21ai_0)
  67|                     0.5099    0.0000   23.4524 ^ _11434_/A2 (sky130_fd_sc_hd__a21oi_1)
  68|      3    0.0084    0.1479    0.3357   23.7880 v _11434_/Y (sky130_fd_sc_hd__a21oi_1)
  69|                     0.1479    0.0000   23.7880 v _11438_/A3 (sky130_fd_sc_hd__o31ai_1)
  70|      3    0.0088    0.8527    0.8462   24.6343 ^ _11438_/Y (sky130_fd_sc_hd__o31ai_1)
  71|                     0.8527    0.0000   24.6343 ^ _11440_/B2 (sky130_fd_sc_hd__a221oi_1)
  72|      3    0.0058    0.1806    0.4326   25.0668 v _11440_/Y (sky130_fd_sc_hd__a221oi_1)
  73|                     0.1806    0.0000   25.0668 v _11443_/A3 (sky130_fd_sc_hd__o311ai_0)
  74|      3    0.0068    1.0230    1.0241   26.0910 ^ _11443_/Y (sky130_fd_sc_hd__o311ai_0)
  75|                     1.0230    0.0000   26.0910 ^ _11446_/A3 (sky130_fd_sc_hd__a311oi_1)
  76|      3    0.0042    0.1761    0.4919   26.5829 v _11446_/Y (sky130_fd_sc_hd__a311oi_1)
  77|                     0.1761    0.0000   26.5829 v _11451_/A3 (sky130_fd_sc_hd__o311ai_0)
  78|      2    0.0045    0.7912    0.8376   27.4205 ^ _11451_/Y (sky130_fd_sc_hd__o311ai_0)
  79|                     0.7912    0.0000   27.4205 ^ _11453_/B (sky130_fd_sc_hd__nand2_1)
  80|      1    0.0041    0.1315    0.3533   27.7737 v _11453_/Y (sky130_fd_sc_hd__nand2_1)
  81|                     0.1315    0.0000   27.7737 v _11507_/B (sky130_fd_sc_hd__xnor2_1)
  82|      2    0.0037    0.0814    0.2543   28.0280 v _11507_/Y (sky130_fd_sc_hd__xnor2_1)
  83|                     0.0814    0.0000   28.0280 v _11509_/A1 (sky130_fd_sc_hd__o21ai_0)
  84|     31    0.0511    3.2455    2.6362   30.6642 ^ _11509_/Y (sky130_fd_sc_hd__o21ai_0)
  85|                     3.2455    0.0000   30.6642 ^ _11512_/B1 (sky130_fd_sc_hd__o21ai_0)
  86|      1    0.0015    0.3761    0.8625   31.5267 v _11512_/Y (sky130_fd_sc_hd__o21ai_0)
  87|                     0.3761    0.0000   31.5267 v _12026_/D (sky130_fd_sc_hd__dfxtp_1)
  88|                                        31.5267   data arrival time
  89| 
  90|                     0.0000   27.9100   27.9100   clock clk (rise edge)
  91|                               0.0000   27.9100   clock network delay (ideal)
  92|                               0.0000   27.9100   clock reconvergence pessimism
  93|                                        27.9100 ^ _12026_/CLK (sky130_fd_sc_hd__dfxtp_1)
  94|                              -0.5559   27.3541   library setup time
  95|                                        27.3541   data required time
  96| -------------------------------------------------------------------------------------
  97|                                        27.3541   data required time
  98|                                       -31.5267   data arrival time
  99| -------------------------------------------------------------------------------------
 100|                                        -4.1726   slack (VIOLATED)
 101| 
 102| 
=== 文件结束：path_R1.rpt ===

=== 文件：path_R2.rpt（共 102 行）===
   1| Startpoint: in_b[2] (input port clocked by clk)
   2| Endpoint: _12026_ (rising edge-triggered flip-flop clocked by clk)
   3| Path Group: clk
   4| Path Type: max
   5| Corner: ss_n40C_1v60
   6| 
   7| Fanout       Cap      Slew     Delay      Time   Description
   8| -------------------------------------------------------------------------------------
   9|                     0.0000    0.0000    0.0000   clock clk (rise edge)
  10|                               0.0000    0.0000   clock network delay (ideal)
  11|                               5.5820    5.5820 ^ input external delay
  12|     19    0.0415    0.4338    0.3091    5.8911 ^ in_b[2] (in)
  13|                     0.4338    0.0000    5.8911 ^ _10621_/B (sky130_fd_sc_hd__nand2_1)
  14|      2    0.0046    0.1123    0.2453    6.1365 v _10621_/Y (sky130_fd_sc_hd__nand2_1)
  15|                     0.1123    0.0000    6.1365 v _10905_/A (sky130_fd_sc_hd__xnor3_1)
  16|      2    0.0054    0.1199    0.9804    7.1168 v _10905_/X (sky130_fd_sc_hd__xnor3_1)
  17|                     0.1199    0.0000    7.1168 v _10907_/B (sky130_fd_sc_hd__xnor2_1)
  18|      3    0.0110    0.6492    0.6267    7.7436 ^ _10907_/Y (sky130_fd_sc_hd__xnor2_1)
  19|                     0.6492    0.0000    7.7436 ^ _11029_/B (sky130_fd_sc_hd__xnor3_1)
  20|      2    0.0063    0.1268    1.0379    8.7814 v _11029_/X (sky130_fd_sc_hd__xnor3_1)
  21|                     0.1268    0.0000    8.7814 v _11087_/B (sky130_fd_sc_hd__xnor2_1)
  22|      2    0.0060    0.1002    0.2727    9.0542 v _11087_/Y (sky130_fd_sc_hd__xnor2_1)
  23|                     0.1002    0.0000    9.0542 v _11113_/A (sky130_fd_sc_hd__xnor2_1)
  24|      3    0.0113    0.6618    0.6601    9.7142 ^ _11113_/Y (sky130_fd_sc_hd__xnor2_1)
  25|                     0.6618    0.0000    9.7142 ^ _11186_/B (sky130_fd_sc_hd__xor3_1)
  26|      2    0.0090    0.1536    1.0917   10.8059 v _11186_/X (sky130_fd_sc_hd__xor3_1)
  27|                     0.1536    0.0000   10.8059 v _11255_/B (sky130_fd_sc_hd__xnor3_1)
  28|      2    0.0061    0.1254    0.9265   11.7324 v _11255_/X (sky130_fd_sc_hd__xnor3_1)
  29|                     0.1254    0.0000   11.7324 v _11257_/B (sky130_fd_sc_hd__xor2_1)
  30|      2    0.0063    0.3752    0.3997   12.1321 ^ _11257_/X (sky130_fd_sc_hd__xor2_1)
  31|                     0.3752    0.0000   12.1321 ^ _11302_/C (sky130_fd_sc_hd__xor3_1)
  32|      2    0.0073    0.1401    0.7300   12.8620 v _11302_/X (sky130_fd_sc_hd__xor3_1)
  33|                     0.1401    0.0000   12.8620 v _11306_/B (sky130_fd_sc_hd__maj3_1)
  34|      2    0.0073    0.1599    0.9433   13.8053 v _11306_/X (sky130_fd_sc_hd__maj3_1)
  35|                     0.1599    0.0000   13.8053 v _11338_/B (sky130_fd_sc_hd__xor3_1)
  36|      2    0.0061    0.1307    0.9799   14.7852 v _11338_/X (sky130_fd_sc_hd__xor3_1)
  37|                     0.1307    0.0000   14.7852 v _11340_/B (sky130_fd_sc_hd__xor2_1)
  38|      2    0.0065    0.3820    0.4077   15.1930 ^ _11340_/X (sky130_fd_sc_hd__xor2_1)
  39|                     0.3820    0.0000   15.1930 ^ _11416_/A1 (sky130_fd_sc_hd__a21oi_1)
  40|      2    0.0067    0.1299    0.2608   15.4538 v _11416_/Y (sky130_fd_sc_hd__a21oi_1)
  41|                     0.1299    0.0000   15.4538 v _11418_/C (sky130_fd_sc_hd__maj3_1)
  42|      2    0.0055    0.1444    0.9285   16.3823 v _11418_/X (sky130_fd_sc_hd__maj3_1)
  43|                     0.1444    0.0000   16.3823 v _11420_/A1 (sky130_fd_sc_hd__o21ai_0)
  44|      2    0.0063    0.4984    0.5449   16.9272 ^ _11420_/Y (sky130_fd_sc_hd__o21ai_0)
  45|                     0.4984    0.0000   16.9272 ^ _11421_/C (sky130_fd_sc_hd__maj3_1)
  46|      2    0.0065    0.1750    0.5349   17.4621 ^ _11421_/X (sky130_fd_sc_hd__maj3_1)
  47|                     0.1750    0.0000   17.4621 ^ _11422_/A2 (sky130_fd_sc_hd__a21oi_1)
  48|      2    0.0067    0.1381    0.1799   17.6420 v _11422_/Y (sky130_fd_sc_hd__a21oi_1)
  49|                     0.1381    0.0000   17.6420 v _11423_/C (sky130_fd_sc_hd__maj3_1)
  50|      2    0.0067    0.1552    0.9453   18.5873 v _11423_/X (sky130_fd_sc_hd__maj3_1)
  51|                     0.1552    0.0000   18.5873 v _11424_/C (sky130_fd_sc_hd__maj3_1)
  52|      2    0.0056    0.1456    0.9406   19.5278 v _11424_/X (sky130_fd_sc_hd__maj3_1)
  53|                     0.1456    0.0000   19.5278 v _11426_/A2 (sky130_fd_sc_hd__o21ai_0)
  54|      2    0.0065    0.5098    0.5289   20.0567 ^ _11426_/Y (sky130_fd_sc_hd__o21ai_0)
  55|                     0.5098    0.0000   20.0567 ^ _11427_/A2 (sky130_fd_sc_hd__a21oi_1)
  56|      2    0.0069    0.1331    0.3197   20.3764 v _11427_/Y (sky130_fd_sc_hd__a21oi_1)
  57|                     0.1331    0.0000   20.3764 v _11428_/C (sky130_fd_sc_hd__maj3_1)
  58|      2    0.0069    0.1564    0.9447   21.3211 v _11428_/X (sky130_fd_sc_hd__maj3_1)
  59|                     0.1564    0.0000   21.3211 v _11429_/C (sky130_fd_sc_hd__maj3_1)
  60|      2    0.0061    0.1494    0.9456   22.2667 v _11429_/X (sky130_fd_sc_hd__maj3_1)
  61|                     0.1494    0.0000   22.2667 v _11430_/A2 (sky130_fd_sc_hd__o21bai_1)
  62|      2    0.0065    0.3918    0.4391   22.7059 ^ _11430_/Y (sky130_fd_sc_hd__o21bai_1)
  63|                     0.3918    0.0000   22.7059 ^ _11431_/A2 (sky130_fd_sc_hd__a21oi_1)
  64|      3    0.0050    0.1137    0.2517   22.9576 v _11431_/Y (sky130_fd_sc_hd__a21oi_1)
  65|                     0.1137    0.0000   22.9576 v _11433_/A2 (sky130_fd_sc_hd__o21ai_0)
  66|      2    0.0065    0.5099    0.5119   23.4695 ^ _11433_/Y (sky130_fd_sc_hd__o21ai_0)
  67|                     0.5099    0.0000   23.4695 ^ _11434_/A2 (sky130_fd_sc_hd__a21oi_1)
  68|      3    0.0084    0.1479    0.3357   23.8052 v _11434_/Y (sky130_fd_sc_hd__a21oi_1)
  69|                     0.1479    0.0000   23.8052 v _11438_/A3 (sky130_fd_sc_hd__o31ai_1)
  70|      3    0.0088    0.8527    0.8462   24.6514 ^ _11438_/Y (sky130_fd_sc_hd__o31ai_1)
  71|                     0.8527    0.0000   24.6514 ^ _11440_/B2 (sky130_fd_sc_hd__a221oi_1)
  72|      3    0.0058    0.1806    0.4326   25.0840 v _11440_/Y (sky130_fd_sc_hd__a221oi_1)
  73|                     0.1806    0.0000   25.0840 v _11443_/A3 (sky130_fd_sc_hd__o311ai_0)
  74|      3    0.0068    1.0230    1.0241   26.1081 ^ _11443_/Y (sky130_fd_sc_hd__o311ai_0)
  75|                     1.0230    0.0000   26.1081 ^ _11446_/A3 (sky130_fd_sc_hd__a311oi_1)
  76|      3    0.0042    0.1761    0.4919   26.6000 v _11446_/Y (sky130_fd_sc_hd__a311oi_1)
  77|                     0.1761    0.0000   26.6000 v _11451_/A3 (sky130_fd_sc_hd__o311ai_0)
  78|      2    0.0045    0.7912    0.8376   27.4376 ^ _11451_/Y (sky130_fd_sc_hd__o311ai_0)
  79|                     0.7912    0.0000   27.4376 ^ _11453_/B (sky130_fd_sc_hd__nand2_1)
  80|      1    0.0041    0.1315    0.3533   27.7908 v _11453_/Y (sky130_fd_sc_hd__nand2_1)
  81|                     0.1315    0.0000   27.7908 v _11507_/B (sky130_fd_sc_hd__xnor2_1)
  82|      2    0.0037    0.0814    0.2543   28.0452 v _11507_/Y (sky130_fd_sc_hd__xnor2_1)
  83|                     0.0814    0.0000   28.0452 v _11509_/A1 (sky130_fd_sc_hd__o21ai_0)
  84|     31    0.0511    3.2455    2.6362   30.6814 ^ _11509_/Y (sky130_fd_sc_hd__o21ai_0)
  85|                     3.2455    0.0000   30.6814 ^ _11512_/B1 (sky130_fd_sc_hd__o21ai_0)
  86|      1    0.0015    0.3761    0.8625   31.5439 v _11512_/Y (sky130_fd_sc_hd__o21ai_0)
  87|                     0.3761    0.0000   31.5439 v _12026_/D (sky130_fd_sc_hd__dfxtp_1)
  88|                                        31.5439   data arrival time
  89| 
  90|                     0.0000   27.9100   27.9100   clock clk (rise edge)
  91|                               0.0000   27.9100   clock network delay (ideal)
  92|                               0.0000   27.9100   clock reconvergence pessimism
  93|                                        27.9100 ^ _12026_/CLK (sky130_fd_sc_hd__dfxtp_1)
  94|                              -0.5559   27.3541   library setup time
  95|                                        27.3541   data required time
  96| -------------------------------------------------------------------------------------
  97|                                        27.3541   data required time
  98|                                       -31.5439   data arrival time
  99| -------------------------------------------------------------------------------------
 100|                                        -4.1897   slack (VIOLATED)
 101| 
 102| 
=== 文件结束：path_R2.rpt ===

=== 文件：dot4sat.v（共 43 行）===
   1| // CASE-01 baseline (spec 1, D1): four signed 16x16 products summed exactly, saturated to 32-bit signed.
   2| // Output registered only; latency L = 1. Synchronous active-high reset clears out_valid.
   3| // out_data is not reset and has no enable (spec 2.4: data is don't-care when out_valid = 0).
   4| module dot4sat (
   5|     input  wire        clk,
   6|     input  wire        rst,
   7|     input  wire        in_valid,
   8|     input  wire [63:0] in_a,
   9|     input  wire [63:0] in_b,
  10|     output reg         out_valid,
  11|     output reg  [31:0] out_data
  12| );
  13| 
  14|     wire signed [15:0] a0 = in_a[15:0];
  15|     wire signed [15:0] a1 = in_a[31:16];
  16|     wire signed [15:0] a2 = in_a[47:32];
  17|     wire signed [15:0] a3 = in_a[63:48];
  18|     wire signed [15:0] b0 = in_b[15:0];
  19|     wire signed [15:0] b1 = in_b[31:16];
  20|     wire signed [15:0] b2 = in_b[47:32];
  21|     wire signed [15:0] b3 = in_b[63:48];
  22| 
  23|     wire signed [31:0] p0 = a0 * b0;
  24|     wire signed [31:0] p1 = a1 * b1;
  25|     wire signed [31:0] p2 = a2 * b2;
  26|     wire signed [31:0] p3 = a3 * b3;
  27| 
  28|     // full range is [-4294836224, 4294967296]: needs 34 signed bits
  29|     wire signed [33:0] sum = p0 + p1 + p2 + p3;
  30| 
  31|     localparam signed [33:0] SMAX = 34'sd2147483647;
  32|     localparam signed [33:0] SMIN = -34'sd2147483648;
  33| 
  34|     wire [31:0] sat = (sum > SMAX) ? 32'h7FFF_FFFF :
  35|                       (sum < SMIN) ? 32'h8000_0000 : sum[31:0];
  36| 
  37|     always @(posedge clk) begin
  38|         if (rst) out_valid <= 1'b0;
  39|         else     out_valid <= in_valid;
  40|         out_data <= sat;
  41|     end
  42| 
  43| endmodule
=== 文件结束：dot4sat.v ===

=== 文件：context.md（共 79 行）===
   1| ## 1. 接口
   2| 
   3| 模块名 `dot4sat`。单时钟，只在 `clk` 上升沿动作。
   4| 
   5| | 端口 | 方向 | 位宽 | 说明 |
   6| |---|---|---|---|
   7| | `clk` | 入 | 1 | |
   8| | `rst` | 入 | 1 | 同步复位，高有效 |
   9| | `in_valid` | 入 | 1 | |
  10| | `in_a`、`in_b` | 入 | 64 | 第 i 路（i = 0..3）为 `in_a[16*i +: 16]`、`in_b[16*i +: 16]`，各自按 16 位二进制补码解释 |
  11| | `out_valid` | 出 | 1 | |
  12| | `out_data` | 出 | 32 | 32 位二进制补码 |
  13| 
  14| ## 2. 两次分析记录的共同条件
  15| 
  16| - 两次分析记录（R1、R2）用同一份综合网表（sha256 `1fa89c975162f4f1f9a2f349bed73b4dae5f53ab921883be842cb0a37763a8d1`）、同一个工具版本（OpenSTA 3.1.0）、同一套工艺库（Sky130 HD，`sky130_fd_sc_hd`）、同一个六点集合（`tt_025C_1v80`、`tt_100C_1v80`、`ss_100C_1v60`、`ss_n40C_1v60`、`ff_n40C_1v95`、`ff_100C_1v95`）和同一组报告生成命令。
  17| - 分析模型：综合后分析；理想时钟（时钟延迟、uncertainty、transition 都为 0）；不读取寄生参数，连线负载只计引脚电容；数据和控制输入由 `sky130_fd_sc_hd__buf_2`（A→X）驱动，输入 transition 为 0。
  18| - OpenSTA 3.1.0 用 scene 组织 corner：`report_checks`、`find_timing_paths` 用 `-scenes` 选择场景（缩写 `-scene` 也可以用）；`report_wns`、`report_tns`、`report_worst_slack` 没有选择场景的选项。报告生成命令里的变量已展开。
  19| - `summary_R1.tsv`、`summary_R2.tsv`：每次记录的 `WS`（六点 setup/hold 最差 slack）、`CAT`（按路径类别的最差路径：slack、起点、终点）、`TOPO`（按类别的结构路径数）三类行，列说明：`WS <scene> <max|min> <slack>`；`CAT <scene> <类别> <max|min> <slack> <起点> <终点>`；`TOPO <类别> <数量>`。
  20| - `path_R1.rpt`、`path_R2.rpt`：两次记录的详细路径报告都来自 `ss_n40C_1v60` 下"输入到寄存器"这一类的 setup 路径，是下面这条命令的输出（按默认设置只报告 slack 最差的一条）；它可能不是各自的全局最差点，各组的全局最差点在 summary 里：
  21|   `report_checks -from [all_inputs -no_clocks] -to [all_registers -data_pins] -path_delay max -scene ss_n40C_1v60 -fields {slew cap input_pins fanout} -digits 4`
  22| - `intent.md` 是接口时序的意图说明（要求），`values.txt` 是 T 和 C_load 的取值，`dot4sat.v` 是模块的 RTL 原文。
  23| - **两次记录各自实际生效的约束清单和覆盖检查结果尚未提供**，可以在"检查请求"里要求。
  24| - 时钟周期 T 的来历：T 是按"基线最差 setup slack 约为周期的 −15%"校准得到的固定值。
  25| 
  26| ## 查询的执行契约
  27| 
  28| 你在"检查请求"里写的每条 OpenSTA 查询，会由一个固定的执行器按下面的规则执行。规则对参与的每个模型相同，运行开始后不放宽也不收紧。
  29| 
  30| ### 可用命令
  31| 
  32| 查询在一个受限的 Tcl 解释器里运行，只有下面三张表里的命令可用（还有 Tcl 的基本控制结构：`foreach`、`if`、`set`、`puts`、`llength`、`lindex`、`string`、`expr`、`catch`、`flush` 等）。不能读写文件，不能启动外部进程，不能把输出重定向到文件。
  33| 
  34| 只读查询命令（按原文顺序）：`report_annotated_check`、`report_annotated_delay`、`report_arrival`、`report_check_types`、`report_checks`、`report_clock_latency`、`report_clock_min_period`、`report_clock_properties`、`report_clock_skew`、`report_constant`、`report_dcalc`、`report_disabled_edges`、`report_edges`、`report_instance`、`report_lib_cell`、`report_net`、`report_object_full_names`、`report_object_names`、`report_parasitic_annotation`、`report_path`、`report_required`、`report_slack`、`report_slew`、`report_slews`、`report_tns`、`report_units`、`report_wns`、`report_worst_slack`、`check_setup`、`find_timing_paths`、`get_cell`、`get_cells`、`get_clock`、`get_clocks`、`get_fanin`、`get_fanout`、`get_full_name`、`get_lib`、`get_lib_cell`、`get_lib_cells`、`get_lib_pin`、`get_lib_pins`、`get_libs`、`get_modes`、`get_name`、`get_net`、`get_nets`、`get_pin`、`get_pins`、`get_port`、`get_ports`、`get_property`、`get_scenes`、`get_timing_edges`、`all_clocks`、`all_inputs`、`all_outputs`、`all_registers`、`total_negative_slack`、`worst_clock_skew`、`worst_negative_slack`、`worst_slack`。
  35| 
  36| 改变分析模型的命令（约束、分析条件、单位、场景、网表）：`connect_pin`、`create_clock`、`create_generated_clock`、`create_voltage_area`、`delete_clock`、`delete_generated_clock`、`delete_instance`、`delete_net`、`disconnect_pin`、`make_instance`、`make_net`、`make_port`、`replace_cell`、`set_assigned_check`、`set_assigned_delay`、`set_assigned_transition`、`set_case_analysis`、`set_clock_gating_check`、`set_clock_groups`、`set_clock_latency`、`set_clock_sense`、`set_clock_transition`、`set_clock_uncertainty`、`set_cmd_units`、`set_data_check`、`set_delay_calculator`、`set_disable_clock_gating_check`、`set_disable_inferred_clock_gating`、`set_disable_timing`、`set_drive`、`set_driving_cell`、`set_false_path`、`set_fanout_load`、`set_hierarchy_separator`、`set_ideal_latency`、`set_ideal_network`、`set_ideal_transition`、`set_input_delay`、`set_input_transition`、`set_level_shifter_strategy`、`set_level_shifter_threshold`、`set_load`、`set_logic_dc`、`set_logic_one`、`set_logic_zero`、`set_max_area`、`set_max_capacitance`、`set_max_delay`、`set_max_dynamic_power`、`set_max_fanout`、`set_max_leakage_power`、`set_max_time_borrow`、`set_max_transition`、`set_min_capacitance`、`set_min_delay`、`set_min_pulse_width`、`set_mode`、`set_multicycle_path`、`set_operating_conditions`、`set_output_delay`、`set_path_margin`、`set_port_fanout_number`、`set_power_activity`、`set_propagated_clock`、`set_property`、`set_pvt`、`set_resistance`、`set_scene`、`set_sense`、`set_timing_derate`、`set_units`、`set_voltage`、`set_wire_load_min_block_size`、`set_wire_load_mode`、`set_wire_load_model`、`set_wire_load_selection_group`、`unset_case_analysis`、`unset_clock_groups`、`unset_clock_latency`、`unset_clock_transition`、`unset_clock_uncertainty`、`unset_data_check`、`unset_disable_clock_gating_check`、`unset_disable_inferred_clock_gating`、`unset_disable_timing`、`unset_input_delay`、`unset_output_delay`、`unset_path_exceptions`、`unset_power_activity`、`unset_propagated_clock`、`unset_timing_derate`。含这些命令的查询在单独的对照实例里执行，结果会标注"改变模型的对照"；它可以支持或反对一个假设，但不能用来证实关于原始分析模型的事实。
  37| 
  38| 建环境命令（分析环境已经由记录提供，调用时跳过并回显一行说明）：`create_clock`、`define_corners`、`define_scene`、`link_design`、`read_liberty`、`read_power_activities`、`read_saif`、`read_sdc`、`read_sdf`、`read_spef`、`read_vcd`、`read_verilog`、`sky130_define_scenes`、`sky130_read_libs`。其中 `create_clock` 的周期等于记录里的 T 时按建环境命令跳过，周期是其他值时按改变模型的命令处理。
  39| 
  40| ### 多场景的写法
  41| 
  42| 分析里有六个 scene。`report_arrival`、`report_required`、`report_slack` 在多 scene 下必须带 `-scene <名字>`；不带时工具会报 `Error 103`，这个错误会原样交还给你，执行器不替你改写。`report_checks`、`find_timing_paths` 接受 `-scene` 或 `-scenes`。
  43| 
  44| ### 输出顺序
  45| 
  46| 执行器在每条命令执行前后自动 `flush` 标准输出，所以循环里 `puts` 的文字和紧随其后的报告输出会按你写的顺序出现，你不需要自己处理。
  47| 
  48| ### 实例、行数和字节上限
  49| 
  50| 每条查询对每一份分析记录各执行一次，称为一个实例：你写明只对 R1 或只对 R2 执行的，有 1 个实例；没写明的，有 2 个实例（R1、R2 各一个，结果分别标注）。每个模型最多 12 条检查请求；第 13 条起不执行。
  51| 
  52| 每个实例交还给你的输出最多 2000 行（含命令回显行），同时最多 256 KiB（按交还文字的 UTF-8 字节计）。超过时保留开头和结尾各一半，中间用一行 `[已截断：省略 N 行；原始 M 行 B 字节；见执行契约]` 代替，省略的行数相对原始输出计。计数的例外：截断标记那一行和下面说的单行截断后缀不计入上面的行数和字节数（所以被截断的实例交还 2001 行）；单独一行超过 256 KiB 时，这一行先缩短到 128 KiB 并在行尾加 `…[本行截断]` 标记，再按上面的规则处理。原始输出会完整保存，但不交还。
  53| 
  54| 下面这些形态的查询（编号 W01–W08）保证不会被截断：
  55| - W01：check_setup 带端口名单；
  56| - W02：单 scene 对全部非时钟输入逐端口 report_arrival 的循环；
  57| - W03：单 scene 对全部非时钟输入逐端口 find_timing_paths 计数（max/min，带与不带 -unconstrained）的循环；
  58| - W04：W01 与 W02 放在同一实例；
  59| - W05：六个 scene 的 W02 与 W03 放在同一实例；
  60| - W06：默认路径数的一条 report_checks；
  61| - W07：单 scene 的 report_check_types -verbose；
  62| - W08：六个 scene 的 worst_slack 与 total_negative_slack（max 与 min）；
  63| 
  64| 下面这些形态不保证不被截断（按实测会超出上面的上限）：
  65| - 逐端口完整 report_checks 报告乘以多端口（单 scene 全部输入约 6500 行，六个 scene 约 39000 行）；
  66| - -group_path_count 或 -endpoint_path_count 不小于 40 的报告；
  67| - 跨多个 scene 的完整报告枚举；
  68| 
  69| ### 总预算
  70| 
  71| 一个模型的全部实例加起来交还给你的文字有总预算：600000 token（按保守换算，每 token 约 1.91 字节）。超过时按下面的顺序保留，排在后面的实例整个不交还：你在检查请求里声明的优先级在前；没有声明的按请求编号顺序；同一条请求 R1 先于 R2。第 2 轮题目末尾固定附一张预算账单，写明总预算、每个已交还实例占用的行数和是否截断、每个未交还实例的原始行数和被排到后面所依据的规则。未交还不等于查询失败。
  72| 
  73| ### 时间和其他上限
  74| 
  75| 每个实例里查询部分的时限 600 秒，整个工具进程 1200 秒；进程输出超过 50 MiB 时终止；工具进程的内存上限 8 GiB（超过时工具进程自行退出）；受限解释器最多执行 1000000 条 Tcl 命令。因超时或超限终止的实例，交还的是终止前已经产生的输出，末尾附一行说明。
  76| 
  77| ### 交还的内容
  78| 
  79| 每个实例交还：你的原始查询、实际执行的查询（只有预先登记的两条机械改写规则可能改动它，改动会注明）、输出、一个固定的结果代码。第 2 轮里新提出的查询会被记录，但不执行。
=== 文件结束：context.md ===

请按以下四个部分作答，每部分用对应的标题开头。四部分合计不超过 120 行；超出的部分不进入评分，其中的检查请求也不会被执行。

一、观察
列出 R1 与 R2 之间的差异事实，每条注明证据位置（文件名:行号）。

二、结论和确定程度
对"两次记录的差异来自什么"给出你的结论，并明确写出它是"确认"、"假设"还是"条件成立时才确认"。区分"报告的 slack 变大"和"电路变快"。结论涉及约束时写出端口范围。

三、证据
列出支撑你结论的证据，以及还缺什么。

四、检查请求
列出你希望执行的查询（最多 12 条，第 13 条起不执行），尽量写成可以直接在 OpenSTA 3.1.0 中执行的命令，并写明对 R1 还是 R2 执行；不写明的，对两组都执行。context.md 里的"查询的执行契约"说明了可用命令、输出上限和总预算；你可以为各条查询声明优先级（写"优先级 n"）。

以下是你在第 1 轮的回答。

<<<第 1 轮回答开始>>>
一、观察

1. 两次记录的**结构路径数完全相同**：in2reg=130、reg2reg=0、reg2out=33（summary_R1.tsv:1-3；summary_R2.tsv:1-3）。
2. 两次记录的 **reg2out** 的 WS 值和 CAT 值在六个 corner 下完全一致（summary_R1.tsv:10-11,18-19,26-27,34-35,42-43,50-51；summary_R2.tsv:10-11,18-19,26-27,34-35,42-43,50-51）。
3. 两次记录的 **in2reg min** WS/CAT 完全一致，起点都是 `rst`、终点 `_12058_/D`（summary_R1.tsv:7,15,23,31,39,47；summary_R2.tsv:7,15,23,31,39,47）。
4. 仅 **in2reg max** 的 setup 最差 slack 不同：R2 比 R1 变小（更差）约 0.004–0.017 ns。具体为 tt_025C_1v80 由 11.191043 到 11.185458（R1:4，R2:4）；tt_100C_1v80 由 11.321179 到 11.317221（R1:12，R2:12）；ss_100C_1v60 由 -0.679952 到 -0.687278（R1:20，R2:20）；ss_n40C_1v60 由 -4.172595 到 -4.189726（R1:28，R2:28）；ff_n40C_1v95 由 15.881204 到 15.871505（R1:36，R2:36）；ff_100C_1v95 由 15.902846 到 15.894229（R1:44，R2:44）。
5. 与上一条对应，**in2reg max 的最差路径起点整体换组**：R1 全部在 `in_a` 侧（tt/tt100/ss100/ss_n40 为 `in_a[34]`，ff_n40/ff100 为 `in_a[3]`，见 summary_R1.tsv:6,14,22,30,38,46）；R2 全部在 `in_b` 侧（tt/tt100/ss100 为 `in_b[35]`，ss_n40/ff_n40/ff100 为 `in_b[2]`，见 summary_R2.tsv:6,14,22,30,38,46）；两者终点都是 `_12026_/D`。
6. 两条详细路径报告都来自 `ss_n40C_1v60` 的 in2reg setup 最差路径。R1 起点 `in_a[34]`、到达 31.5267、slack -4.1726（path_R1.rpt:1,88,100）；R2 起点 `in_b[2]`、到达 31.5439、slack -4.1897（path_R2.rpt:1,88,100）。
7. 两条路径报告的 input external delay 同为 5.5820（path_R1.rpt:11；path_R2.rpt:11），data required time 同为 27.3541（path_R1.rpt:94-95；path_R2.rpt:94-95）；且都在 `_11302_/X` 之后进入相同的公共后缀（path_R1.rpt:32 起为 12.8449；path_R2.rpt:32 起为 12.8620，到终点各段 delay 一致）。

二、结论和确定程度

结论：两次记录的差异最可能来自**两次运行实际生效的输入侧约束/路径例外不同**（尤其是 R1 与 R2 对 `in_a` 或 `in_b` 相关输入的 input delay 覆盖/数值或 false/multicycle/disables 不同），而不是网表、库、corner、负载或内部电路速度发生了变化。R2 相对 R1 的“报告 slack”不是变大，而是 **in2reg max setup slack 变小（更差）**；这不是“电路变快”，也不是公共门路径变慢——两条路径的公共尾部相同，只是被报告为最差的输入起点从 `in_a` 侧换到了 `in_b` 侧。

确定程度：**条件成立时才确认**。因为实际生效的约束清单和覆盖检查尚未提供（context.md:23），目前只能说是强假设。确认条件：若检查请求显示 R1 与 R2 在 `in_a`/`in_b` 的 input delay 覆盖不同（R2 对 `in_a` 侧没有 5.582 的 max input delay，或设小/排除，导致 `in_b` 侧成为最差；或在 R1 中 `in_b` 侧未被同等上报），则本结论成立。端口范围重点在 `in_a[63:0]` 与 `in_b[63:0]`。

三、证据

- 支持差异“不是全局网表/库/负载变化”的证据：TOPO、reg2out、in2reg min 完全一致（summary_R1.tsv:1-3,7,10-11,15,18-19,23,26-27,31,34-35,39,42-43,47,50-51；summary_R2.tsv 对应行）。
- 支持差异在“输入侧选径”的证据：六个 corner 的 in2reg max 起点从 R1 的 `in_a` 组系统性地变成 R2 的 `in_b` 组（summary_R1.tsv:6,14,22,30,38,46；summary_R2.tsv:6,14,22,30,38,46），而终点、min 起点保持不变。
- 支持“两条路径只是起点不同、公共段不变”的证据：两条 path 报告的 input external delay 均为 5.5820，required time 均为 27.3541，且自 `_11302_/X` 后逐段 delay 完全一致（path_R1.rpt:11,32-98；path_R2.rpt:11,32-98）。
- 缺失的证据：R1、R2 各自展开后每个非时钟输入端口的 `input_delay_max/min`（或等价报告）、`driving_cell`/transition、是否有 `set_false_path`/`set_multicycle_path`/`set_disable_timing` 作用于 `in_a`/`in_b`，以及 R1/R2 对全部 130 个非时钟输入的覆盖检查结果。

四、检查请求

```tcl
# Q1（优先级1；对 R1 和 R2 都执行）
# 关键起点是否形成受约束的 in2reg max 路径
foreach p [get_ports {in_a[34] in_b[2] in_a[3] in_b[35]}] {
  puts "PORT $p"
  catch { report_checks -from $p -to [get_pins _12026_/D] -path_delay max \
           -scene ss_n40C_1v60 -fields {slack input_pins arrival required} -digits 4 }
}

# Q2（优先级1；对 R1 和 R2 都执行）
# 全非时钟输入逐端口计数：max/min，带/不带 -unconstrained
set scene ss_n40C_1v60
foreach p [all_inputs -no_clocks] {
  set n1 [llength [find_timing_paths -from $p -to [all_registers -data_pins] \
          -path_delay max -scene $scene]]
  set n2 [llength [find_timing_paths -from $p -to [all_registers -data_pins] \
          -path_delay max -scene $scene -unconstrained]]
  set n3 [llength [find_timing_paths -from $p -to [all_registers -data_pins] \
          -path_delay min -scene $scene]]
  set n4 [llength [find_timing_paths -from $p -to [all_registers -data_pins] \
          -path_delay min -scene $scene -unconstrained]]
  puts "$p max $n1 $n2 min $n3 $n4"
}

# Q3（优先级2；对 R1 和 R2 都执行）
# 比较全输入到 _12026_/D 的到达时间
set scene ss_n40C_1v60
foreach p [all_inputs -no_clocks] {
  puts "PORT $p"
  catch { report_arrival -from $p -to [get_pins _12026_/D] -scene $scene -digits 4 }
}

# Q4（优先级3；对 R1 和 R2 都执行）
# 读取每个非时钟输入端口的 input delay/driving 属性
foreach p [all_inputs -no_clocks] {
  puts "PORT $p"
  foreach prop {input_delay_max input_delay_min input_transition_rise input_transition_fall driving_cell} {
    if {[catch {set v [get_property $p $prop]}]} { set v "<no_property>" }
    puts "  $prop $v"
  }
}

# Q5（优先级2；对 R1 和 R2 都执行）
# 六 scene 全局最差/TNS，核验差异被限制在 in2reg max
foreach sc {tt_025C_1v80 tt_100C_1v80 ss_100C_1v60 ss_n40C_1v60 ff_n40C_1v95 ff_100C_1v95} {
  puts "$sc max WS=[worst_slack -max -scene $sc] TNS=[total_negative_slack -max -scene $sc]"
  puts "$sc min WS=[worst_slack -min -scene $sc] TNS=[total_negative_slack -min -scene $sc]"
}

# Q6（优先级3；对 R1 和 R2 都执行）
# 汇总每实例中被约束输入端口/仅 -unconstrained 可见的端口数
set scene ss_n40C_1v60
set cn 0; set un 0
foreach p [all_inputs -no_clocks] {
  set a [llength [find_timing_paths -from $p -to [all_registers -data_pins] \
         -path_delay max -scene $scene]]
  set b [llength [find_timing_paths -from $p -to [all_registers -data_pins] \
         -path_delay max -scene $scene -unconstrained]]
  if {$a > 0} { incr cn }
  if {$a == 0 && $b > 0} { incr un }
}
puts "constrained_in2reg_max_endpoints=$cn unconstrained_only=$un"
```
<<<第 1 轮回答结束>>>

以下是你在第 1 轮"检查请求"中提出的查询的执行结果（末尾附预算账单）。

### 查询 B1（R1）
你写的查询：
```tcl
# Q1（优先级1；对 R1 和 R2 都执行）
# 关键起点是否形成受约束的 in2reg max 路径
foreach p [get_ports {in_a[34] in_b[2] in_a[3] in_b[35]}] {
  puts "PORT $p"
  catch { report_checks -from $p -to [get_pins _12026_/D] -path_delay max \
           -scene ss_n40C_1v60 -fields {slack input_pins arrival required} -digits 4 }
}

# Q2（优先级1；对 R1 和 R2 都执行）
# 全非时钟输入逐端口计数：max/min，带/不带 -unconstrained
set scene ss_n40C_1v60
foreach p [all_inputs -no_clocks] {
  set n1 [llength [find_timing_paths -from $p -to [all_registers -data_pins] \
          -path_delay max -scene $scene]]
  set n2 [llength [find_timing_paths -from $p -to [all_registers -data_pins] \
          -path_delay max -scene $scene -unconstrained]]
  set n3 [llength [find_timing_paths -from $p -to [all_registers -data_pins] \
          -path_delay min -scene $scene]]
  set n4 [llength [find_timing_paths -from $p -to [all_registers -data_pins] \
          -path_delay min -scene $scene -unconstrained]]
  puts "$p max $n1 $n2 min $n3 $n4"
}

# Q3（优先级2；对 R1 和 R2 都执行）
# 比较全输入到 _12026_/D 的到达时间
set scene ss_n40C_1v60
foreach p [all_inputs -no_clocks] {
  puts "PORT $p"
  catch { report_arrival -from $p -to [get_pins _12026_/D] -scene $scene -digits 4 }
}

# Q4（优先级3；对 R1 和 R2 都执行）
# 读取每个非时钟输入端口的 input delay/driving 属性
foreach p [all_inputs -no_clocks] {
  puts "PORT $p"
  foreach prop {input_delay_max input_delay_min input_transition_rise input_transition_fall driving_cell} {
    if {[catch {set v [get_property $p $prop]}]} { set v "<no_property>" }
    puts "  $prop $v"
  }
}

# Q5（优先级2；对 R1 和 R2 都执行）
# 六 scene 全局最差/TNS，核验差异被限制在 in2reg max
foreach sc {tt_025C_1v80 tt_100C_1v80 ss_100C_1v60 ss_n40C_1v60 ff_n40C_1v95 ff_100C_1v95} {
  puts "$sc max WS=[worst_slack -max -scene $sc] TNS=[total_negative_slack -max -scene $sc]"
  puts "$sc min WS=[worst_slack -min -scene $sc] TNS=[total_negative_slack -min -scene $sc]"
}

# Q6（优先级3；对 R1 和 R2 都执行）
# 汇总每实例中被约束输入端口/仅 -unconstrained 可见的端口数
set scene ss_n40C_1v60
set cn 0; set un 0
foreach p [all_inputs -no_clocks] {
  set a [llength [find_timing_paths -from $p -to [all_registers -data_pins] \
         -path_delay max -scene $scene]]
  set b [llength [find_timing_paths -from $p -to [all_registers -data_pins] \
         -path_delay max -scene $scene -unconstrained]]
  if {$a > 0} { incr cn }
  if {$a == 0 && $b > 0} { incr un }
}
puts "constrained_in2reg_max_endpoints=$cn unconstrained_only=$un"
```
实际执行的命令：
```tcl
# Q1（优先级1；对 R1 和 R2 都执行）
# 关键起点是否形成受约束的 in2reg max 路径
foreach p [get_ports {in_a[34] in_b[2] in_a[3] in_b[35]}] {
  puts "PORT $p"
  catch { report_checks -from $p -to [get_pins _12026_/D] -path_delay max \
           -scene ss_n40C_1v60 -fields {slack input_pins arrival required} -digits 4 }
}

# Q2（优先级1；对 R1 和 R2 都执行）
# 全非时钟输入逐端口计数：max/min，带/不带 -unconstrained
set scene ss_n40C_1v60
foreach p [all_inputs -no_clocks] {
  set n1 [llength [find_timing_paths -from $p -to [all_registers -data_pins] \
          -path_delay max -scene $scene]]
  set n2 [llength [find_timing_paths -from $p -to [all_registers -data_pins] \
          -path_delay max -scene $scene -unconstrained]]
  set n3 [llength [find_timing_paths -from $p -to [all_registers -data_pins] \
          -path_delay min -scene $scene]]
  set n4 [llength [find_timing_paths -from $p -to [all_registers -data_pins] \
          -path_delay min -scene $scene -unconstrained]]
  puts "$p max $n1 $n2 min $n3 $n4"
}

# Q3（优先级2；对 R1 和 R2 都执行）
# 比较全输入到 _12026_/D 的到达时间
set scene ss_n40C_1v60
foreach p [all_inputs -no_clocks] {
  puts "PORT $p"
  catch { report_arrival -from $p -to [get_pins _12026_/D] -scene $scene -digits 4 }
}

# Q4（优先级3；对 R1 和 R2 都执行）
# 读取每个非时钟输入端口的 input delay/driving 属性
foreach p [all_inputs -no_clocks] {
  puts "PORT $p"
  foreach prop {input_delay_max input_delay_min input_transition_rise input_transition_fall driving_cell} {
    if {[catch {set v [get_property $p $prop]}]} { set v "<no_property>" }
    puts "  $prop $v"
  }
}

# Q5（优先级2；对 R1 和 R2 都执行）
# 六 scene 全局最差/TNS，核验差异被限制在 in2reg max
foreach sc {tt_025C_1v80 tt_100C_1v80 ss_100C_1v60 ss_n40C_1v60 ff_n40C_1v95 ff_100C_1v95} {
  puts "$sc max WS=[worst_slack -max -scene $sc] TNS=[total_negative_slack -max -scene $sc]"
  puts "$sc min WS=[worst_slack -min -scene $sc] TNS=[total_negative_slack -min -scene $sc]"
}

# Q6（优先级3；对 R1 和 R2 都执行）
# 汇总每实例中被约束输入端口/仅 -unconstrained 可见的端口数
set scene ss_n40C_1v60
set cn 0; set un 0
foreach p [all_inputs -no_clocks] {
  set a [llength [find_timing_paths -from $p -to [all_registers -data_pins] \
         -path_delay max -scene $scene]]
  set b [llength [find_timing_paths -from $p -to [all_registers -data_pins] \
         -path_delay max -scene $scene -unconstrained]]
  if {$a > 0} { incr cn }
  if {$a == 0 && $b > 0} { incr un }
}
puts "constrained_in2reg_max_endpoints=$cn unconstrained_only=$un"
```
机械改写：无
执行类型：原上下文；执行结果：语法错误；异常：-；归因：请求本身的问题
输出：
```text
CASE02-CMD: foreach p [get_ports {in_a[34] in_b[2] in_a[3] in_b[35]}] {
PORT _906ecdedfb640000_p_Port
Warning 168: c2_query.tcl line 1, unknown field slack.
Warning 168: c2_query.tcl line 1, unknown field arrival.
Warning 168: c2_query.tcl line 1, unknown field required.
Startpoint: in_a[34] (input port clocked by clk)
Endpoint: _12026_ (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max
Corner: ss_n40C_1v60

    Delay      Time   Description
-------------------------------------------------------------
   0.0000    0.0000   clock clk (rise edge)
   0.0000    0.0000   clock network delay (ideal)
   5.5820    5.5820 ^ input external delay
   0.2730    5.8550 ^ in_a[34] (in)
   0.0000    5.8550 ^ _10564_/A (sky130_fd_sc_hd__and2_0)
   0.4006    6.2556 ^ _10564_/X (sky130_fd_sc_hd__and2_0)
   0.0000    6.2556 ^ _10854_/A (sky130_fd_sc_hd__xnor3_1)
   1.0188    7.2744 v _10854_/X (sky130_fd_sc_hd__xnor3_1)
   0.0000    7.2744 v _10985_/B (sky130_fd_sc_hd__xor3_1)
   0.9736    8.2480 v _10985_/X (sky130_fd_sc_hd__xor3_1)
   0.0000    8.2480 v _10986_/B (sky130_fd_sc_hd__xor2_1)
   0.4475    8.6955 ^ _10986_/X (sky130_fd_sc_hd__xor2_1)
   0.0000    8.6955 ^ _11069_/B (sky130_fd_sc_hd__xor2_1)
   0.4045    9.1000 ^ _11069_/X (sky130_fd_sc_hd__xor2_1)
   0.0000    9.1000 ^ _11071_/C (sky130_fd_sc_hd__nand3_1)
   0.2403    9.3403 v _11071_/Y (sky130_fd_sc_hd__nand3_1)
   0.0000    9.3403 v _11073_/B (sky130_fd_sc_hd__xor3_1)
   0.9973   10.3376 v _11073_/X (sky130_fd_sc_hd__xor3_1)
   0.0000   10.3376 v _11149_/A (sky130_fd_sc_hd__xnor2_1)
   0.5470   10.8846 ^ _11149_/Y (sky130_fd_sc_hd__xnor2_1)
   0.0000   10.8846 ^ _11228_/B (sky130_fd_sc_hd__xnor3_1)
   0.9809   11.8655 v _11228_/X (sky130_fd_sc_hd__xnor3_1)
   0.0000   11.8655 v _11302_/B (sky130_fd_sc_hd__xor3_1)
   0.9794   12.8449 v _11302_/X (sky130_fd_sc_hd__xor3_1)
   0.0000   12.8449 v _11306_/B (sky130_fd_sc_hd__maj3_1)
   0.9433   13.7882 v _11306_/X (sky130_fd_sc_hd__maj3_1)
   0.0000   13.7882 v _11338_/B (sky130_fd_sc_hd__xor3_1)
   0.9799   14.7681 v _11338_/X (sky130_fd_sc_hd__xor3_1)
   0.0000   14.7681 v _11340_/B (sky130_fd_sc_hd__xor2_1)
   0.4077   15.1758 ^ _11340_/X (sky130_fd_sc_hd__xor2_1)
   0.0000   15.1758 ^ _11416_/A1 (sky130_fd_sc_hd__a21oi_1)
   0.2608   15.4366 v _11416_/Y (sky130_fd_sc_hd__a21oi_1)
   0.0000   15.4366 v _11418_/C (sky130_fd_sc_hd__maj3_1)
   0.9285   16.3652 v _11418_/X (sky130_fd_sc_hd__maj3_1)
   0.0000   16.3652 v _11420_/A1 (sky130_fd_sc_hd__o21ai_0)
   0.5449   16.9101 ^ _11420_/Y (sky130_fd_sc_hd__o21ai_0)
   0.0000   16.9101 ^ _11421_/C (sky130_fd_sc_hd__maj3_1)
   0.5349   17.4450 ^ _11421_/X (sky130_fd_sc_hd__maj3_1)
   0.0000   17.4450 ^ _11422_/A2 (sky130_fd_sc_hd__a21oi_1)
   0.1799   17.6249 v _11422_/Y (sky130_fd_sc_hd__a21oi_1)
   0.0000   17.6249 v _11423_/C (sky130_fd_sc_hd__maj3_1)
   0.9453   18.5701 v _11423_/X (sky130_fd_sc_hd__maj3_1)
   0.0000   18.5701 v _11424_/C (sky130_fd_sc_hd__maj3_1)
   0.9406   19.5107 v _11424_/X (sky130_fd_sc_hd__maj3_1)
   0.0000   19.5107 v _11426_/A2 (sky130_fd_sc_hd__o21ai_0)
   0.5289   20.0396 ^ _11426_/Y (sky130_fd_sc_hd__o21ai_0)
   0.0000   20.0396 ^ _11427_/A2 (sky130_fd_sc_hd__a21oi_1)
   0.3197   20.3593 v _11427_/Y (sky130_fd_sc_hd__a21oi_1)
   0.0000   20.3593 v _11428_/C (sky130_fd_sc_hd__maj3_1)
   0.9447   21.3040 v _11428_/X (sky130_fd_sc_hd__maj3_1)
   0.0000   21.3040 v _11429_/C (sky130_fd_sc_hd__maj3_1)
   0.9456   22.2496 v _11429_/X (sky130_fd_sc_hd__maj3_1)
   0.0000   22.2496 v _11430_/A2 (sky130_fd_sc_hd__o21bai_1)
   0.4391   22.6887 ^ _11430_/Y (sky130_fd_sc_hd__o21bai_1)
   0.0000   22.6887 ^ _11431_/A2 (sky130_fd_sc_hd__a21oi_1)
   0.2517   22.9404 v _11431_/Y (sky130_fd_sc_hd__a21oi_1)
   0.0000   22.9404 v _11433_/A2 (sky130_fd_sc_hd__o21ai_0)
   0.5119   23.4524 ^ _11433_/Y (sky130_fd_sc_hd__o21ai_0)
   0.0000   23.4524 ^ _11434_/A2 (sky130_fd_sc_hd__a21oi_1)
   0.3357   23.7880 v _11434_/Y (sky130_fd_sc_hd__a21oi_1)
   0.0000   23.7880 v _11438_/A3 (sky130_fd_sc_hd__o31ai_1)
   0.8462   24.6343 ^ _11438_/Y (sky130_fd_sc_hd__o31ai_1)
   0.0000   24.6343 ^ _11440_/B2 (sky130_fd_sc_hd__a221oi_1)
   0.4326   25.0668 v _11440_/Y (sky130_fd_sc_hd__a221oi_1)
   0.0000   25.0668 v _11443_/A3 (sky130_fd_sc_hd__o311ai_0)
   1.0241   26.0910 ^ _11443_/Y (sky130_fd_sc_hd__o311ai_0)
   0.0000   26.0910 ^ _11446_/A3 (sky130_fd_sc_hd__a311oi_1)
   0.4919   26.5829 v _11446_/Y (sky130_fd_sc_hd__a311oi_1)
   0.0000   26.5829 v _11451_/A3 (sky130_fd_sc_hd__o311ai_0)
   0.8376   27.4205 ^ _11451_/Y (sky130_fd_sc_hd__o311ai_0)
   0.0000   27.4205 ^ _11453_/B (sky130_fd_sc_hd__nand2_1)
   0.3533   27.7737 v _11453_/Y (sky130_fd_sc_hd__nand2_1)
   0.0000   27.7737 v _11507_/B (sky130_fd_sc_hd__xnor2_1)
   0.2543   28.0280 v _11507_/Y (sky130_fd_sc_hd__xnor2_1)
   0.0000   28.0280 v _11509_/A1 (sky130_fd_sc_hd__o21ai_0)
   2.6362   30.6642 ^ _11509_/Y (sky130_fd_sc_hd__o21ai_0)
   0.0000   30.6642 ^ _11512_/B1 (sky130_fd_sc_hd__o21ai_0)
   0.8625   31.5267 v _11512_/Y (sky130_fd_sc_hd__o21ai_0)
   0.0000   31.5267 v _12026_/D (sky130_fd_sc_hd__dfxtp_1)
            31.5267   data arrival time

  27.9100   27.9100   clock clk (rise edge)
   0.0000   27.9100   clock network delay (ideal)
   0.0000   27.9100   clock reconvergence pessimism
            27.9100 ^ _12026_/CLK (sky130_fd_sc_hd__dfxtp_1)
  -0.5559   27.3541   library setup time
            27.3541   data required time
-------------------------------------------------------------
            27.3541   data required time
           -31.5267   data arrival time
-------------------------------------------------------------
            -4.1726   slack (VIOLATED)


PORT _109fcdedfb640000_p_Port
Warning 168: c2_query.tcl line 1, unknown field slack.
Warning 168: c2_query.tcl line 1, unknown field arrival.
Warning 168: c2_query.tcl line 1, unknown field required.
No paths found.
PORT _107ecdedfb640000_p_Port
Warning 168: c2_query.tcl line 1, unknown field slack.
Warning 168: c2_query.tcl line 1, unknown field arrival.
Warning 168: c2_query.tcl line 1, unknown field required.
Startpoint: in_a[3] (input port clocked by clk)
Endpoint: _12026_ (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max
Corner: ss_n40C_1v60

    Delay      Time   Description
-------------------------------------------------------------
   0.0000    0.0000   clock clk (rise edge)
   0.0000    0.0000   clock network delay (ideal)
   5.5820    5.5820 ^ input external delay
   0.2813    5.8633 ^ in_a[3] (in)
   0.0000    5.8633 ^ _10760_/A (sky130_fd_sc_hd__nand2_1)
   0.2805    6.1438 v _10760_/Y (sky130_fd_sc_hd__nand2_1)
   0.0000    6.1438 v _10905_/B (sky130_fd_sc_hd__xnor3_1)
   0.9196    7.0634 v _10905_/X (sky130_fd_sc_hd__xnor3_1)
   0.0000    7.0634 v _10907_/B (sky130_fd_sc_hd__xnor2_1)
   0.6267    7.6902 ^ _10907_/Y (sky130_fd_sc_hd__xnor2_1)
   0.0000    7.6902 ^ _11029_/B (sky130_fd_sc_hd__xnor3_1)
   1.0379    8.7280 v _11029_/X (sky130_fd_sc_hd__xnor3_1)
   0.0000    8.7280 v _11087_/B (sky130_fd_sc_hd__xnor2_1)
   0.2727    9.0008 v _11087_/Y (sky130_fd_sc_hd__xnor2_1)
   0.0000    9.0008 v _11113_/A (sky130_fd_sc_hd__xnor2_1)
   0.6601    9.6608 ^ _11113_/Y (sky130_fd_sc_hd__xnor2_1)
   0.0000    9.6608 ^ _11186_/B (sky130_fd_sc_hd__xor3_1)
   1.0917   10.7525 v _11186_/X (sky130_fd_sc_hd__xor3_1)
   0.0000   10.7525 v _11255_/B (sky130_fd_sc_hd__xnor3_1)
   0.9265   11.6790 v _11255_/X (sky130_fd_sc_hd__xnor3_1)
   0.0000   11.6790 v _11257_/B (sky130_fd_sc_hd__xor2_1)
   0.3997   12.0787 ^ _11257_/X (sky130_fd_sc_hd__xor2_1)
   0.0000   12.0787 ^ _11302_/C (sky130_fd_sc_hd__xor3_1)
   0.7300   12.8086 v _11302_/X (sky130_fd_sc_hd__xor3_1)
   0.0000   12.8086 v _11306_/B (sky130_fd_sc_hd__maj3_1)
   0.9433   13.7519 v _11306_/X (sky130_fd_sc_hd__maj3_1)
   0.0000   13.7519 v _11338_/B (sky130_fd_sc_hd__xor3_1)
   0.9799   14.7319 v _11338_/X (sky130_fd_sc_hd__xor3_1)
   0.0000   14.7319 v _11340_/B (sky130_fd_sc_hd__xor2_1)
   0.4077   15.1396 ^ _11340_/X (sky130_fd_sc_hd__xor2_1)
   0.0000   15.1396 ^ _11416_/A1 (sky130_fd_sc_hd__a21oi_1)
   0.2608   15.4004 v _11416_/Y (sky130_fd_sc_hd__a21oi_1)
   0.0000   15.4004 v _11418_/C (sky130_fd_sc_hd__maj3_1)
   0.9285   16.3289 v _11418_/X (sky130_fd_sc_hd__maj3_1)
   0.0000   16.3289 v _11420_/A1 (sky130_fd_sc_hd__o21ai_0)
   0.5449   16.8738 ^ _11420_/Y (sky130_fd_sc_hd__o21ai_0)
   0.0000   16.8738 ^ _11421_/C (sky130_fd_sc_hd__maj3_1)
   0.5349   17.4087 ^ _11421_/X (sky130_fd_sc_hd__maj3_1)
   0.0000   17.4087 ^ _11422_/A2 (sky130_fd_sc_hd__a21oi_1)
   0.1799   17.5886 v _11422_/Y (sky130_fd_sc_hd__a21oi_1)
   0.0000   17.5886 v _11423_/C (sky130_fd_sc_hd__maj3_1)
   0.9453   18.5339 v _11423_/X (sky130_fd_sc_hd__maj3_1)
   0.0000   18.5339 v _11424_/C (sky130_fd_sc_hd__maj3_1)
   0.9406   19.4744 v _11424_/X (sky130_fd_sc_hd__maj3_1)
   0.0000   19.4744 v _11426_/A2 (sky130_fd_sc_hd__o21ai_0)
   0.5289   20.0033 ^ _11426_/Y (sky130_fd_sc_hd__o21ai_0)
   0.0000   20.0033 ^ _11427_/A2 (sky130_fd_sc_hd__a21oi_1)
   0.3197   20.3230 v _11427_/Y (sky130_fd_sc_hd__a21oi_1)
   0.0000   20.3230 v _11428_/C (sky130_fd_sc_hd__maj3_1)
   0.9447   21.2677 v _11428_/X (sky130_fd_sc_hd__maj3_1)
   0.0000   21.2677 v _11429_/C (sky130_fd_sc_hd__maj3_1)
   0.9456   22.2133 v _11429_/X (sky130_fd_sc_hd__maj3_1)
   0.0000   22.2133 v _11430_/A2 (sky130_fd_sc_hd__o21bai_1)
   0.4391   22.6525 ^ _11430_/Y (sky130_fd_sc_hd__o21bai_1)
   0.0000   22.6525 ^ _11431_/A2 (sky130_fd_sc_hd__a21oi_1)
   0.2517   22.9042 v _11431_/Y (sky130_fd_sc_hd__a21oi_1)
   0.0000   22.9042 v _11433_/A2 (sky130_fd_sc_hd__o21ai_0)
   0.5119   23.4161 ^ _11433_/Y (sky130_fd_sc_hd__o21ai_0)
   0.0000   23.4161 ^ _11434_/A2 (sky130_fd_sc_hd__a21oi_1)
   0.3357   23.7518 v _11434_/Y (sky130_fd_sc_hd__a21oi_1)
   0.0000   23.7518 v _11438_/A3 (sky130_fd_sc_hd__o31ai_1)
   0.8462   24.5980 ^ _11438_/Y (sky130_fd_sc_hd__o31ai_1)
   0.0000   24.5980 ^ _11440_/B2 (sky130_fd_sc_hd__a221oi_1)
   0.4326   25.0306 v _11440_/Y (sky130_fd_sc_hd__a221oi_1)
   0.0000   25.0306 v _11443_/A3 (sky130_fd_sc_hd__o311ai_0)
   1.0241   26.0547 ^ _11443_/Y (sky130_fd_sc_hd__o311ai_0)
   0.0000   26.0547 ^ _11446_/A3 (sky130_fd_sc_hd__a311oi_1)
   0.4919   26.5466 v _11446_/Y (sky130_fd_sc_hd__a311oi_1)
   0.0000   26.5466 v _11451_/A3 (sky130_fd_sc_hd__o311ai_0)
   0.8376   27.3842 ^ _11451_/Y (sky130_fd_sc_hd__o311ai_0)
   0.0000   27.3842 ^ _11453_/B (sky130_fd_sc_hd__nand2_1)
   0.3533   27.7374 v _11453_/Y (sky130_fd_sc_hd__nand2_1)
   0.0000   27.7374 v _11507_/B (sky130_fd_sc_hd__xnor2_1)
   0.2543   27.9918 v _11507_/Y (sky130_fd_sc_hd__xnor2_1)
   0.0000   27.9918 v _11509_/A1 (sky130_fd_sc_hd__o21ai_0)
   2.6362   30.6280 ^ _11509_/Y (sky130_fd_sc_hd__o21ai_0)
   0.0000   30.6280 ^ _11512_/B1 (sky130_fd_sc_hd__o21ai_0)
   0.8625   31.4905 v _11512_/Y (sky130_fd_sc_hd__o21ai_0)
   0.0000   31.4905 v _12026_/D (sky130_fd_sc_hd__dfxtp_1)
            31.4905   data arrival time

  27.9100   27.9100   clock clk (rise edge)
   0.0000   27.9100   clock network delay (ideal)
   0.0000   27.9100   clock reconvergence pessimism
            27.9100 ^ _12026_/CLK (sky130_fd_sc_hd__dfxtp_1)
  -0.5559   27.3541   library setup time
            27.3541   data required time
-------------------------------------------------------------
            27.3541   data required time
           -31.4905   data arrival time
-------------------------------------------------------------
            -4.1363   slack (VIOLATED)


PORT _908ecdedfb640000_p_Port
Warning 168: c2_query.tcl line 1, unknown field slack.
Warning 168: c2_query.tcl line 1, unknown field arrival.
Warning 168: c2_query.tcl line 1, unknown field required.
No paths found.
CASE02-CMD: set scene ss_n40C_1v60
ss_n40C_1v60
CASE02-CMD: foreach p [all_inputs -no_clocks] {
_f00696edfb640000_p_Port max 1 1 min 1 1
_c0987aedfb640000_p_Port max 1 1 min 1 1
_90ce95edfb640000_p_Port max 1 1 min 1 1
_9060cdedfb640000_p_Port max 1 1 min 1 1
_1061cdedfb640000_p_Port max 1 1 min 1 1
_9061cdedfb640000_p_Port max 1 1 min 1 1
_1062cdedfb640000_p_Port max 1 1 min 1 1
_9062cdedfb640000_p_Port max 1 1 min 1 1
_1063cdedfb640000_p_Port max 1 1 min 1 1
_9063cdedfb640000_p_Port max 1 1 min 1 1
_1064cdedfb640000_p_Port max 1 1 min 1 1
_9064cdedfb640000_p_Port max 1 1 min 1 1
_1065cdedfb640000_p_Port max 1 1 min 1 1
_9065cdedfb640000_p_Port max 1 1 min 1 1
_1066cdedfb640000_p_Port max 1 1 min 1 1
_9066cdedfb640000_p_Port max 1 1 min 1 1
_1067cdedfb640000_p_Port max 1 1 min 1 1
_9067cdedfb640000_p_Port max 1 1 min 1 1
_1068cdedfb640000_p_Port max 1 1 min 1 1
_9068cdedfb640000_p_Port max 1 1 min 1 1
_1069cdedfb640000_p_Port max 1 1 min 1 1
_9069cdedfb640000_p_Port max 1 1 min 1 1
_106acdedfb640000_p_Port max 1 1 min 1 1
_906acdedfb640000_p_Port max 1 1 min 1 1
_106bcdedfb640000_p_Port max 1 1 min 1 1
_906bcdedfb640000_p_Port max 1 1 min 1 1
_106ccdedfb640000_p_Port max 1 1 min 1 1
_906ccdedfb640000_p_Port max 1 1 min 1 1
_106dcdedfb640000_p_Port max 1 1 min 1 1
_906dcdedfb640000_p_Port max 1 1 min 1 1
_106ecdedfb640000_p_Port max 1 1 min 1 1
_906ecdedfb640000_p_Port max 1 1 min 1 1
_106fcdedfb640000_p_Port max 1 1 min 1 1
_906fcdedfb640000_p_Port max 1 1 min 1 1
_1070cdedfb640000_p_Port max 1 1 min 1 1
_9070cdedfb640000_p_Port max 1 1 min 1 1
_1071cdedfb640000_p_Port max 1 1 min 1 1
_9071cdedfb640000_p_Port max 1 1 min 1 1
_1072cdedfb640000_p_Port max 1 1 min 1 1
_9072cdedfb640000_p_Port max 1 1 min 1 1
_1073cdedfb640000_p_Port max 1 1 min 1 1
_9073cdedfb640000_p_Port max 1 1 min 1 1
_1074cdedfb640000_p_Port max 1 1 min 1 1
_9074cdedfb640000_p_Port max 1 1 min 1 1
_1075cdedfb640000_p_Port max 1 1 min 1 1
_9075cdedfb640000_p_Port max 1 1 min 1 1
_1076cdedfb640000_p_Port max 1 1 min 1 1
_9076cdedfb640000_p_Port max 1 1 min 1 1
_1077cdedfb640000_p_Port max 1 1 min 1 1
_9077cdedfb640000_p_Port max 1 1 min 1 1
_1078cdedfb640000_p_Port max 1 1 min 1 1
_9078cdedfb640000_p_Port max 1 1 min 1 1
_1079cdedfb640000_p_Port max 1 1 min 1 1
_9079cdedfb640000_p_Port max 1 1 min 1 1
_107acdedfb640000_p_Port max 1 1 min 1 1
_907acdedfb640000_p_Port max 1 1 min 1 1
_107bcdedfb640000_p_Port max 1 1 min 1 1
_907bcdedfb640000_p_Port max 1 1 min 1 1
_107ccdedfb640000_p_Port max 1 1 min 1 1
_907ccdedfb640000_p_Port max 1 1 min 1 1
_107dcdedfb640000_p_Port max 1 1 min 1 1
_907dcdedfb640000_p_Port max 1 1 min 1 1
_107ecdedfb640000_p_Port max 1 1 min 1 1
_907ecdedfb640000_p_Port max 1 1 min 1 1
_107fcdedfb640000_p_Port max 1 1 min 1 1
_907fcdedfb640000_p_Port max 1 1 min 1 1
_9080cdedfb640000_p_Port max 0 1 min 0 1
_1081cdedfb640000_p_Port max 0 1 min 0 1
_9081cdedfb640000_p_Port max 0 1 min 0 1
_1082cdedfb640000_p_Port max 0 1 min 0 1
_9082cdedfb640000_p_Port max 0 1 min 0 1
_1083cdedfb640000_p_Port max 0 1 min 0 1
_9083cdedfb640000_p_Port max 0 1 min 0 1
_1084cdedfb640000_p_Port max 0 1 min 0 1
_9084cdedfb640000_p_Port max 0 1 min 0 1
_1085cdedfb640000_p_Port max 0 1 min 0 1
_9085cdedfb640000_p_Port max 0 1 min 0 1
_1086cdedfb640000_p_Port max 0 1 min 0 1
_9086cdedfb640000_p_Port max 0 1 min 0 1
_1087cdedfb640000_p_Port max 0 1 min 0 1
_9087cdedfb640000_p_Port max 0 1 min 0 1
_1088cdedfb640000_p_Port max 0 1 min 0 1
_9088cdedfb640000_p_Port max 0 1 min 0 1
_1089cdedfb640000_p_Port max 0 1 min 0 1
_9089cdedfb640000_p_Port max 0 1 min 0 1
_108acdedfb640000_p_Port max 0 1 min 0 1
_908acdedfb640000_p_Port max 0 1 min 0 1
_108bcdedfb640000_p_Port max 0 1 min 0 1
_908bcdedfb640000_p_Port max 0 1 min 0 1
_108ccdedfb640000_p_Port max 0 1 min 0 1
_908ccdedfb640000_p_Port max 0 1 min 0 1
_108dcdedfb640000_p_Port max 0 1 min 0 1
_908dcdedfb640000_p_Port max 0 1 min 0 1
_108ecdedfb640000_p_Port max 0 1 min 0 1
_908ecdedfb640000_p_Port max 0 1 min 0 1
_108fcdedfb640000_p_Port max 0 1 min 0 1
_908fcdedfb640000_p_Port max 0 1 min 0 1
_1090cdedfb640000_p_Port max 0 1 min 0 1
_9090cdedfb640000_p_Port max 0 1 min 0 1
_1091cdedfb640000_p_Port max 0 1 min 0 1
_9091cdedfb640000_p_Port max 0 1 min 0 1
_1092cdedfb640000_p_Port max 0 1 min 0 1
_9092cdedfb640000_p_Port max 0 1 min 0 1
_1093cdedfb640000_p_Port max 0 1 min 0 1
_9093cdedfb640000_p_Port max 0 1 min 0 1
_1094cdedfb640000_p_Port max 0 1 min 0 1
_9094cdedfb640000_p_Port max 0 1 min 0 1
_1095cdedfb640000_p_Port max 0 1 min 0 1
_9095cdedfb640000_p_Port max 0 1 min 0 1
_1096cdedfb640000_p_Port max 0 1 min 0 1
_9096cdedfb640000_p_Port max 0 1 min 0 1
_1097cdedfb640000_p_Port max 0 1 min 0 1
_9097cdedfb640000_p_Port max 0 1 min 0 1
_1098cdedfb640000_p_Port max 0 1 min 0 1
_9098cdedfb640000_p_Port max 0 1 min 0 1
_1099cdedfb640000_p_Port max 0 1 min 0 1
_9099cdedfb640000_p_Port max 0 1 min 0 1
_109acdedfb640000_p_Port max 0 1 min 0 1
_909acdedfb640000_p_Port max 0 1 min 0 1
_109bcdedfb640000_p_Port max 0 1 min 0 1
_909bcdedfb640000_p_Port max 0 1 min 0 1
_109ccdedfb640000_p_Port max 0 1 min 0 1
_909ccdedfb640000_p_Port max 0 1 min 0 1
_109dcdedfb640000_p_Port max 0 1 min 0 1
_909dcdedfb640000_p_Port max 0 1 min 0 1
_109ecdedfb640000_p_Port max 0 1 min 0 1
_909ecdedfb640000_p_Port max 0 1 min 0 1
_109fcdedfb640000_p_Port max 0 1 min 0 1
_909fcdedfb640000_p_Port max 0 1 min 0 1
_10a0cdedfb640000_p_Port max 0 1 min 0 1
CASE02-CMD: set scene ss_n40C_1v60
ss_n40C_1v60
CASE02-CMD: foreach p [all_inputs -no_clocks] {
PORT _f00696edfb640000_p_Port
PORT _c0987aedfb640000_p_Port
PORT _90ce95edfb640000_p_Port
PORT _9060cdedfb640000_p_Port
PORT _1061cdedfb640000_p_Port
PORT _9061cdedfb640000_p_Port
PORT _1062cdedfb640000_p_Port
PORT _9062cdedfb640000_p_Port
PORT _1063cdedfb640000_p_Port
PORT _9063cdedfb640000_p_Port
PORT _1064cdedfb640000_p_Port
PORT _9064cdedfb640000_p_Port
PORT _1065cdedfb640000_p_Port
PORT _9065cdedfb640000_p_Port
PORT _1066cdedfb640000_p_Port
PORT _9066cdedfb640000_p_Port
PORT _1067cdedfb640000_p_Port
PORT _9067cdedfb640000_p_Port
PORT _1068cdedfb640000_p_Port
PORT _9068cdedfb640000_p_Port
PORT _1069cdedfb640000_p_Port
PORT _9069cdedfb640000_p_Port
PORT _106acdedfb640000_p_Port
PORT _906acdedfb640000_p_Port
PORT _106bcdedfb640000_p_Port
PORT _906bcdedfb640000_p_Port
PORT _106ccdedfb640000_p_Port
PORT _906ccdedfb640000_p_Port
PORT _106dcdedfb640000_p_Port
PORT _906dcdedfb640000_p_Port
PORT _106ecdedfb640000_p_Port
PORT _906ecdedfb640000_p_Port
PORT _106fcdedfb640000_p_Port
PORT _906fcdedfb640000_p_Port
PORT _1070cdedfb640000_p_Port
PORT _9070cdedfb640000_p_Port
PORT _1071cdedfb640000_p_Port
PORT _9071cdedfb640000_p_Port
PORT _1072cdedfb640000_p_Port
PORT _9072cdedfb640000_p_Port
PORT _1073cdedfb640000_p_Port
PORT _9073cdedfb640000_p_Port
PORT _1074cdedfb640000_p_Port
PORT _9074cdedfb640000_p_Port
PORT _1075cdedfb640000_p_Port
PORT _9075cdedfb640000_p_Port
PORT _1076cdedfb640000_p_Port
PORT _9076cdedfb640000_p_Port
PORT _1077cdedfb640000_p_Port
PORT _9077cdedfb640000_p_Port
PORT _1078cdedfb640000_p_Port
PORT _9078cdedfb640000_p_Port
PORT _1079cdedfb640000_p_Port
PORT _9079cdedfb640000_p_Port
PORT _107acdedfb640000_p_Port
PORT _907acdedfb640000_p_Port
PORT _107bcdedfb640000_p_Port
PORT _907bcdedfb640000_p_Port
PORT _107ccdedfb640000_p_Port
PORT _907ccdedfb640000_p_Port
PORT _107dcdedfb640000_p_Port
PORT _907dcdedfb640000_p_Port
PORT _107ecdedfb640000_p_Port
PORT _907ecdedfb640000_p_Port
PORT _107fcdedfb640000_p_Port
PORT _907fcdedfb640000_p_Port
PORT _9080cdedfb640000_p_Port
PORT _1081cdedfb640000_p_Port
PORT _9081cdedfb640000_p_Port
PORT _1082cdedfb640000_p_Port
PORT _9082cdedfb640000_p_Port
PORT _1083cdedfb640000_p_Port
PORT _9083cdedfb640000_p_Port
PORT _1084cdedfb640000_p_Port
PORT _9084cdedfb640000_p_Port
PORT _1085cdedfb640000_p_Port
PORT _9085cdedfb640000_p_Port
PORT _1086cdedfb640000_p_Port
PORT _9086cdedfb640000_p_Port
PORT _1087cdedfb640000_p_Port
PORT _9087cdedfb640000_p_Port
PORT _1088cdedfb640000_p_Port
PORT _9088cdedfb640000_p_Port
PORT _1089cdedfb640000_p_Port
PORT _9089cdedfb640000_p_Port
PORT _108acdedfb640000_p_Port
PORT _908acdedfb640000_p_Port
PORT _108bcdedfb640000_p_Port
PORT _908bcdedfb640000_p_Port
PORT _108ccdedfb640000_p_Port
PORT _908ccdedfb640000_p_Port
PORT _108dcdedfb640000_p_Port
PORT _908dcdedfb640000_p_Port
PORT _108ecdedfb640000_p_Port
PORT _908ecdedfb640000_p_Port
PORT _108fcdedfb640000_p_Port
PORT _908fcdedfb640000_p_Port
PORT _1090cdedfb640000_p_Port
PORT _9090cdedfb640000_p_Port
PORT _1091cdedfb640000_p_Port
PORT _9091cdedfb640000_p_Port
PORT _1092cdedfb640000_p_Port
PORT _9092cdedfb640000_p_Port
PORT _1093cdedfb640000_p_Port
PORT _9093cdedfb640000_p_Port
PORT _1094cdedfb640000_p_Port
PORT _9094cdedfb640000_p_Port
PORT _1095cdedfb640000_p_Port
PORT _9095cdedfb640000_p_Port
PORT _1096cdedfb640000_p_Port
PORT _9096cdedfb640000_p_Port
PORT _1097cdedfb640000_p_Port
PORT _9097cdedfb640000_p_Port
PORT _1098cdedfb640000_p_Port
PORT _9098cdedfb640000_p_Port
PORT _1099cdedfb640000_p_Port
PORT _9099cdedfb640000_p_Port
PORT _109acdedfb640000_p_Port
PORT _909acdedfb640000_p_Port
PORT _109bcdedfb640000_p_Port
PORT _909bcdedfb640000_p_Port
PORT _109ccdedfb640000_p_Port
PORT _909ccdedfb640000_p_Port
PORT _109dcdedfb640000_p_Port
PORT _909dcdedfb640000_p_Port
PORT _109ecdedfb640000_p_Port
PORT _909ecdedfb640000_p_Port
PORT _109fcdedfb640000_p_Port
PORT _909fcdedfb640000_p_Port
PORT _10a0cdedfb640000_p_Port
CASE02-CMD: foreach p [all_inputs -no_clocks] {
PORT _f00696edfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _c0987aedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _90ce95edfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _9060cdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _1061cdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _9061cdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _1062cdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _9062cdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _1063cdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _9063cdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _1064cdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _9064cdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _1065cdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _9065cdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _1066cdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _9066cdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _1067cdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _9067cdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _1068cdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _9068cdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _1069cdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _9069cdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _106acdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _906acdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _106bcdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _906bcdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _106ccdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _906ccdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _106dcdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _906dcdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _106ecdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _906ecdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _106fcdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _906fcdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _1070cdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _9070cdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _1071cdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _9071cdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _1072cdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _9072cdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _1073cdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _9073cdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _1074cdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _9074cdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _1075cdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _9075cdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _1076cdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _9076cdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _1077cdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _9077cdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _1078cdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _9078cdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _1079cdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _9079cdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _107acdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _907acdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _107bcdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _907bcdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _107ccdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _907ccdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _107dcdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _907dcdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _107ecdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _907ecdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _107fcdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _907fcdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _9080cdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _1081cdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _9081cdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _1082cdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _9082cdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _1083cdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _9083cdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _1084cdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _9084cdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _1085cdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _9085cdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _1086cdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _9086cdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _1087cdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _9087cdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _1088cdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _9088cdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _1089cdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _9089cdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _108acdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _908acdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _108bcdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _908bcdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _108ccdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _908ccdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _108dcdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _908dcdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _108ecdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _908ecdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _108fcdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _908fcdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _1090cdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _9090cdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _1091cdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _9091cdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _1092cdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _9092cdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _1093cdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _9093cdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _1094cdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _9094cdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _1095cdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _9095cdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _1096cdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _9096cdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _1097cdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _9097cdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _1098cdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _9098cdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _1099cdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _9099cdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _109acdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _909acdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _109bcdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _909bcdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _109ccdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _909ccdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _109dcdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _909dcdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _109ecdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _909ecdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _109fcdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _909fcdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _10a0cdedfb640000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
CASE02-CMD: foreach sc {tt_025C_1v80 tt_100C_1v80 ss_100C_1v60 ss_n40C_1v60 ff_n40C_1v95 ff_100C_1v95} {
tt_025C_1v80 max WS=11.191043075655372 TNS=0.0
tt_025C_1v80 min WS=0.09305387279663745 TNS=0.0
tt_100C_1v80 max WS=11.32117898139033 TNS=0.0
tt_100C_1v80 min WS=0.08983023607005908 TNS=0.0
ss_100C_1v60 max WS=-0.6799521138591476 TNS=-21.004391709342716
ss_100C_1v60 min WS=0.18567888030452087 TNS=0.0
ss_n40C_1v60 max WS=-4.172594832200332 TNS=-129.94064858564798
ss_n40C_1v60 min WS=0.18500412836443383 TNS=0.0
ff_n40C_1v95 max WS=15.881204356648498 TNS=0.0
ff_n40C_1v95 min WS=0.06347266641938298 TNS=0.0
ff_100C_1v95 max WS=15.90284571263497 TNS=0.0
ff_100C_1v95 min WS=0.059112952317363035 TNS=0.0
CASE02-CMD: set scene ss_n40C_1v60
ss_n40C_1v60
CASE02-CMD: set cn 0; set un 0
0
CASE02-CMD: foreach p [all_inputs -no_clocks] {
CASE02-CMD: puts "constrained_in2reg_max_endpoints=$cn unconstrained_only=$un"
constrained_in2reg_max_endpoints=66 unconstrained_only=64
```

### 查询 B1（R2）
你写的查询：
```tcl
# Q1（优先级1；对 R1 和 R2 都执行）
# 关键起点是否形成受约束的 in2reg max 路径
foreach p [get_ports {in_a[34] in_b[2] in_a[3] in_b[35]}] {
  puts "PORT $p"
  catch { report_checks -from $p -to [get_pins _12026_/D] -path_delay max \
           -scene ss_n40C_1v60 -fields {slack input_pins arrival required} -digits 4 }
}

# Q2（优先级1；对 R1 和 R2 都执行）
# 全非时钟输入逐端口计数：max/min，带/不带 -unconstrained
set scene ss_n40C_1v60
foreach p [all_inputs -no_clocks] {
  set n1 [llength [find_timing_paths -from $p -to [all_registers -data_pins] \
          -path_delay max -scene $scene]]
  set n2 [llength [find_timing_paths -from $p -to [all_registers -data_pins] \
          -path_delay max -scene $scene -unconstrained]]
  set n3 [llength [find_timing_paths -from $p -to [all_registers -data_pins] \
          -path_delay min -scene $scene]]
  set n4 [llength [find_timing_paths -from $p -to [all_registers -data_pins] \
          -path_delay min -scene $scene -unconstrained]]
  puts "$p max $n1 $n2 min $n3 $n4"
}

# Q3（优先级2；对 R1 和 R2 都执行）
# 比较全输入到 _12026_/D 的到达时间
set scene ss_n40C_1v60
foreach p [all_inputs -no_clocks] {
  puts "PORT $p"
  catch { report_arrival -from $p -to [get_pins _12026_/D] -scene $scene -digits 4 }
}

# Q4（优先级3；对 R1 和 R2 都执行）
# 读取每个非时钟输入端口的 input delay/driving 属性
foreach p [all_inputs -no_clocks] {
  puts "PORT $p"
  foreach prop {input_delay_max input_delay_min input_transition_rise input_transition_fall driving_cell} {
    if {[catch {set v [get_property $p $prop]}]} { set v "<no_property>" }
    puts "  $prop $v"
  }
}

# Q5（优先级2；对 R1 和 R2 都执行）
# 六 scene 全局最差/TNS，核验差异被限制在 in2reg max
foreach sc {tt_025C_1v80 tt_100C_1v80 ss_100C_1v60 ss_n40C_1v60 ff_n40C_1v95 ff_100C_1v95} {
  puts "$sc max WS=[worst_slack -max -scene $sc] TNS=[total_negative_slack -max -scene $sc]"
  puts "$sc min WS=[worst_slack -min -scene $sc] TNS=[total_negative_slack -min -scene $sc]"
}

# Q6（优先级3；对 R1 和 R2 都执行）
# 汇总每实例中被约束输入端口/仅 -unconstrained 可见的端口数
set scene ss_n40C_1v60
set cn 0; set un 0
foreach p [all_inputs -no_clocks] {
  set a [llength [find_timing_paths -from $p -to [all_registers -data_pins] \
         -path_delay max -scene $scene]]
  set b [llength [find_timing_paths -from $p -to [all_registers -data_pins] \
         -path_delay max -scene $scene -unconstrained]]
  if {$a > 0} { incr cn }
  if {$a == 0 && $b > 0} { incr un }
}
puts "constrained_in2reg_max_endpoints=$cn unconstrained_only=$un"
```
实际执行的命令：
```tcl
# Q1（优先级1；对 R1 和 R2 都执行）
# 关键起点是否形成受约束的 in2reg max 路径
foreach p [get_ports {in_a[34] in_b[2] in_a[3] in_b[35]}] {
  puts "PORT $p"
  catch { report_checks -from $p -to [get_pins _12026_/D] -path_delay max \
           -scene ss_n40C_1v60 -fields {slack input_pins arrival required} -digits 4 }
}

# Q2（优先级1；对 R1 和 R2 都执行）
# 全非时钟输入逐端口计数：max/min，带/不带 -unconstrained
set scene ss_n40C_1v60
foreach p [all_inputs -no_clocks] {
  set n1 [llength [find_timing_paths -from $p -to [all_registers -data_pins] \
          -path_delay max -scene $scene]]
  set n2 [llength [find_timing_paths -from $p -to [all_registers -data_pins] \
          -path_delay max -scene $scene -unconstrained]]
  set n3 [llength [find_timing_paths -from $p -to [all_registers -data_pins] \
          -path_delay min -scene $scene]]
  set n4 [llength [find_timing_paths -from $p -to [all_registers -data_pins] \
          -path_delay min -scene $scene -unconstrained]]
  puts "$p max $n1 $n2 min $n3 $n4"
}

# Q3（优先级2；对 R1 和 R2 都执行）
# 比较全输入到 _12026_/D 的到达时间
set scene ss_n40C_1v60
foreach p [all_inputs -no_clocks] {
  puts "PORT $p"
  catch { report_arrival -from $p -to [get_pins _12026_/D] -scene $scene -digits 4 }
}

# Q4（优先级3；对 R1 和 R2 都执行）
# 读取每个非时钟输入端口的 input delay/driving 属性
foreach p [all_inputs -no_clocks] {
  puts "PORT $p"
  foreach prop {input_delay_max input_delay_min input_transition_rise input_transition_fall driving_cell} {
    if {[catch {set v [get_property $p $prop]}]} { set v "<no_property>" }
    puts "  $prop $v"
  }
}

# Q5（优先级2；对 R1 和 R2 都执行）
# 六 scene 全局最差/TNS，核验差异被限制在 in2reg max
foreach sc {tt_025C_1v80 tt_100C_1v80 ss_100C_1v60 ss_n40C_1v60 ff_n40C_1v95 ff_100C_1v95} {
  puts "$sc max WS=[worst_slack -max -scene $sc] TNS=[total_negative_slack -max -scene $sc]"
  puts "$sc min WS=[worst_slack -min -scene $sc] TNS=[total_negative_slack -min -scene $sc]"
}

# Q6（优先级3；对 R1 和 R2 都执行）
# 汇总每实例中被约束输入端口/仅 -unconstrained 可见的端口数
set scene ss_n40C_1v60
set cn 0; set un 0
foreach p [all_inputs -no_clocks] {
  set a [llength [find_timing_paths -from $p -to [all_registers -data_pins] \
         -path_delay max -scene $scene]]
  set b [llength [find_timing_paths -from $p -to [all_registers -data_pins] \
         -path_delay max -scene $scene -unconstrained]]
  if {$a > 0} { incr cn }
  if {$a == 0 && $b > 0} { incr un }
}
puts "constrained_in2reg_max_endpoints=$cn unconstrained_only=$un"
```
机械改写：无
执行类型：原上下文；执行结果：语法错误；异常：-；归因：请求本身的问题
输出：
```text
CASE02-CMD: foreach p [get_ports {in_a[34] in_b[2] in_a[3] in_b[35]}] {
PORT _907e8a57db630000_p_Port
Warning 168: c2_query.tcl line 1, unknown field slack.
Warning 168: c2_query.tcl line 1, unknown field arrival.
Warning 168: c2_query.tcl line 1, unknown field required.
Startpoint: in_a[34] (input port clocked by clk)
Endpoint: _12026_ (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max
Corner: ss_n40C_1v60

    Delay      Time   Description
-------------------------------------------------------------
   0.0000    0.0000   clock clk (rise edge)
   0.0000    0.0000   clock network delay (ideal)
   5.5820    5.5820 ^ input external delay
   0.2730    5.8550 ^ in_a[34] (in)
   0.0000    5.8550 ^ _10564_/A (sky130_fd_sc_hd__and2_0)
   0.4006    6.2556 ^ _10564_/X (sky130_fd_sc_hd__and2_0)
   0.0000    6.2556 ^ _10854_/A (sky130_fd_sc_hd__xnor3_1)
   1.0188    7.2744 v _10854_/X (sky130_fd_sc_hd__xnor3_1)
   0.0000    7.2744 v _10985_/B (sky130_fd_sc_hd__xor3_1)
   0.9736    8.2480 v _10985_/X (sky130_fd_sc_hd__xor3_1)
   0.0000    8.2480 v _10986_/B (sky130_fd_sc_hd__xor2_1)
   0.4475    8.6955 ^ _10986_/X (sky130_fd_sc_hd__xor2_1)
   0.0000    8.6955 ^ _11069_/B (sky130_fd_sc_hd__xor2_1)
   0.4045    9.1000 ^ _11069_/X (sky130_fd_sc_hd__xor2_1)
   0.0000    9.1000 ^ _11071_/C (sky130_fd_sc_hd__nand3_1)
   0.2403    9.3403 v _11071_/Y (sky130_fd_sc_hd__nand3_1)
   0.0000    9.3403 v _11073_/B (sky130_fd_sc_hd__xor3_1)
   0.9973   10.3376 v _11073_/X (sky130_fd_sc_hd__xor3_1)
   0.0000   10.3376 v _11149_/A (sky130_fd_sc_hd__xnor2_1)
   0.5470   10.8846 ^ _11149_/Y (sky130_fd_sc_hd__xnor2_1)
   0.0000   10.8846 ^ _11228_/B (sky130_fd_sc_hd__xnor3_1)
   0.9809   11.8655 v _11228_/X (sky130_fd_sc_hd__xnor3_1)
   0.0000   11.8655 v _11302_/B (sky130_fd_sc_hd__xor3_1)
   0.9794   12.8449 v _11302_/X (sky130_fd_sc_hd__xor3_1)
   0.0000   12.8449 v _11306_/B (sky130_fd_sc_hd__maj3_1)
   0.9433   13.7882 v _11306_/X (sky130_fd_sc_hd__maj3_1)
   0.0000   13.7882 v _11338_/B (sky130_fd_sc_hd__xor3_1)
   0.9799   14.7681 v _11338_/X (sky130_fd_sc_hd__xor3_1)
   0.0000   14.7681 v _11340_/B (sky130_fd_sc_hd__xor2_1)
   0.4077   15.1758 ^ _11340_/X (sky130_fd_sc_hd__xor2_1)
   0.0000   15.1758 ^ _11416_/A1 (sky130_fd_sc_hd__a21oi_1)
   0.2608   15.4366 v _11416_/Y (sky130_fd_sc_hd__a21oi_1)
   0.0000   15.4366 v _11418_/C (sky130_fd_sc_hd__maj3_1)
   0.9285   16.3652 v _11418_/X (sky130_fd_sc_hd__maj3_1)
   0.0000   16.3652 v _11420_/A1 (sky130_fd_sc_hd__o21ai_0)
   0.5449   16.9101 ^ _11420_/Y (sky130_fd_sc_hd__o21ai_0)
   0.0000   16.9101 ^ _11421_/C (sky130_fd_sc_hd__maj3_1)
   0.5349   17.4450 ^ _11421_/X (sky130_fd_sc_hd__maj3_1)
   0.0000   17.4450 ^ _11422_/A2 (sky130_fd_sc_hd__a21oi_1)
   0.1799   17.6249 v _11422_/Y (sky130_fd_sc_hd__a21oi_1)
   0.0000   17.6249 v _11423_/C (sky130_fd_sc_hd__maj3_1)
   0.9453   18.5701 v _11423_/X (sky130_fd_sc_hd__maj3_1)
   0.0000   18.5701 v _11424_/C (sky130_fd_sc_hd__maj3_1)
   0.9406   19.5107 v _11424_/X (sky130_fd_sc_hd__maj3_1)
   0.0000   19.5107 v _11426_/A2 (sky130_fd_sc_hd__o21ai_0)
   0.5289   20.0396 ^ _11426_/Y (sky130_fd_sc_hd__o21ai_0)
   0.0000   20.0396 ^ _11427_/A2 (sky130_fd_sc_hd__a21oi_1)
   0.3197   20.3593 v _11427_/Y (sky130_fd_sc_hd__a21oi_1)
   0.0000   20.3593 v _11428_/C (sky130_fd_sc_hd__maj3_1)
   0.9447   21.3040 v _11428_/X (sky130_fd_sc_hd__maj3_1)
   0.0000   21.3040 v _11429_/C (sky130_fd_sc_hd__maj3_1)
   0.9456   22.2496 v _11429_/X (sky130_fd_sc_hd__maj3_1)
   0.0000   22.2496 v _11430_/A2 (sky130_fd_sc_hd__o21bai_1)
   0.4391   22.6887 ^ _11430_/Y (sky130_fd_sc_hd__o21bai_1)
   0.0000   22.6887 ^ _11431_/A2 (sky130_fd_sc_hd__a21oi_1)
   0.2517   22.9404 v _11431_/Y (sky130_fd_sc_hd__a21oi_1)
   0.0000   22.9404 v _11433_/A2 (sky130_fd_sc_hd__o21ai_0)
   0.5119   23.4524 ^ _11433_/Y (sky130_fd_sc_hd__o21ai_0)
   0.0000   23.4524 ^ _11434_/A2 (sky130_fd_sc_hd__a21oi_1)
   0.3357   23.7880 v _11434_/Y (sky130_fd_sc_hd__a21oi_1)
   0.0000   23.7880 v _11438_/A3 (sky130_fd_sc_hd__o31ai_1)
   0.8462   24.6343 ^ _11438_/Y (sky130_fd_sc_hd__o31ai_1)
   0.0000   24.6343 ^ _11440_/B2 (sky130_fd_sc_hd__a221oi_1)
   0.4326   25.0668 v _11440_/Y (sky130_fd_sc_hd__a221oi_1)
   0.0000   25.0668 v _11443_/A3 (sky130_fd_sc_hd__o311ai_0)
   1.0241   26.0910 ^ _11443_/Y (sky130_fd_sc_hd__o311ai_0)
   0.0000   26.0910 ^ _11446_/A3 (sky130_fd_sc_hd__a311oi_1)
   0.4919   26.5829 v _11446_/Y (sky130_fd_sc_hd__a311oi_1)
   0.0000   26.5829 v _11451_/A3 (sky130_fd_sc_hd__o311ai_0)
   0.8376   27.4205 ^ _11451_/Y (sky130_fd_sc_hd__o311ai_0)
   0.0000   27.4205 ^ _11453_/B (sky130_fd_sc_hd__nand2_1)
   0.3533   27.7737 v _11453_/Y (sky130_fd_sc_hd__nand2_1)
   0.0000   27.7737 v _11507_/B (sky130_fd_sc_hd__xnor2_1)
   0.2543   28.0280 v _11507_/Y (sky130_fd_sc_hd__xnor2_1)
   0.0000   28.0280 v _11509_/A1 (sky130_fd_sc_hd__o21ai_0)
   2.6362   30.6642 ^ _11509_/Y (sky130_fd_sc_hd__o21ai_0)
   0.0000   30.6642 ^ _11512_/B1 (sky130_fd_sc_hd__o21ai_0)
   0.8625   31.5267 v _11512_/Y (sky130_fd_sc_hd__o21ai_0)
   0.0000   31.5267 v _12026_/D (sky130_fd_sc_hd__dfxtp_1)
            31.5267   data arrival time

  27.9100   27.9100   clock clk (rise edge)
   0.0000   27.9100   clock network delay (ideal)
   0.0000   27.9100   clock reconvergence pessimism
            27.9100 ^ _12026_/CLK (sky130_fd_sc_hd__dfxtp_1)
  -0.5559   27.3541   library setup time
            27.3541   data required time
-------------------------------------------------------------
            27.3541   data required time
           -31.5267   data arrival time
-------------------------------------------------------------
            -4.1726   slack (VIOLATED)


PORT _10af8a57db630000_p_Port
Warning 168: c2_query.tcl line 1, unknown field slack.
Warning 168: c2_query.tcl line 1, unknown field arrival.
Warning 168: c2_query.tcl line 1, unknown field required.
Startpoint: in_b[2] (input port clocked by clk)
Endpoint: _12026_ (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max
Corner: ss_n40C_1v60

    Delay      Time   Description
-------------------------------------------------------------
   0.0000    0.0000   clock clk (rise edge)
   0.0000    0.0000   clock network delay (ideal)
   5.5820    5.5820 ^ input external delay
   0.3091    5.8911 ^ in_b[2] (in)
   0.0000    5.8911 ^ _10621_/B (sky130_fd_sc_hd__nand2_1)
   0.2453    6.1365 v _10621_/Y (sky130_fd_sc_hd__nand2_1)
   0.0000    6.1365 v _10905_/A (sky130_fd_sc_hd__xnor3_1)
   0.9804    7.1168 v _10905_/X (sky130_fd_sc_hd__xnor3_1)
   0.0000    7.1168 v _10907_/B (sky130_fd_sc_hd__xnor2_1)
   0.6267    7.7436 ^ _10907_/Y (sky130_fd_sc_hd__xnor2_1)
   0.0000    7.7436 ^ _11029_/B (sky130_fd_sc_hd__xnor3_1)
   1.0379    8.7814 v _11029_/X (sky130_fd_sc_hd__xnor3_1)
   0.0000    8.7814 v _11087_/B (sky130_fd_sc_hd__xnor2_1)
   0.2727    9.0542 v _11087_/Y (sky130_fd_sc_hd__xnor2_1)
   0.0000    9.0542 v _11113_/A (sky130_fd_sc_hd__xnor2_1)
   0.6601    9.7142 ^ _11113_/Y (sky130_fd_sc_hd__xnor2_1)
   0.0000    9.7142 ^ _11186_/B (sky130_fd_sc_hd__xor3_1)
   1.0917   10.8059 v _11186_/X (sky130_fd_sc_hd__xor3_1)
   0.0000   10.8059 v _11255_/B (sky130_fd_sc_hd__xnor3_1)
   0.9265   11.7324 v _11255_/X (sky130_fd_sc_hd__xnor3_1)
   0.0000   11.7324 v _11257_/B (sky130_fd_sc_hd__xor2_1)
   0.3997   12.1321 ^ _11257_/X (sky130_fd_sc_hd__xor2_1)
   0.0000   12.1321 ^ _11302_/C (sky130_fd_sc_hd__xor3_1)
   0.7300   12.8620 v _11302_/X (sky130_fd_sc_hd__xor3_1)
   0.0000   12.8620 v _11306_/B (sky130_fd_sc_hd__maj3_1)
   0.9433   13.8053 v _11306_/X (sky130_fd_sc_hd__maj3_1)
   0.0000   13.8053 v _11338_/B (sky130_fd_sc_hd__xor3_1)
   0.9799   14.7852 v _11338_/X (sky130_fd_sc_hd__xor3_1)
   0.0000   14.7852 v _11340_/B (sky130_fd_sc_hd__xor2_1)
   0.4077   15.1930 ^ _11340_/X (sky130_fd_sc_hd__xor2_1)
   0.0000   15.1930 ^ _11416_/A1 (sky130_fd_sc_hd__a21oi_1)
   0.2608   15.4538 v _11416_/Y (sky130_fd_sc_hd__a21oi_1)
   0.0000   15.4538 v _11418_/C (sky130_fd_sc_hd__maj3_1)
   0.9285   16.3823 v _11418_/X (sky130_fd_sc_hd__maj3_1)
   0.0000   16.3823 v _11420_/A1 (sky130_fd_sc_hd__o21ai_0)
   0.5449   16.9272 ^ _11420_/Y (sky130_fd_sc_hd__o21ai_0)
   0.0000   16.9272 ^ _11421_/C (sky130_fd_sc_hd__maj3_1)
   0.5349   17.4621 ^ _11421_/X (sky130_fd_sc_hd__maj3_1)
   0.0000   17.4621 ^ _11422_/A2 (sky130_fd_sc_hd__a21oi_1)
   0.1799   17.6420 v _11422_/Y (sky130_fd_sc_hd__a21oi_1)
   0.0000   17.6420 v _11423_/C (sky130_fd_sc_hd__maj3_1)
   0.9453   18.5873 v _11423_/X (sky130_fd_sc_hd__maj3_1)
   0.0000   18.5873 v _11424_/C (sky130_fd_sc_hd__maj3_1)
   0.9406   19.5278 v _11424_/X (sky130_fd_sc_hd__maj3_1)
   0.0000   19.5278 v _11426_/A2 (sky130_fd_sc_hd__o21ai_0)
   0.5289   20.0567 ^ _11426_/Y (sky130_fd_sc_hd__o21ai_0)
   0.0000   20.0567 ^ _11427_/A2 (sky130_fd_sc_hd__a21oi_1)
   0.3197   20.3764 v _11427_/Y (sky130_fd_sc_hd__a21oi_1)
   0.0000   20.3764 v _11428_/C (sky130_fd_sc_hd__maj3_1)
   0.9447   21.3211 v _11428_/X (sky130_fd_sc_hd__maj3_1)
   0.0000   21.3211 v _11429_/C (sky130_fd_sc_hd__maj3_1)
   0.9456   22.2667 v _11429_/X (sky130_fd_sc_hd__maj3_1)
   0.0000   22.2667 v _11430_/A2 (sky130_fd_sc_hd__o21bai_1)
   0.4391   22.7059 ^ _11430_/Y (sky130_fd_sc_hd__o21bai_1)
   0.0000   22.7059 ^ _11431_/A2 (sky130_fd_sc_hd__a21oi_1)
   0.2517   22.9576 v _11431_/Y (sky130_fd_sc_hd__a21oi_1)
   0.0000   22.9576 v _11433_/A2 (sky130_fd_sc_hd__o21ai_0)
   0.5119   23.4695 ^ _11433_/Y (sky130_fd_sc_hd__o21ai_0)
   0.0000   23.4695 ^ _11434_/A2 (sky130_fd_sc_hd__a21oi_1)
   0.3357   23.8052 v _11434_/Y (sky130_fd_sc_hd__a21oi_1)
   0.0000   23.8052 v _11438_/A3 (sky130_fd_sc_hd__o31ai_1)
   0.8462   24.6514 ^ _11438_/Y (sky130_fd_sc_hd__o31ai_1)
   0.0000   24.6514 ^ _11440_/B2 (sky130_fd_sc_hd__a221oi_1)
   0.4326   25.0840 v _11440_/Y (sky130_fd_sc_hd__a221oi_1)
   0.0000   25.0840 v _11443_/A3 (sky130_fd_sc_hd__o311ai_0)
   1.0241   26.1081 ^ _11443_/Y (sky130_fd_sc_hd__o311ai_0)
   0.0000   26.1081 ^ _11446_/A3 (sky130_fd_sc_hd__a311oi_1)
   0.4919   26.6000 v _11446_/Y (sky130_fd_sc_hd__a311oi_1)
   0.0000   26.6000 v _11451_/A3 (sky130_fd_sc_hd__o311ai_0)
   0.8376   27.4376 ^ _11451_/Y (sky130_fd_sc_hd__o311ai_0)
   0.0000   27.4376 ^ _11453_/B (sky130_fd_sc_hd__nand2_1)
   0.3533   27.7908 v _11453_/Y (sky130_fd_sc_hd__nand2_1)
   0.0000   27.7908 v _11507_/B (sky130_fd_sc_hd__xnor2_1)
   0.2543   28.0452 v _11507_/Y (sky130_fd_sc_hd__xnor2_1)
   0.0000   28.0452 v _11509_/A1 (sky130_fd_sc_hd__o21ai_0)
   2.6362   30.6814 ^ _11509_/Y (sky130_fd_sc_hd__o21ai_0)
   0.0000   30.6814 ^ _11512_/B1 (sky130_fd_sc_hd__o21ai_0)
   0.8625   31.5439 v _11512_/Y (sky130_fd_sc_hd__o21ai_0)
   0.0000   31.5439 v _12026_/D (sky130_fd_sc_hd__dfxtp_1)
            31.5439   data arrival time

  27.9100   27.9100   clock clk (rise edge)
   0.0000   27.9100   clock network delay (ideal)
   0.0000   27.9100   clock reconvergence pessimism
            27.9100 ^ _12026_/CLK (sky130_fd_sc_hd__dfxtp_1)
  -0.5559   27.3541   library setup time
            27.3541   data required time
-------------------------------------------------------------
            27.3541   data required time
           -31.5439   data arrival time
-------------------------------------------------------------
            -4.1897   slack (VIOLATED)


PORT _108e8a57db630000_p_Port
Warning 168: c2_query.tcl line 1, unknown field slack.
Warning 168: c2_query.tcl line 1, unknown field arrival.
Warning 168: c2_query.tcl line 1, unknown field required.
Startpoint: in_a[3] (input port clocked by clk)
Endpoint: _12026_ (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max
Corner: ss_n40C_1v60

    Delay      Time   Description
-------------------------------------------------------------
   0.0000    0.0000   clock clk (rise edge)
   0.0000    0.0000   clock network delay (ideal)
   5.5820    5.5820 ^ input external delay
   0.2813    5.8633 ^ in_a[3] (in)
   0.0000    5.8633 ^ _10760_/A (sky130_fd_sc_hd__nand2_1)
   0.2805    6.1438 v _10760_/Y (sky130_fd_sc_hd__nand2_1)
   0.0000    6.1438 v _10905_/B (sky130_fd_sc_hd__xnor3_1)
   0.9196    7.0634 v _10905_/X (sky130_fd_sc_hd__xnor3_1)
   0.0000    7.0634 v _10907_/B (sky130_fd_sc_hd__xnor2_1)
   0.6267    7.6902 ^ _10907_/Y (sky130_fd_sc_hd__xnor2_1)
   0.0000    7.6902 ^ _11029_/B (sky130_fd_sc_hd__xnor3_1)
   1.0379    8.7280 v _11029_/X (sky130_fd_sc_hd__xnor3_1)
   0.0000    8.7280 v _11087_/B (sky130_fd_sc_hd__xnor2_1)
   0.2727    9.0008 v _11087_/Y (sky130_fd_sc_hd__xnor2_1)
   0.0000    9.0008 v _11113_/A (sky130_fd_sc_hd__xnor2_1)
   0.6601    9.6608 ^ _11113_/Y (sky130_fd_sc_hd__xnor2_1)
   0.0000    9.6608 ^ _11186_/B (sky130_fd_sc_hd__xor3_1)
   1.0917   10.7525 v _11186_/X (sky130_fd_sc_hd__xor3_1)
   0.0000   10.7525 v _11255_/B (sky130_fd_sc_hd__xnor3_1)
   0.9265   11.6790 v _11255_/X (sky130_fd_sc_hd__xnor3_1)
   0.0000   11.6790 v _11257_/B (sky130_fd_sc_hd__xor2_1)
   0.3997   12.0787 ^ _11257_/X (sky130_fd_sc_hd__xor2_1)
   0.0000   12.0787 ^ _11302_/C (sky130_fd_sc_hd__xor3_1)
   0.7300   12.8086 v _11302_/X (sky130_fd_sc_hd__xor3_1)
   0.0000   12.8086 v _11306_/B (sky130_fd_sc_hd__maj3_1)
   0.9433   13.7519 v _11306_/X (sky130_fd_sc_hd__maj3_1)
   0.0000   13.7519 v _11338_/B (sky130_fd_sc_hd__xor3_1)
   0.9799   14.7319 v _11338_/X (sky130_fd_sc_hd__xor3_1)
   0.0000   14.7319 v _11340_/B (sky130_fd_sc_hd__xor2_1)
   0.4077   15.1396 ^ _11340_/X (sky130_fd_sc_hd__xor2_1)
   0.0000   15.1396 ^ _11416_/A1 (sky130_fd_sc_hd__a21oi_1)
   0.2608   15.4004 v _11416_/Y (sky130_fd_sc_hd__a21oi_1)
   0.0000   15.4004 v _11418_/C (sky130_fd_sc_hd__maj3_1)
   0.9285   16.3289 v _11418_/X (sky130_fd_sc_hd__maj3_1)
   0.0000   16.3289 v _11420_/A1 (sky130_fd_sc_hd__o21ai_0)
   0.5449   16.8738 ^ _11420_/Y (sky130_fd_sc_hd__o21ai_0)
   0.0000   16.8738 ^ _11421_/C (sky130_fd_sc_hd__maj3_1)
   0.5349   17.4087 ^ _11421_/X (sky130_fd_sc_hd__maj3_1)
   0.0000   17.4087 ^ _11422_/A2 (sky130_fd_sc_hd__a21oi_1)
   0.1799   17.5886 v _11422_/Y (sky130_fd_sc_hd__a21oi_1)
   0.0000   17.5886 v _11423_/C (sky130_fd_sc_hd__maj3_1)
   0.9453   18.5339 v _11423_/X (sky130_fd_sc_hd__maj3_1)
   0.0000   18.5339 v _11424_/C (sky130_fd_sc_hd__maj3_1)
   0.9406   19.4744 v _11424_/X (sky130_fd_sc_hd__maj3_1)
   0.0000   19.4744 v _11426_/A2 (sky130_fd_sc_hd__o21ai_0)
   0.5289   20.0033 ^ _11426_/Y (sky130_fd_sc_hd__o21ai_0)
   0.0000   20.0033 ^ _11427_/A2 (sky130_fd_sc_hd__a21oi_1)
   0.3197   20.3230 v _11427_/Y (sky130_fd_sc_hd__a21oi_1)
   0.0000   20.3230 v _11428_/C (sky130_fd_sc_hd__maj3_1)
   0.9447   21.2677 v _11428_/X (sky130_fd_sc_hd__maj3_1)
   0.0000   21.2677 v _11429_/C (sky130_fd_sc_hd__maj3_1)
   0.9456   22.2133 v _11429_/X (sky130_fd_sc_hd__maj3_1)
   0.0000   22.2133 v _11430_/A2 (sky130_fd_sc_hd__o21bai_1)
   0.4391   22.6525 ^ _11430_/Y (sky130_fd_sc_hd__o21bai_1)
   0.0000   22.6525 ^ _11431_/A2 (sky130_fd_sc_hd__a21oi_1)
   0.2517   22.9042 v _11431_/Y (sky130_fd_sc_hd__a21oi_1)
   0.0000   22.9042 v _11433_/A2 (sky130_fd_sc_hd__o21ai_0)
   0.5119   23.4161 ^ _11433_/Y (sky130_fd_sc_hd__o21ai_0)
   0.0000   23.4161 ^ _11434_/A2 (sky130_fd_sc_hd__a21oi_1)
   0.3357   23.7518 v _11434_/Y (sky130_fd_sc_hd__a21oi_1)
   0.0000   23.7518 v _11438_/A3 (sky130_fd_sc_hd__o31ai_1)
   0.8462   24.5980 ^ _11438_/Y (sky130_fd_sc_hd__o31ai_1)
   0.0000   24.5980 ^ _11440_/B2 (sky130_fd_sc_hd__a221oi_1)
   0.4326   25.0306 v _11440_/Y (sky130_fd_sc_hd__a221oi_1)
   0.0000   25.0306 v _11443_/A3 (sky130_fd_sc_hd__o311ai_0)
   1.0241   26.0547 ^ _11443_/Y (sky130_fd_sc_hd__o311ai_0)
   0.0000   26.0547 ^ _11446_/A3 (sky130_fd_sc_hd__a311oi_1)
   0.4919   26.5466 v _11446_/Y (sky130_fd_sc_hd__a311oi_1)
   0.0000   26.5466 v _11451_/A3 (sky130_fd_sc_hd__o311ai_0)
   0.8376   27.3842 ^ _11451_/Y (sky130_fd_sc_hd__o311ai_0)
   0.0000   27.3842 ^ _11453_/B (sky130_fd_sc_hd__nand2_1)
   0.3533   27.7374 v _11453_/Y (sky130_fd_sc_hd__nand2_1)
   0.0000   27.7374 v _11507_/B (sky130_fd_sc_hd__xnor2_1)
   0.2543   27.9918 v _11507_/Y (sky130_fd_sc_hd__xnor2_1)
   0.0000   27.9918 v _11509_/A1 (sky130_fd_sc_hd__o21ai_0)
   2.6362   30.6280 ^ _11509_/Y (sky130_fd_sc_hd__o21ai_0)
   0.0000   30.6280 ^ _11512_/B1 (sky130_fd_sc_hd__o21ai_0)
   0.8625   31.4905 v _11512_/Y (sky130_fd_sc_hd__o21ai_0)
   0.0000   31.4905 v _12026_/D (sky130_fd_sc_hd__dfxtp_1)
            31.4905   data arrival time

  27.9100   27.9100   clock clk (rise edge)
   0.0000   27.9100   clock network delay (ideal)
   0.0000   27.9100   clock reconvergence pessimism
            27.9100 ^ _12026_/CLK (sky130_fd_sc_hd__dfxtp_1)
  -0.5559   27.3541   library setup time
            27.3541   data required time
-------------------------------------------------------------
            27.3541   data required time
           -31.4905   data arrival time
-------------------------------------------------------------
            -4.1363   slack (VIOLATED)


PORT _909e8a57db630000_p_Port
Warning 168: c2_query.tcl line 1, unknown field slack.
Warning 168: c2_query.tcl line 1, unknown field arrival.
Warning 168: c2_query.tcl line 1, unknown field required.
Startpoint: in_b[35] (input port clocked by clk)
Endpoint: _12026_ (rising edge-triggered flip-flop clocked by clk)
Path Group: clk
Path Type: max
Corner: ss_n40C_1v60

    Delay      Time   Description
-------------------------------------------------------------
   0.0000    0.0000   clock clk (rise edge)
   0.0000    0.0000   clock network delay (ideal)
   5.5820    5.5820 ^ input external delay
   0.2787    5.8607 ^ in_b[35] (in)
   0.0000    5.8607 ^ _10564_/B (sky130_fd_sc_hd__and2_0)
   0.4031    6.2638 ^ _10564_/X (sky130_fd_sc_hd__and2_0)
   0.0000    6.2638 ^ _10854_/A (sky130_fd_sc_hd__xnor3_1)
   1.0188    7.2826 v _10854_/X (sky130_fd_sc_hd__xnor3_1)
   0.0000    7.2826 v _10985_/B (sky130_fd_sc_hd__xor3_1)
   0.9736    8.2562 v _10985_/X (sky130_fd_sc_hd__xor3_1)
   0.0000    8.2562 v _10986_/B (sky130_fd_sc_hd__xor2_1)
   0.4475    8.7037 ^ _10986_/X (sky130_fd_sc_hd__xor2_1)
   0.0000    8.7037 ^ _11069_/B (sky130_fd_sc_hd__xor2_1)
   0.4045    9.1082 ^ _11069_/X (sky130_fd_sc_hd__xor2_1)
   0.0000    9.1082 ^ _11071_/C (sky130_fd_sc_hd__nand3_1)
   0.2403    9.3485 v _11071_/Y (sky130_fd_sc_hd__nand3_1)
   0.0000    9.3485 v _11073_/B (sky130_fd_sc_hd__xor3_1)
   0.9973   10.3458 v _11073_/X (sky130_fd_sc_hd__xor3_1)
   0.0000   10.3458 v _11149_/A (sky130_fd_sc_hd__xnor2_1)
   0.5470   10.8928 ^ _11149_/Y (sky130_fd_sc_hd__xnor2_1)
   0.0000   10.8928 ^ _11228_/B (sky130_fd_sc_hd__xnor3_1)
   0.9809   11.8738 v _11228_/X (sky130_fd_sc_hd__xnor3_1)
   0.0000   11.8738 v _11302_/B (sky130_fd_sc_hd__xor3_1)
   0.9794   12.8531 v _11302_/X (sky130_fd_sc_hd__xor3_1)
   0.0000   12.8531 v _11306_/B (sky130_fd_sc_hd__maj3_1)
   0.9433   13.7964 v _11306_/X (sky130_fd_sc_hd__maj3_1)
   0.0000   13.7964 v _11338_/B (sky130_fd_sc_hd__xor3_1)
   0.9799   14.7763 v _11338_/X (sky130_fd_sc_hd__xor3_1)
   0.0000   14.7763 v _11340_/B (sky130_fd_sc_hd__xor2_1)
   0.4077   15.1841 ^ _11340_/X (sky130_fd_sc_hd__xor2_1)
   0.0000   15.1841 ^ _11416_/A1 (sky130_fd_sc_hd__a21oi_1)
   0.2608   15.4449 v _11416_/Y (sky130_fd_sc_hd__a21oi_1)
   0.0000   15.4449 v _11418_/C (sky130_fd_sc_hd__maj3_1)
   0.9285   16.3734 v _11418_/X (sky130_fd_sc_hd__maj3_1)
   0.0000   16.3734 v _11420_/A1 (sky130_fd_sc_hd__o21ai_0)
   0.5449   16.9183 ^ _11420_/Y (sky130_fd_sc_hd__o21ai_0)
   0.0000   16.9183 ^ _11421_/C (sky130_fd_sc_hd__maj3_1)
   0.5349   17.4532 ^ _11421_/X (sky130_fd_sc_hd__maj3_1)
   0.0000   17.4532 ^ _11422_/A2 (sky130_fd_sc_hd__a21oi_1)
   0.1799   17.6331 v _11422_/Y (sky130_fd_sc_hd__a21oi_1)
   0.0000   17.6331 v _11423_/C (sky130_fd_sc_hd__maj3_1)
   0.9453   18.5783 v _11423_/X (sky130_fd_sc_hd__maj3_1)
   0.0000   18.5783 v _11424_/C (sky130_fd_sc_hd__maj3_1)
   0.9406   19.5189 v _11424_/X (sky130_fd_sc_hd__maj3_1)
   0.0000   19.5189 v _11426_/A2 (sky130_fd_sc_hd__o21ai_0)
   0.5289   20.0478 ^ _11426_/Y (sky130_fd_sc_hd__o21ai_0)
   0.0000   20.0478 ^ _11427_/A2 (sky130_fd_sc_hd__a21oi_1)
   0.3197   20.3675 v _11427_/Y (sky130_fd_sc_hd__a21oi_1)
   0.0000   20.3675 v _11428_/C (sky130_fd_sc_hd__maj3_1)
   0.9447   21.3122 v _11428_/X (sky130_fd_sc_hd__maj3_1)
   0.0000   21.3122 v _11429_/C (sky130_fd_sc_hd__maj3_1)
   0.9456   22.2578 v _11429_/X (sky130_fd_sc_hd__maj3_1)
   0.0000   22.2578 v _11430_/A2 (sky130_fd_sc_hd__o21bai_1)
   0.4391   22.6969 ^ _11430_/Y (sky130_fd_sc_hd__o21bai_1)
   0.0000   22.6969 ^ _11431_/A2 (sky130_fd_sc_hd__a21oi_1)
   0.2517   22.9486 v _11431_/Y (sky130_fd_sc_hd__a21oi_1)
   0.0000   22.9486 v _11433_/A2 (sky130_fd_sc_hd__o21ai_0)
   0.5119   23.4606 ^ _11433_/Y (sky130_fd_sc_hd__o21ai_0)
   0.0000   23.4606 ^ _11434_/A2 (sky130_fd_sc_hd__a21oi_1)
   0.3357   23.7962 v _11434_/Y (sky130_fd_sc_hd__a21oi_1)
   0.0000   23.7962 v _11438_/A3 (sky130_fd_sc_hd__o31ai_1)
   0.8462   24.6425 ^ _11438_/Y (sky130_fd_sc_hd__o31ai_1)
   0.0000   24.6425 ^ _11440_/B2 (sky130_fd_sc_hd__a221oi_1)
   0.4326   25.0751 v _11440_/Y (sky130_fd_sc_hd__a221oi_1)
   0.0000   25.0751 v _11443_/A3 (sky130_fd_sc_hd__o311ai_0)
   1.0241   26.0992 ^ _11443_/Y (sky130_fd_sc_hd__o311ai_0)
   0.0000   26.0992 ^ _11446_/A3 (sky130_fd_sc_hd__a311oi_1)
   0.4919   26.5911 v _11446_/Y (sky130_fd_sc_hd__a311oi_1)
   0.0000   26.5911 v _11451_/A3 (sky130_fd_sc_hd__o311ai_0)
   0.8376   27.4287 ^ _11451_/Y (sky130_fd_sc_hd__o311ai_0)
   0.0000   27.4287 ^ _11453_/B (sky130_fd_sc_hd__nand2_1)
   0.3533   27.7819 v _11453_/Y (sky130_fd_sc_hd__nand2_1)
   0.0000   27.7819 v _11507_/B (sky130_fd_sc_hd__xnor2_1)
   0.2543   28.0363 v _11507_/Y (sky130_fd_sc_hd__xnor2_1)
   0.0000   28.0363 v _11509_/A1 (sky130_fd_sc_hd__o21ai_0)
   2.6362   30.6724 ^ _11509_/Y (sky130_fd_sc_hd__o21ai_0)
   0.0000   30.6724 ^ _11512_/B1 (sky130_fd_sc_hd__o21ai_0)
   0.8625   31.5350 v _11512_/Y (sky130_fd_sc_hd__o21ai_0)
   0.0000   31.5350 v _12026_/D (sky130_fd_sc_hd__dfxtp_1)
            31.5350   data arrival time

  27.9100   27.9100   clock clk (rise edge)
   0.0000   27.9100   clock network delay (ideal)
   0.0000   27.9100   clock reconvergence pessimism
            27.9100 ^ _12026_/CLK (sky130_fd_sc_hd__dfxtp_1)
  -0.5559   27.3541   library setup time
            27.3541   data required time
-------------------------------------------------------------
            27.3541   data required time
           -31.5350   data arrival time
-------------------------------------------------------------
            -4.1808   slack (VIOLATED)


CASE02-CMD: set scene ss_n40C_1v60
ss_n40C_1v60
CASE02-CMD: foreach p [all_inputs -no_clocks] {
_f0165357db630000_p_Port max 1 1 min 1 1
_c0a83757db630000_p_Port max 1 1 min 1 1
_90de5257db630000_p_Port max 1 1 min 1 1
_90708a57db630000_p_Port max 1 1 min 1 1
_10718a57db630000_p_Port max 1 1 min 1 1
_90718a57db630000_p_Port max 1 1 min 1 1
_10728a57db630000_p_Port max 1 1 min 1 1
_90728a57db630000_p_Port max 1 1 min 1 1
_10738a57db630000_p_Port max 1 1 min 1 1
_90738a57db630000_p_Port max 1 1 min 1 1
_10748a57db630000_p_Port max 1 1 min 1 1
_90748a57db630000_p_Port max 1 1 min 1 1
_10758a57db630000_p_Port max 1 1 min 1 1
_90758a57db630000_p_Port max 1 1 min 1 1
_10768a57db630000_p_Port max 1 1 min 1 1
_90768a57db630000_p_Port max 1 1 min 1 1
_10778a57db630000_p_Port max 1 1 min 1 1
_90778a57db630000_p_Port max 1 1 min 1 1
_10788a57db630000_p_Port max 1 1 min 1 1
_90788a57db630000_p_Port max 1 1 min 1 1
_10798a57db630000_p_Port max 1 1 min 1 1
_90798a57db630000_p_Port max 1 1 min 1 1
_107a8a57db630000_p_Port max 1 1 min 1 1
_907a8a57db630000_p_Port max 1 1 min 1 1
_107b8a57db630000_p_Port max 1 1 min 1 1
_907b8a57db630000_p_Port max 1 1 min 1 1
_107c8a57db630000_p_Port max 1 1 min 1 1
_907c8a57db630000_p_Port max 1 1 min 1 1
_107d8a57db630000_p_Port max 1 1 min 1 1
_907d8a57db630000_p_Port max 1 1 min 1 1
_107e8a57db630000_p_Port max 1 1 min 1 1
_907e8a57db630000_p_Port max 1 1 min 1 1
_107f8a57db630000_p_Port max 1 1 min 1 1
_907f8a57db630000_p_Port max 1 1 min 1 1
_10808a57db630000_p_Port max 1 1 min 1 1
_90808a57db630000_p_Port max 1 1 min 1 1
_10818a57db630000_p_Port max 1 1 min 1 1
_90818a57db630000_p_Port max 1 1 min 1 1
_10828a57db630000_p_Port max 1 1 min 1 1
_90828a57db630000_p_Port max 1 1 min 1 1
_10838a57db630000_p_Port max 1 1 min 1 1
_90838a57db630000_p_Port max 1 1 min 1 1
_10848a57db630000_p_Port max 1 1 min 1 1
_90848a57db630000_p_Port max 1 1 min 1 1
_10858a57db630000_p_Port max 1 1 min 1 1
_90858a57db630000_p_Port max 1 1 min 1 1
_10868a57db630000_p_Port max 1 1 min 1 1
_90868a57db630000_p_Port max 1 1 min 1 1
_10878a57db630000_p_Port max 1 1 min 1 1
_90878a57db630000_p_Port max 1 1 min 1 1
_10888a57db630000_p_Port max 1 1 min 1 1
_90888a57db630000_p_Port max 1 1 min 1 1
_10898a57db630000_p_Port max 1 1 min 1 1
_90898a57db630000_p_Port max 1 1 min 1 1
_108a8a57db630000_p_Port max 1 1 min 1 1
_908a8a57db630000_p_Port max 1 1 min 1 1
_108b8a57db630000_p_Port max 1 1 min 1 1
_908b8a57db630000_p_Port max 1 1 min 1 1
_108c8a57db630000_p_Port max 1 1 min 1 1
_908c8a57db630000_p_Port max 1 1 min 1 1
_108d8a57db630000_p_Port max 1 1 min 1 1
_908d8a57db630000_p_Port max 1 1 min 1 1
_108e8a57db630000_p_Port max 1 1 min 1 1
_908e8a57db630000_p_Port max 1 1 min 1 1
_108f8a57db630000_p_Port max 1 1 min 1 1
_908f8a57db630000_p_Port max 1 1 min 1 1
_90908a57db630000_p_Port max 1 1 min 1 1
_10918a57db630000_p_Port max 1 1 min 1 1
_90918a57db630000_p_Port max 1 1 min 1 1
_10928a57db630000_p_Port max 1 1 min 1 1
_90928a57db630000_p_Port max 1 1 min 1 1
_10938a57db630000_p_Port max 1 1 min 1 1
_90938a57db630000_p_Port max 1 1 min 1 1
_10948a57db630000_p_Port max 1 1 min 1 1
_90948a57db630000_p_Port max 1 1 min 1 1
_10958a57db630000_p_Port max 1 1 min 1 1
_90958a57db630000_p_Port max 1 1 min 1 1
_10968a57db630000_p_Port max 1 1 min 1 1
_90968a57db630000_p_Port max 1 1 min 1 1
_10978a57db630000_p_Port max 1 1 min 1 1
_90978a57db630000_p_Port max 1 1 min 1 1
_10988a57db630000_p_Port max 1 1 min 1 1
_90988a57db630000_p_Port max 1 1 min 1 1
_10998a57db630000_p_Port max 1 1 min 1 1
_90998a57db630000_p_Port max 1 1 min 1 1
_109a8a57db630000_p_Port max 1 1 min 1 1
_909a8a57db630000_p_Port max 1 1 min 1 1
_109b8a57db630000_p_Port max 1 1 min 1 1
_909b8a57db630000_p_Port max 1 1 min 1 1
_109c8a57db630000_p_Port max 1 1 min 1 1
_909c8a57db630000_p_Port max 1 1 min 1 1
_109d8a57db630000_p_Port max 1 1 min 1 1
_909d8a57db630000_p_Port max 1 1 min 1 1
_109e8a57db630000_p_Port max 1 1 min 1 1
_909e8a57db630000_p_Port max 1 1 min 1 1
_109f8a57db630000_p_Port max 1 1 min 1 1
_909f8a57db630000_p_Port max 1 1 min 1 1
_10a08a57db630000_p_Port max 1 1 min 1 1
_90a08a57db630000_p_Port max 1 1 min 1 1
_10a18a57db630000_p_Port max 1 1 min 1 1
_90a18a57db630000_p_Port max 1 1 min 1 1
_10a28a57db630000_p_Port max 1 1 min 1 1
_90a28a57db630000_p_Port max 1 1 min 1 1
_10a38a57db630000_p_Port max 1 1 min 1 1
_90a38a57db630000_p_Port max 1 1 min 1 1
_10a48a57db630000_p_Port max 1 1 min 1 1
_90a48a57db630000_p_Port max 1 1 min 1 1
_10a58a57db630000_p_Port max 1 1 min 1 1
_90a58a57db630000_p_Port max 1 1 min 1 1
_10a68a57db630000_p_Port max 1 1 min 1 1
_90a68a57db630000_p_Port max 1 1 min 1 1
_10a78a57db630000_p_Port max 1 1 min 1 1
_90a78a57db630000_p_Port max 1 1 min 1 1
_10a88a57db630000_p_Port max 1 1 min 1 1
_90a88a57db630000_p_Port max 1 1 min 1 1
_10a98a57db630000_p_Port max 1 1 min 1 1
_90a98a57db630000_p_Port max 1 1 min 1 1
_10aa8a57db630000_p_Port max 1 1 min 1 1
_90aa8a57db630000_p_Port max 1 1 min 1 1
_10ab8a57db630000_p_Port max 1 1 min 1 1
_90ab8a57db630000_p_Port max 1 1 min 1 1
_10ac8a57db630000_p_Port max 1 1 min 1 1
_90ac8a57db630000_p_Port max 1 1 min 1 1
_10ad8a57db630000_p_Port max 1 1 min 1 1
_90ad8a57db630000_p_Port max 1 1 min 1 1
_10ae8a57db630000_p_Port max 1 1 min 1 1
_90ae8a57db630000_p_Port max 1 1 min 1 1
_10af8a57db630000_p_Port max 1 1 min 1 1
_90af8a57db630000_p_Port max 1 1 min 1 1
_10b08a57db630000_p_Port max 1 1 min 1 1
CASE02-CMD: set scene ss_n40C_1v60
ss_n40C_1v60
CASE02-CMD: foreach p [all_inputs -no_clocks] {
PORT _f0165357db630000_p_Port
PORT _c0a83757db630000_p_Port
PORT _90de5257db630000_p_Port
PORT _90708a57db630000_p_Port
PORT _10718a57db630000_p_Port
PORT _90718a57db630000_p_Port
PORT _10728a57db630000_p_Port
PORT _90728a57db630000_p_Port
PORT _10738a57db630000_p_Port
PORT _90738a57db630000_p_Port
PORT _10748a57db630000_p_Port
PORT _90748a57db630000_p_Port
PORT _10758a57db630000_p_Port
PORT _90758a57db630000_p_Port
PORT _10768a57db630000_p_Port
PORT _90768a57db630000_p_Port
PORT _10778a57db630000_p_Port
PORT _90778a57db630000_p_Port
PORT _10788a57db630000_p_Port
PORT _90788a57db630000_p_Port
PORT _10798a57db630000_p_Port
PORT _90798a57db630000_p_Port
PORT _107a8a57db630000_p_Port
PORT _907a8a57db630000_p_Port
PORT _107b8a57db630000_p_Port
PORT _907b8a57db630000_p_Port
PORT _107c8a57db630000_p_Port
PORT _907c8a57db630000_p_Port
PORT _107d8a57db630000_p_Port
PORT _907d8a57db630000_p_Port
PORT _107e8a57db630000_p_Port
PORT _907e8a57db630000_p_Port
PORT _107f8a57db630000_p_Port
PORT _907f8a57db630000_p_Port
PORT _10808a57db630000_p_Port
PORT _90808a57db630000_p_Port
PORT _10818a57db630000_p_Port
PORT _90818a57db630000_p_Port
PORT _10828a57db630000_p_Port
PORT _90828a57db630000_p_Port
PORT _10838a57db630000_p_Port
PORT _90838a57db630000_p_Port
PORT _10848a57db630000_p_Port
PORT _90848a57db630000_p_Port
PORT _10858a57db630000_p_Port
PORT _90858a57db630000_p_Port
PORT _10868a57db630000_p_Port
PORT _90868a57db630000_p_Port
PORT _10878a57db630000_p_Port
PORT _90878a57db630000_p_Port
PORT _10888a57db630000_p_Port
PORT _90888a57db630000_p_Port
PORT _10898a57db630000_p_Port
PORT _90898a57db630000_p_Port
PORT _108a8a57db630000_p_Port
PORT _908a8a57db630000_p_Port
PORT _108b8a57db630000_p_Port
PORT _908b8a57db630000_p_Port
PORT _108c8a57db630000_p_Port
PORT _908c8a57db630000_p_Port
PORT _108d8a57db630000_p_Port
PORT _908d8a57db630000_p_Port
PORT _108e8a57db630000_p_Port
PORT _908e8a57db630000_p_Port
PORT _108f8a57db630000_p_Port
PORT _908f8a57db630000_p_Port
PORT _90908a57db630000_p_Port
PORT _10918a57db630000_p_Port
PORT _90918a57db630000_p_Port
PORT _10928a57db630000_p_Port
PORT _90928a57db630000_p_Port
PORT _10938a57db630000_p_Port
PORT _90938a57db630000_p_Port
PORT _10948a57db630000_p_Port
PORT _90948a57db630000_p_Port
PORT _10958a57db630000_p_Port
PORT _90958a57db630000_p_Port
PORT _10968a57db630000_p_Port
PORT _90968a57db630000_p_Port
PORT _10978a57db630000_p_Port
PORT _90978a57db630000_p_Port
PORT _10988a57db630000_p_Port
PORT _90988a57db630000_p_Port
PORT _10998a57db630000_p_Port
PORT _90998a57db630000_p_Port
PORT _109a8a57db630000_p_Port
PORT _909a8a57db630000_p_Port
PORT _109b8a57db630000_p_Port
PORT _909b8a57db630000_p_Port
PORT _109c8a57db630000_p_Port
PORT _909c8a57db630000_p_Port
PORT _109d8a57db630000_p_Port
PORT _909d8a57db630000_p_Port
PORT _109e8a57db630000_p_Port
PORT _909e8a57db630000_p_Port
PORT _109f8a57db630000_p_Port
PORT _909f8a57db630000_p_Port
PORT _10a08a57db630000_p_Port
PORT _90a08a57db630000_p_Port
PORT _10a18a57db630000_p_Port
PORT _90a18a57db630000_p_Port
PORT _10a28a57db630000_p_Port
PORT _90a28a57db630000_p_Port
PORT _10a38a57db630000_p_Port
PORT _90a38a57db630000_p_Port
PORT _10a48a57db630000_p_Port
PORT _90a48a57db630000_p_Port
PORT _10a58a57db630000_p_Port
PORT _90a58a57db630000_p_Port
PORT _10a68a57db630000_p_Port
PORT _90a68a57db630000_p_Port
PORT _10a78a57db630000_p_Port
PORT _90a78a57db630000_p_Port
PORT _10a88a57db630000_p_Port
PORT _90a88a57db630000_p_Port
PORT _10a98a57db630000_p_Port
PORT _90a98a57db630000_p_Port
PORT _10aa8a57db630000_p_Port
PORT _90aa8a57db630000_p_Port
PORT _10ab8a57db630000_p_Port
PORT _90ab8a57db630000_p_Port
PORT _10ac8a57db630000_p_Port
PORT _90ac8a57db630000_p_Port
PORT _10ad8a57db630000_p_Port
PORT _90ad8a57db630000_p_Port
PORT _10ae8a57db630000_p_Port
PORT _90ae8a57db630000_p_Port
PORT _10af8a57db630000_p_Port
PORT _90af8a57db630000_p_Port
PORT _10b08a57db630000_p_Port
CASE02-CMD: foreach p [all_inputs -no_clocks] {
PORT _f0165357db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _c0a83757db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _90de5257db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _90708a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _10718a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _90718a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _10728a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _90728a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _10738a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _90738a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _10748a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _90748a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _10758a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _90758a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _10768a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _90768a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _10778a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _90778a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _10788a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _90788a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _10798a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _90798a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _107a8a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _907a8a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _107b8a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _907b8a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _107c8a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _907c8a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _107d8a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _907d8a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _107e8a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _907e8a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _107f8a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _907f8a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _10808a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _90808a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _10818a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _90818a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _10828a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _90828a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _10838a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _90838a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _10848a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _90848a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _10858a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _90858a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _10868a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _90868a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _10878a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _90878a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _10888a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _90888a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _10898a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _90898a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _108a8a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _908a8a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _108b8a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _908b8a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _108c8a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _908c8a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _108d8a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _908d8a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _108e8a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _908e8a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _108f8a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _908f8a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _90908a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _10918a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _90918a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _10928a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _90928a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _10938a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _90938a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _10948a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _90948a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _10958a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _90958a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _10968a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _90968a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _10978a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _90978a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _10988a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _90988a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _10998a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _90998a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _109a8a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _909a8a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _109b8a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _909b8a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _109c8a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _909c8a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _109d8a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _909d8a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _109e8a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _909e8a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _109f8a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _909f8a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _10a08a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _90a08a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _10a18a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _90a18a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _10a28a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _90a28a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _10a38a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _90a38a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _10a48a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _90a48a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _10a58a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _90a58a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _10a68a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _90a68a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _10a78a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _90a78a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _10a88a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _90a88a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _10a98a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _90a98a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _10aa8a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _90aa8a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _10ab8a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _90ab8a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _10ac8a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _90ac8a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _10ad8a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _90ad8a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _10ae8a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _90ae8a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _10af8a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _90af8a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
PORT _10b08a57db630000_p_Port
  input_delay_max <no_property>
  input_delay_min <no_property>
  input_transition_rise <no_property>
  input_transition_fall <no_property>
  driving_cell <no_property>
CASE02-CMD: foreach sc {tt_025C_1v80 tt_100C_1v80 ss_100C_1v60 ss_n40C_1v60 ff_n40C_1v95 ff_100C_1v95} {
tt_025C_1v80 max WS=11.185458209594348 TNS=0.0
tt_025C_1v80 min WS=0.09305387279663745 TNS=0.0
tt_100C_1v80 max WS=11.317221258240215 TNS=0.0
tt_100C_1v80 min WS=0.08983023607005908 TNS=0.0
ss_100C_1v60 max WS=-0.687277809672019 TNS=-21.231488279541733
ss_100C_1v60 min WS=0.18567888030452087 TNS=0.0
ss_n40C_1v60 max WS=-4.189726018044011 TNS=-130.4888465326457
ss_n40C_1v60 min WS=0.18500412836443383 TNS=0.0
ff_n40C_1v95 max WS=15.871505448031069 TNS=0.0
ff_n40C_1v95 min WS=0.06347266641938298 TNS=0.0
ff_100C_1v95 max WS=15.894228605363333 TNS=0.0
ff_100C_1v95 min WS=0.059112952317363035 TNS=0.0
CASE02-CMD: set scene ss_n40C_1v60
ss_n40C_1v60
CASE02-CMD: set cn 0; set un 0
0
CASE02-CMD: foreach p [all_inputs -no_clocks] {
CASE02-CMD: puts "constrained_in2reg_max_endpoints=$cn unconstrained_only=$un"
constrained_in2reg_max_endpoints=130 unconstrained_only=0
```

## 预算账单

① 总预算：600000 token（每 token 约 1.91 字节的保守换算；本次已交还合计 62141 token，含本账单）。

② 已交还的实例：
- B1 R1：1290 行，未截断
- B1 R2：1492 行，未截断

③ 未交还的实例：（无）

④ 以上未交还的结果已完整归档，未交还原因是累计超过公开的总预算，不是查询失败。

根据这些结果，确认或修正你第 1 轮的判断，栏位不变。
