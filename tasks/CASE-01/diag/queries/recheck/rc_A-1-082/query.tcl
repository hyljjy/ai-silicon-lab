# 全网表非寄存器单元按驱动尺寸后缀（_0、_1、_2、_4 …）计数（用于 A-1-082）
set total 0
foreach c [get_cells *] {
  set ref [get_property $c ref_name]
  if {[string match *dfxtp* $ref]} { continue }
  if {[regexp {_([0-9]+)$} $ref -> s]} { incr cnt($s) } else { incr cnt(none) }
  incr total
}
foreach s [lsort [array names cnt]] { puts "size _$s: $cnt($s)" }
puts "non-register cells: $total"
