"""Zero-dimensional chemical kinetics: auto-ignition delay time.

A constant-pressure adiabatic reactor is integrated in time; the ignition
delay is defined as the instant of maximum temperature rise (max dT/dt), the
standard thermal-runaway definition.
"""
import numpy as np
import cantera as ct
from . import config as cfg
from . import mixtures as mx


def ignition_delay(gas, composition, T0, P=None, t_end=2.0, rise=400.0):
    """Auto-ignition delay [s] for a constant-pressure reactor at T0, P.

    Ignition is defined as the first instant the temperature has risen by
    ``rise`` K above the initial value -- a robust, monotonic criterion that
    avoids spurious early-time gradient spikes from the variable-step solver.
    """
    gas.TPX = T0, (P or cfg.IGNITION_P), composition
    reactor = ct.IdealGasConstPressureReactor(gas)
    net = ct.ReactorNet([reactor])
    net.rtol, net.atol = 1.0e-9, 1.0e-15

    t = 0.0
    while t < t_end:
        t = net.step()
        if reactor.T >= T0 + rise:
            return t
    return np.nan


def sweep_temperature(case="air", n=None):
    """Ignition delay vs initial temperature (Arrhenius sweep)."""
    n = n or cfg.IGNITION_POINTS
    gas = ct.Solution(cfg.MECHANISM)
    temps = np.linspace(*cfg.IGNITION_T_RANGE, n)
    comp_fn = {
        "air": lambda T: mx.air_mixture(1.0),
        "oxy": lambda T: mx.oxy_mixture(1.0, 0.21),
        "egr": lambda T: mx.egr_mixture(gas, 1.0, 0.20),
    }[case]
    tau = [ignition_delay(gas, comp_fn(T), T) for T in temps]
    return {"T": temps, "tau": tau}


def sweep_egr_ignition(T0=1100.0, n=12):
    """Ignition delay vs EGR fraction at a fixed initial temperature."""
    gas = ct.Solution(cfg.MECHANISM)
    fracs = np.linspace(0.0, cfg.EGR_FRACTION_MAX, n)
    tau = [ignition_delay(gas, mx.egr_mixture(gas, 1.0, f), T0) for f in fracs]
    return {"egr_fraction": fracs, "tau": tau}
