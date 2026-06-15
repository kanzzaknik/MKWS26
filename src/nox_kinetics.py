"""Finite-rate NO formation kinetics in a 0-D reactor.

Unlike the equilibrium estimate in :mod:`equilibrium`, this module integrates
the full GRI-Mech 3.0 chemistry in time and tracks the *kinetic* build-up of
nitric oxide through the (extended) Zeldovich mechanism. Thermal NO is strongly
coupled to both temperature and residence time, so a finite-rate treatment is
the physically correct way to compare the air, EGR and oxy-fuel regimes.
"""
import numpy as np
import cantera as ct
from . import config as cfg
from . import mixtures as mx


_NO_SPECIES = ("NO", "NO2", "N2O", "N", "NH", "HNO")


def no_history(gas, composition, t_end=0.5, P=None, npts=120):
    """Post-flame thermal-NO build-up vs time at the adiabatic flame temperature.

    The fresh mixture is first burned (HP equilibrium) to obtain its flame
    temperature and bulk-product composition. The nitrogen-oxide species are
    then reset to zero and the chemistry is integrated at fixed temperature and
    pressure, so the curve shows NO forming *kinetically* (extended Zeldovich)
    and relaxing toward its equilibrium value -- which is reached only at long
    residence times. Returns log-spaced time [s] and NO [ppm] arrays.
    """
    P = P or cfg.P_REF
    # 1) burn the mixture to get flame temperature and products
    gas.TPX = cfg.T_UNBURNED, P, composition
    gas.equilibrate("HP")
    Tad = gas.T
    X = {sp: x for sp, x in zip(gas.species_names, gas.X) if x > 0.0}
    # 2) zero the NO pool (let it re-form kinetically)
    for sp in _NO_SPECIES:
        X.pop(sp, None)
    gas.TPX = Tad, P, X       # Cantera renormalises X
    # 3) integrate at fixed temperature (post-flame thermal NO)
    reactor = ct.IdealGasConstPressureReactor(gas, energy="off")
    net = ct.ReactorNet([reactor])
    net.rtol, net.atol = 1.0e-9, 1.0e-15
    times = np.unique(np.concatenate([[0.0], np.logspace(-6, np.log10(t_end), npts)]))
    no = np.empty_like(times)
    for i, t in enumerate(times):
        net.advance(t)
        no[i] = reactor.thermo["NO"].X[0] * 1.0e6
    return {"t": times, "NO_ppm": no, "Tad": Tad}


def compare_regimes(t_end=0.1):
    """Kinetic NO(t) for air, EGR 20% and oxy-fuel (21% O2) at phi = 1."""
    gas = ct.Solution(cfg.MECHANISM)
    out = {}
    out["air"] = no_history(gas, mx.air_mixture(1.0), t_end)
    out["egr"] = no_history(gas, mx.egr_mixture(gas, 1.0, 0.20), t_end)
    out["oxy"] = no_history(gas, mx.oxy_mixture(1.0, 0.21), t_end)
    return out
