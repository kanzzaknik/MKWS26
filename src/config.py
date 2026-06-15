"""Global configuration for the EGR / oxy-fuel methane combustion study.

All physical and numerical parameters used across the project live here so that
every analysis module shares one consistent set of assumptions.
"""

# --- Chemistry -------------------------------------------------------------
MECHANISM = "gri30.yaml"   # 53 species, 325 reactions, ships with Cantera
FUEL = "CH4"               # methane

# Air composition (molar). O2 : N2 = 1 : 3.76 is the standard dry-air ratio.
N2_PER_O2 = 3.76

# --- Reference thermodynamic state ----------------------------------------
T_UNBURNED = 300.0         # K, fresh-charge / intake temperature
P_REF = 101325.0           # Pa, atmospheric pressure (1 atm)

# --- Sweep ranges ----------------------------------------------------------
PHI_RANGE = (0.6, 1.4)     # equivalence ratio window for flame studies
PHI_POINTS = 9

DILUENT_FRACTION_MAX = 0.30    # max added-diluent mole fraction (Tad study)
EGR_FRACTION_MAX = 0.25        # max recirculated-gas mole fraction
OXY_O2_RANGE = (0.21, 0.45)    # O2 mole fraction inside an O2/CO2 oxidiser

# Ignition-delay temperature sweep (constant-pressure reactor)
IGNITION_T_RANGE = (1000.0, 1800.0)   # K
IGNITION_POINTS = 12
IGNITION_P = 5 * P_REF               # 5 atm, representative of an engine

# --- Output ----------------------------------------------------------------
DPI = 300
