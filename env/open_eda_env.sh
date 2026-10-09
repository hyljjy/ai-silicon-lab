# === Open-source EDA environment (Ubuntu-24.04) ===
if [ -z "${OPEN_EDA_ENV:-}" ]; then
  export OPEN_EDA_ENV=1
  export TOOLS=$HOME/tools
  export PATH=$TOOLS/opensta/bin:$PATH
  # Appended, not prepended: bin/ has generic names (lsusb, dot, openocd...) that must not shadow system tools.
  # Never source oss-cad-suite/environment: it prepends bin/ and py3bin/ (Python 3.11) and shadows system python3. See docs/env/TOOL_ISSUES.md TOOL-009.
  export PATH=$PATH:$TOOLS/oss-cad-suite/bin
  # Sky130 PDK (ciel-managed, sky130_fd_sc_hd only); helper scripts in $SKY130_KIT
  export PDK_ROOT=$HOME/pdk
  export PDK=sky130A
  export SKY130_HD=$PDK_ROOT/$PDK/libs.ref/sky130_fd_sc_hd
  export SKY130_KIT=$PDK_ROOT/sky130hd_kit
fi
