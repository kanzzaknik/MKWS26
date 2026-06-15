"""Command-line orchestration: compute results, save CSVs, render figures.

Usage:
    python -m src.run equilibrium     # Tad sweeps (fast)
    python -m src.run ignition        # ignition-delay sweeps (fast)
    python -m src.run nox             # equilibrium NO sweeps (fast)
    python -m src.run flame_air|flame_egr|flame_oxy|flame_dilution   # 1-D flames
    python -m src.run flame_plots     # assemble flame figures from cache
    python -m src.run all             # everything in sequence
"""
import sys
import os
import numpy as np
import matplotlib.pyplot as plt

from . import equilibrium as eq
from . import kinetics as kin
from . import flame as fl
from . import plots as P


# ---------------------------------------------------------------- equilibrium
def run_equilibrium():
    d = eq.sweep_diluent_tad()
    P.save_csv("tad_vs_diluent.csv", d)
    for sp in ("N2", "CO2", "H2O"):
        plt.plot(d["fraction"] * 100, d[sp], "-o", color=P.C[sp], label=sp)
    plt.xlabel("Added diluent mole fraction [%]")
    plt.ylabel("Adiabatic flame temperature [K]")
    plt.title("Effect of diluent species on $T_{ad}$ (CH$_4$/air, $\\phi=1$)")
    plt.legend()
    P._fig("fig1_tad_vs_diluent.png")

    d = eq.sweep_phi_tad()
    P.save_csv("tad_vs_phi.csv", d)
    plt.plot(d["phi"], d["air"], "-o", color=P.C["air"], label="Air")
    plt.plot(d["phi"], d["oxy"], "-s", color=P.C["oxy"], label="Oxy-fuel (O$_2$/CO$_2$, 21% O$_2$)")
    plt.plot(d["phi"], d["egr"], "-^", color=P.C["egr"], label="EGR 20%")
    plt.xlabel("Equivalence ratio $\\phi$ [-]")
    plt.ylabel("Adiabatic flame temperature [K]")
    plt.title("$T_{ad}$ vs equivalence ratio")
    plt.legend()
    P._fig("fig2_tad_vs_phi.png")


# ---------------------------------------------------------------- ignition
def run_ignition():
    cases = {"air": "Air", "oxy": "Oxy-fuel (21% O$_2$)", "egr": "EGR 20%"}
    store = {}
    for c, lab in cases.items():
        r = kin.sweep_temperature(c)
        store["T"] = r["T"]
        store[c] = r["tau"]
        plt.semilogy(1000.0 / r["T"], r["tau"], "-o", color=P.C[c], label=lab)
    P.save_csv("ignition_arrhenius.csv", store)
    plt.xlabel("1000 / T [1/K]")
    plt.ylabel("Ignition delay $\\tau$ [s]")
    plt.title("Auto-ignition delay (CH$_4$, $\\phi=1$, 5 atm)")
    plt.legend()
    P._fig("fig5_ignition_arrhenius.png")

    r = kin.sweep_egr_ignition()
    P.save_csv("ignition_vs_egr.csv", r)
    plt.plot(r["egr_fraction"] * 100, np.asarray(r["tau"]) * 1e3, "-o", color=P.C["egr"])
    plt.xlabel("EGR fraction [%]")
    plt.ylabel("Ignition delay $\\tau$ [ms]")
    plt.title("Ignition delay vs EGR fraction (CH$_4$, $\\phi=1$, 1100 K, 5 atm)")
    P._fig("fig6_ignition_vs_egr.png")


# ---------------------------------------------------------------- NOx
def run_nox():
    d = eq.sweep_nox_phi()
    P.save_csv("nox_vs_phi.csv", d)
    plt.plot(d["phi"], d["air"], "-o", color=P.C["air"], label="Air")
    plt.plot(d["phi"], d["oxy"], "-s", color=P.C["oxy"], label="Oxy-fuel (21% O$_2$)")
    plt.plot(d["phi"], d["egr"], "-^", color=P.C["egr"], label="EGR 20%")
    plt.xlabel("Equivalence ratio $\\phi$ [-]")
    plt.ylabel("Equilibrium NO [ppm]")
    plt.title("Equilibrium NO vs equivalence ratio")
    plt.legend()
    P._fig("fig7_nox_vs_phi.png")

    d = eq.sweep_egr()
    P.save_csv("tad_no_vs_egr.csv", d)
    fig, ax1 = plt.subplots()
    ax2 = ax1.twinx()
    ax1.plot(d["egr_fraction"] * 100, d["Tad"], "-o", color=P.C["air"])
    ax2.plot(d["egr_fraction"] * 100, d["NO_ppm"], "-s", color=P.C["egr"])
    ax1.set_xlabel("EGR fraction [%]")
    ax1.set_ylabel("Adiabatic flame temperature [K]", color=P.C["air"])
    ax2.set_ylabel("Equilibrium NO [ppm]", color=P.C["egr"])
    ax1.tick_params(axis="y", labelcolor=P.C["air"])
    ax2.tick_params(axis="y", labelcolor=P.C["egr"])
    ax2.grid(False)
    plt.title("EGR lowers flame temperature and suppresses NO")
    P._fig("fig8_tad_no_vs_egr.png")


