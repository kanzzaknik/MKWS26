"""One-dimensional freely-propagating laminar flame -> laminar burning velocity.

Each operating point is solved as an independent ``ct.FreeFlame`` on a
mixture-averaged transport model with an automatically refined grid. A
deliberately coarse refinement target keeps the parameter sweeps fast while
still resolving the burning velocity to within a couple of percent, which is
ample for the comparative trends studied here.
"""
import numpy as np
import cantera as ct
from . import config as cfg
from . import mixtures as mx

_WIDTH = 0.025         # m, initial domain width (auto-refined)
_REFINE = dict(ratio=6.0, slope=0.30, curve=0.60)


def _solve_one(gas, comp, T, P):
    gas.TPX = T, P, comp
    flame = ct.FreeFlame(gas, width=_WIDTH)
    flame.set_refine_criteria(**_REFINE)
    flame.transport_model = "mixture-averaged"
    flame.solve(loglevel=0, auto=True)
    return flame.velocity[0]


def flame_speed_sweep(compositions, T=None, P=None):
    """Return S_L [m/s] for a list of compositions (NaN on non-convergence)."""
    gas = ct.Solution(cfg.MECHANISM)
    T = T or cfg.T_UNBURNED
    P = P or cfg.P_REF
    speeds = []
    for comp in compositions:
        try:
            speeds.append(_solve_one(gas, comp, T, P))
        except Exception:
            speeds.append(np.nan)
    return np.asarray(speeds)


def sweep_phi(case="air", n=3):
    phis = np.linspace(*cfg.PHI_RANGE, n)
    gas = ct.Solution(cfg.MECHANISM)
    comp_fn = {
        "air": lambda phi: mx.air_mixture(phi),
        "egr": lambda phi: mx.egr_mixture(gas, phi, 0.10),
        "oxy": lambda phi: mx.oxy_mixture(phi, 0.30),
    }[case]
    comps = [comp_fn(phi) for phi in phis]
    return {"phi": phis, "SL": flame_speed_sweep(comps)}


def sweep_egr_speed(n=4):
    gas = ct.Solution(cfg.MECHANISM)
    fracs = np.linspace(0.0, 0.20, n)
    comps = [mx.egr_mixture(gas, 1.0, f) for f in fracs]
    return {"egr_fraction": fracs, "SL": flame_speed_sweep(comps)}


def sweep_oxy_speed(n=4):
    xs = np.linspace(0.21, 0.40, n)
    comps = [mx.oxy_mixture(1.0, x) for x in xs]
    return {"x_o2": xs, "SL": flame_speed_sweep(comps)}
