"""Construction of reactant mixtures for the three combustion regimes studied.

Three families of fresh charge are built here, all on a methane basis:

* ``air_mixture``  -- conventional CH4 / air at a given equivalence ratio.
* ``oxy_mixture``  -- oxy-fuel: the N2 of air is replaced by CO2, the oxidiser
  being an O2/CO2 blend with a prescribed O2 mole fraction.
* ``egr_mixture``  -- exhaust-gas recirculation: a fraction of cooled burned
  products is mixed back into the fresh CH4/air charge.

Every function returns a composition dictionary (mole fractions, unnormalised)
that can be handed straight to ``gas.TPX``.
"""
from . import config as cfg


def _normalise(x):
    total = sum(x.values())
    return {k: v / total for k, v in x.items() if v > 0.0}


def air_mixture(phi):
    """Stoichiometric reference: CH4 + 2 O2 (+ 3.76*2 N2).

    Scaling the fuel by ``phi`` reproduces the usual definition of the
    equivalence ratio (phi > 1 -> fuel rich).
    """
    o2 = 2.0
    return _normalise({
        cfg.FUEL: phi,
        "O2": o2,
        "N2": o2 * cfg.N2_PER_O2,
    })


def oxy_mixture(phi, x_o2=0.21):
    """Oxy-fuel charge: oxidiser is O2 + CO2 with O2 mole fraction ``x_o2``.

    ``x_o2 = 0.21`` mimics the oxygen content of air but with CO2 instead of
    N2 as the bath gas (the classic carbon-capture-ready configuration).
    """
    o2 = 2.0
    co2 = o2 * (1.0 - x_o2) / x_o2
    return _normalise({
        cfg.FUEL: phi,
        "O2": o2,
        "CO2": co2,
    })


def _burned_composition(gas, phi, threshold=1.0e-4):
    """Mole fractions of the equilibrium products of a stoichiometric-basis
    CH4/air flame -- used as the recirculated exhaust gas.

    Trace radicals below ``threshold`` are dropped: real recirculated exhaust is
    cooled before re-induction, so those radicals recombine and only the bulk
    species (CO2, H2O, N2, O2, CO) survive. Pruning them also keeps the flame
    calculation fast and well-conditioned.
    """
    stable = {"N2", "O2", "CO2", "H2O", "CO", "H2", "CH4", "AR"}
    gas.TPX = cfg.T_UNBURNED, cfg.P_REF, air_mixture(phi)
    gas.equilibrate("HP")
    comp = {sp: x for sp, x in zip(gas.species_names, gas.X)
            if x > threshold and sp in stable}
    return comp


def egr_mixture(gas, phi, egr_fraction):
    """Mix a mole fraction ``egr_fraction`` of cooled burned gas back into a
    fresh CH4/air charge.

    The exhaust composition is taken from the equilibrium products at the same
    equivalence ratio; it is re-inhaled at the unburned temperature (i.e. the
    EGR is assumed cooled), so it acts as a chemically-realistic diluent rich
    in CO2 and H2O.
    """
    fresh = air_mixture(phi)
    exhaust = _burned_composition(gas, phi)
    f = egr_fraction
    mix = {}
    for sp in set(fresh) | set(exhaust):
        mix[sp] = (1.0 - f) * fresh.get(sp, 0.0) + f * exhaust.get(sp, 0.0)
    return _normalise(mix)


def diluted_air(phi, diluent, fraction):
    """Stoichiometric-basis CH4/air charge with an extra ``fraction`` mole
    fraction of a single pure diluent (``N2``, ``CO2`` or ``H2O``).

    Used to isolate the *chemical* effect of each diluent species on the
    adiabatic flame temperature, independent of any EGR bookkeeping.
    """
    base = air_mixture(phi)
    # add diluent so that it makes up `fraction` of the final mixture
    scale = (1.0 - fraction)
    mix = {k: v * scale for k, v in base.items()}
    mix[diluent] = mix.get(diluent, 0.0) + fraction
    return _normalise(mix)
