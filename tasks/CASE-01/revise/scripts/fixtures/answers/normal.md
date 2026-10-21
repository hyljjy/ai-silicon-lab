Here is my change.

## RTL

```verilog
module dot4sat(input clk);
  // normal
endmodule
```

DECLARED_L = 2

## 预测表

| id | action | metric | check | corner | category | value_kind | direction | low | high | unit | point | basis |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| P1 | add pipeline register after multiplier | slack | setup | all | reg2reg | delta | 改善 | 0.5 | 2.0 | ns | 1.2 | dot4sat.v:40 |
| P2 | two-stage output | L | | | | | | | | | 2 | dot4sat.v:12 |

## 失败条件

- F-a: setup slack at corner ss does not improve versus baseline
- the area exceeds the cap
  continued second line
1. numbered item

## 其他说明

- not a failure condition
