"""Equilibrium analyses: adiabatic flame temperature and equilibrium NO.

These quantities follow from constant-enthalpy, constant-pressure (HP)
equilibrium and are cheap to evaluate, so they are used for the broad
parameter sweeps (diluent type, equivalence ratio, EGR fraction, oxy O2).
"""
import cantera as ct
from . import config as cfg
from . import mixtures as mx


def _make_gas():
    return ct.Solution(cfg.MECHANISM)


def adiabatic_flame_temperature(gas, composition, T=None, P=None):
    """Constant-enthalpy, constant-pressure adiabatic flame temperature [K]."""
    gas.TPX = (T or cfg.T_UNBURNED), (P or cfg.P_REF), composition
    gas.equilibrate("HP")
    return gas.T


def equilibrium_no_ppm(gas, composition, T=None, P=None):
    """Equilibrium NO concentration in the burned gas, in ppm (mole basis).

    Equilibrium NO is an upper bound on thermal NOx but reproduces the correct
    sensitivity to flame temperature and to the presence of N2, which is what
    the EGR / oxy-fuel comparison is about.
    """
    gas.TPX = (T or cfg.T_UNBURNED), (P or cfg.P_REF), composition
    gas.equilibrate("HP")
    return gas["NO"].X[0] * 1.0e6


# --- sweep helpers ---------------------------------------------------------

def sweep_diluent_tad(diluents=("N2", "CO2", "H2O"), n=16):
    """Tad vs added-diluent mole fraction for each pure diluent (phi = 1)."""
    import numpy as np
    gas = _make_gas()
    fracs = np.linspace(0.0, cfg.DILUENT_FRACTION_MAX, n)
    out = {"fraction": fracs}
    for d in diluents:
        out[d] = [adiabatic_flame_temperature(gas, mx.diluted_air(1.0, d, f))
                  for f in fracs]
    return out


def sweep_phi_tad(n=None):
    """Tad vs equivalence ratio for air, oxy-fuel and EGR(0.20)."""
    import numpy as np
    n = n or cfg.PHI_POINTS
    gas = _make_gas()
    phis = np.linspace(*cfg.PHI_RANGE, n)
    out = {"phi": phis, "air": [], "oxy": [], "egr": []}
    for phi in phis:
        out["air"].append(adiabatic_flame_temperature(gas, mx.air_mixture(phi)))
        out["oxy"].append(adiabatic_flame_temperature(gas, mx.oxy_mixture(phi, 0.21)))
        out["egr"].append(adiabatic_flame_temperature(gas, mx.egr_mixture(gas, phi, 0.20)))
    return out


def sweep_egr(n=16):
    """Tad and equilibrium NO vs EGR fraction (phi = 1)."""
    import numpy as np
    gas = _make_gas()
    fracs = np.linspace(0.0, cfg.EGR_FRACTION_MAX, n)
    tad, no = [], []
    for f in fracs:
        comp = mx.egr_mixture(gas, 1.0, f)
        tad.append(adiabatic_flame_temperature(gas, comp))
        no.append(equilibrium_no_ppm(gas, comp))
    return {"egr_fraction": fracs, "Tad": tad, "NO_ppm": no}


def sweep_nox_phi(n=None):
    """Equilibrium NO vs equivalence ratio for air, oxy-fuel and EGR(0.20)."""
    import numpy as np
    n = n or cfg.PHI_POINTS
    gas = _make_gas()
    phis = np.linspace(*cfg.PHI_RANGE, n)
    out = {"phi": phis, "air": [], "oxy": [], "egr": []}
    for phi in phis:
        out["air"].append(equilibrium_no_ppm(gas, mx.air_mixture(phi)))
        out["oxy"].append(equilibrium_no_ppm(gas, mx.oxy_mixture(phi, 0.21)))
        out["egr"].append(equilibrium_no_ppm(gas, mx.egr_mixture(gas, phi, 0.20)))
    return out
