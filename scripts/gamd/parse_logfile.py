#!/usr/bin/env python3
import re
import glob
import os

# 1) STEP lines carry both step and dV
step_re = re.compile(
    r'^ACCELERATED MD: STEP\s+(\d+)\s+dV\s+([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)'
)

# 2) TOTAL lines now capture Vavg, sigmaV and k0 (in that order)
total_re = re.compile(
    r'^GAUSSIAN ACCELERATED MD: TOTAL.*?Vavg\s+([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)'
    r'.*?sigmaV\s+([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)'
    r'.*?k0\s+(\d+)'
)

def parse_log(log_path):
    """
    Parse a single GaMD equilibration log file for
    STEP, dV, Vavg, sigmaV and k0 values.
    Returns a list of (step, dV, Vavg, sigmaV, k0).
    """
    results = []
    current_step = None
    current_dV   = None

    with open(log_path) as f:
        for line in f:
            line = line.strip()

            # a) catch the STEP / dV line
            m1 = step_re.match(line)
            if m1:
                current_step = int(m1.group(1))
                current_dV   = float(m1.group(2))
                continue

            # b) now catch the TOTAL line (only if we have a STEP pending)
            if current_step is not None:
                m2 = total_re.match(line)
                if m2:
                    vavg   = float(m2.group(1))
                    sigmaV = float(m2.group(2))
                    k0     = int(m2.group(3))
                    results.append((current_step, current_dV, vavg, sigmaV, k0))
                    # reset so we only match one TOTAL per STEP
                    current_step = None
                    current_dV   = None

    return results

def main():
    # find all .log files in cwd
    for log_file in sorted(glob.glob("*.log")):
        data = parse_log(log_file)
        if not data:
            print(f"[!] No TOTAL entries parsed in {log_file}")
            continue

        outname = os.path.splitext(log_file)[0] + ".dat"
        with open(outname, "w") as out:
            out.write("#   step      dV      Vavg   sigmaV    k0\n")
            for step, dV, vavg, sigmaV, k0 in data:
                out.write(f"{step:8d}  {dV:8.3f}  {vavg:9.3f}  {sigmaV:8.3f}  {k0:2d}\n")

        print(f"→ Parsed {log_file} → {outname}")

if __name__ == "__main__":
    main()
