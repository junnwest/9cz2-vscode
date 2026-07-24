#!/usr/bin/env python3
import glob
import os
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import ScalarFormatter, MultipleLocator

def read_gamd_dat(fname):
    """
    Expect five whitespace‐delimited columns:
      Step   dV   Vavg   sigmaV   k0
    """
    df = pd.read_csv(
        fname,
        delim_whitespace=True,
        header=None,
        names=['Step','dV','Vavg','sigmaV','k0'],
        comment='#'
    )
    return df

def plot_time_series(df, source):
    # we now need 3 rows for (sigmaV, Vavg, k0)
    fig, axes = plt.subplots(3, 1, figsize=(10, 8), sharex=True)

    # Disable offset and scientific notation on x-axis for all subplots
    for ax in axes:
        fmt = ScalarFormatter(useOffset=False)
        fmt.set_scientific(False)
        ax.xaxis.set_major_formatter(fmt)
        # optional: put ticks every 10000000 steps
        ax.xaxis.set_major_locator(MultipleLocator(10000000))

    # 1) σᵥ over time
    axes[0].plot(df['Step'], df['sigmaV'], color='tab:blue', lw=1)
    axes[0].set_ylabel(r'$\sigma_V$')
    axes[0].set_title(f'{source} — GaMD metrics over time')

    # 2) Vavg over time
    axes[1].plot(df['Step'], df['Vavg'], color='tab:green', lw=1)
    axes[1].set_ylabel(r'$V_{\mathrm{avg}}$')

    # 3) k₀ over time
    axes[2].step(df['Step'], df['k0'], where='post', color='tab:orange', lw=1)
    axes[2].set_ylabel(r'$k_0$')
    axes[2].set_xlabel('Step')

    plt.tight_layout()
    out_ts = f"{os.path.splitext(source)[0]}_timeseries.png"
    fig.savefig(out_ts, dpi=300)
    plt.close(fig)
    print(f"Saved time series plot: {out_ts}")

def plot_dv_histogram(df, source, bins=40):
    fig, ax = plt.subplots(figsize=(6, 4))

    # Plot probability density histogram of dV
    ax.hist(
        df['dV'],
        bins=bins,
        density=True,          # area = 1
        color='tab:green',
        edgecolor='black',
        alpha=0.7
    )
    ax.set_xlabel('ΔV (boost potential)')
    ax.set_ylabel(r'$p(\Delta V)$')
    ax.set_title(f'{source} — Distribution of ΔV')

    # Disable scientific notation on x-axis
    fmt = ScalarFormatter(useOffset=False)
    fmt.set_scientific(False)
    ax.xaxis.set_major_formatter(fmt)

    plt.tight_layout()
    out_hist = f"{os.path.splitext(source)[0]}_dV_hist.png"
    fig.savefig(out_hist, dpi=300)
    plt.close(fig)
    print(f"Saved dV histogram: {out_hist}")

def main():
    files = sorted(glob.glob("gamd-equil*.dat"))
    if not files:
        print("No '*gamd-equilib.dat' files found.")
        return

    for fname in files:
        df = read_gamd_dat(fname)
        base = os.path.basename(fname)
        plot_time_series(df, base)
        plot_dv_histogram(df, base)

if __name__ == "__main__":
    main()
