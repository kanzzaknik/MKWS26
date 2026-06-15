"""Incremental, resumable, crash-proof flame-speed generator.

Every operating point is solved in its own short-lived subprocess with a hard
timeout, so a single stubborn flame can never hang the whole sweep. Results are
written to CSV after each point and already-computed points are skipped, so the
generator is fully resumable: run it again until it prints COMPLETE.
"""
import os, sys, csv, time, subprocess
import numpy as np

DATA = "results/data"
POINT_TIMEOUT = 30      # s, hard wall-clock limit per flame
DRIVER_BUDGET = 37      # s, total per invocation

JOBS = {
    "flame_phi_air":   ("phi",          [0.6, 0.8, 1.0, 1.2, 1.4]),
    "flame_phi_oxy":   ("phi",          [0.6, 0.8, 1.0, 1.2, 1.4]),
    "flame_phi_egr":   ("phi",          [0.6, 0.8, 1.0, 1.2, 1.4]),
    "flame_egr_speed": ("egr_fraction", [0.0, 0.07, 0.14, 0.20]),
    "flame_oxy_speed": ("x_o2",         [0.21, 0.27, 0.33, 0.40]),
}


def _compose(case, x):
    import cantera as ct
    from src import mixtures as mx
    g = ct.Solution("gri30.yaml")
    if case == "flame_phi_air":
        return mx.air_mixture(x)
    if case == "flame_phi_oxy":
        return mx.oxy_mixture(x, 0.30)
    if case == "flame_phi_egr":
        return mx.egr_mixture(g, x, 0.10)
    if case == "flame_egr_speed":
        return mx.egr_mixture(g, 1.0, x)
    if case == "flame_oxy_speed":
        return mx.oxy_mixture(1.0, x)


def worker(case, x):
    import cantera as ct
    from src import config as cfg, flame as fl
    g = ct.Solution(cfg.MECHANISM)
    sl = fl._solve_one(g, _compose(case, x), cfg.T_UNBURNED, cfg.P_REF)
    print("SL=%.8f" % sl)


def load(name, xkey):
    path = os.path.join(DATA, name + ".csv")
    done = {}
    if os.path.exists(path):
        with open(path) as fh:
            for row in csv.DictReader(fh):
                try:
                    done[round(float(row[xkey]), 6)] = float(row["SL"])
                except ValueError:
                    pass
    return done


def save(name, xkey, xs, done):
    with open(os.path.join(DATA, name + ".csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow([xkey, "SL"])
        for x in xs:
            w.writerow([x, done.get(round(float(x), 6), "nan")])


def driver(name):
    xkey, xs = JOBS[name]
    done = load(name, xkey)
    t0 = time.time()
    for x in xs:
        key = round(float(x), 6)
        if key in done and not np.isnan(done[key]):
            continue
        if time.time() - t0 > DRIVER_BUDGET:
            break
        try:
            r = subprocess.run([sys.executable, __file__, "worker", name, repr(x)],
                               capture_output=True, text=True, timeout=POINT_TIMEOUT)
            sl = float("nan")
            for line in r.stdout.splitlines():
                if line.startswith("SL="):
                    sl = float(line[3:])
        except subprocess.TimeoutExpired:
            sl = float("nan")
        done[key] = sl
        save(name, xkey, xs, done)
        print("  %s=%.4f -> SL=%s" % (xkey, x, sl))
    remaining = [x for x in xs if round(float(x), 6) not in done or np.isnan(done[round(float(x), 6)])]
    print("%s: %d/%d done" % (name, len(xs) - len(remaining), len(xs)))
    return len(remaining) == 0


if __name__ == "__main__":
    if sys.argv[1] == "worker":
        worker(sys.argv[2], float(eval(sys.argv[3])))
    else:
        ok = driver(sys.argv[1])
        print("COMPLETE" if ok else "PARTIAL")