# ---------------------------------------------------------------- 1-D flames
def _cache(name, data):
    np.savez(os.path.join(P.DATA, name + ".npz"), **data)
    print("  cached", name)


def run_flame_case(case):
    r = fl.sweep_phi(case)
    _cache("flame_phi_" + case, r)
    P.save_csv("flame_phi_%s.csv" % case, r)


def run_flame_dilution():
    e = fl.sweep_egr_speed()
    o = fl.sweep_oxy_speed()
    _cache("flame_egr_speed", e)
    _cache("flame_oxy_speed", o)
    P.save_csv("flame_egr_speed.csv", e)
    P.save_csv("flame_oxy_speed.csv", o)


def _read_csv(name):
    import csv
    cols = {}
    with open(os.path.join(P.DATA, name)) as fh:
        r = csv.reader(fh)
        keys = next(r)
        for k in keys:
            cols[k] = []
        for row in r:
            for k, v in zip(keys, row):
                cols[k].append(float(v))
    return {k: np.asarray(v) for k, v in cols.items()}


def run_flame_plots():
    d = {c: _read_csv("flame_phi_%s.csv" % c) for c in ("air", "egr", "oxy")}
    styles = {"air": ("-o", "Air"), "egr": ("-^", "EGR 10%"),
              "oxy": ("-s", "Oxy-fuel (30% O$_2$)")}
    for c, (st, lab) in styles.items():
        plt.plot(d[c]["phi"], d[c]["SL"] * 100, st, color=P.C[c], label=lab)
    plt.xlabel("Equivalence ratio $\\phi$ [-]")
    plt.ylabel("Laminar flame speed $S_L$ [cm/s]")
    plt.title("Laminar flame speed vs equivalence ratio")
    plt.legend()
    P._fig("fig3_flamespeed_vs_phi.png")

    e = _read_csv("flame_egr_speed.csv")
    o = _read_csv("flame_oxy_speed.csv")
    fig, ax1 = plt.subplots()
    ax2 = ax1.twiny()
    l1, = ax1.plot(e["egr_fraction"] * 100, e["SL"] * 100, "-^", color=P.C["egr"], label="EGR dilution")
    l2, = ax2.plot(o["x_o2"] * 100, o["SL"] * 100, "-s", color=P.C["oxy"], label="Oxy O$_2$ fraction")
    ax1.set_xlabel("EGR fraction [%]", color=P.C["egr"])
    ax2.set_xlabel("O$_2$ mole fraction in O$_2$/CO$_2$ oxidiser [%]", color=P.C["oxy"])
    ax1.set_ylabel("Laminar flame speed $S_L$ [cm/s]")
    ax1.tick_params(axis="x", labelcolor=P.C["egr"])
    ax2.tick_params(axis="x", labelcolor=P.C["oxy"])
    ax1.legend(handles=[l1, l2], loc="best")
    plt.title("Flame speed: EGR slows, O$_2$ enrichment accelerates")
    P._fig("fig4_flamespeed_vs_dilution.png")


SECTIONS = {
    "equilibrium": run_equilibrium,
    "ignition": run_ignition,
    "nox": run_nox,
    "flame_air": lambda: run_flame_case("air"),
    "flame_egr": lambda: run_flame_case("egr"),
    "flame_oxy": lambda: run_flame_case("oxy"),
    "flame_dilution": run_flame_dilution,
    "flame_plots": run_flame_plots,
}


def main():
    args = sys.argv[1:] or ["all"]
    if args == ["all"]:
        order = ["equilibrium", "ignition", "nox", "flame_air", "flame_egr",
                 "flame_oxy", "flame_dilution", "flame_plots"]
    else:
        order = args
    for s in order:
        print("== section:", s)
        SECTIONS[s]()


if __name__ == "__main__":
    main()
