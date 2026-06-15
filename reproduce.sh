#!/usr/bin/env bash
# Reproduce every figure in results/ from scratch.
# Equilibrium / ignition / NOx are fast; the 1-D flames are the slow part and
# are generated with a resumable helper (rerun until it prints COMPLETE).
set -e
python -m src.run equilibrium ignition nox

for job in flame_phi_air flame_phi_oxy flame_phi_egr flame_egr_speed flame_oxy_speed; do
    until python gen_incremental.py "$job" | tee /dev/stderr | grep -q COMPLETE; do
        echo "  ... resuming $job"
    done
done

python -m src.run flame_plots
echo "All figures regenerated in results/"
