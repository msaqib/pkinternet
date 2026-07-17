#!/usr/bin/env python3
"""
visualization.py — Reproducible figure generation for the longitudinal panel experiment.

Reads from a results/panel_<ts>.csv file and produces all paper figures.

Usage:
    python3 analysis/visualization.py --results experiments/07_longitudinal_panel/results/

Outputs all figures to results/figures/ as PDF files.
"""

import argparse
import os
import glob
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
from collections import defaultdict

# ── CONFIG ────────────────────────────────────────────────────────────────────

# Consistent color per ISP across all figures
ISP_COLORS = {
    'ptcl':       '#e41a1c',
    'transworld': '#377eb8',
    'cybernet':   '#4daf4a',
    'nayatel':    '#984ea3',
    'nova':       '#ff7f00',
    'zcom':       '#a65628',
    'fasttel':    '#f781bf',
    'orbit':      '#999999',
}

def isp_color(probe_label):
    """Return consistent color for a probe based on its ISP prefix."""
    for isp, color in ISP_COLORS.items():
        if isp in probe_label.lower():
            return color
    return '#333333'

def save(fig, path):
    fig.savefig(path, bbox_inches='tight', dpi=150)
    plt.close(fig)
    print(f"  saved → {path}")

# ── DATA LOADING ──────────────────────────────────────────────────────────────

def load_panel(results_dir):
    """Load the most recent panel CSV from results dir."""
    pattern = os.path.join(results_dir, 'panel_*.csv')
    files = sorted(glob.glob(pattern))
    if not files:
        raise FileNotFoundError(f"No panel_*.csv found in {results_dir}")
    path = files[-1]
    print(f"Loading {path}")
    df = pd.read_csv(path, parse_dates=['ts_utc'])
    print(f"  {len(df)} rows, {df['probe'].nunique()} probes, {df['target'].nunique()} targets")
    return df

# ── FIGURE 1: RTT heatmap — median RTT per probe × site ──────────────────────

def fig_rtt_heatmap(df, out_dir):
    print("Figure 1: RTT heatmap")
    pivot = (
        df.groupby(['probe', 'target'])['rtt_min']
        .median()
        .unstack('target')
    )
    # order probes by overall median RTT
    probe_order = pivot.median(axis=1).sort_values().index
    site_order  = pivot.median(axis=0).sort_values().index
    pivot = pivot.loc[probe_order, site_order]

    # shorten site names
    pivot.columns = [c.replace('.com.pk','').replace('.gov.pk','')
                      .replace('.pk','').replace('.com','') for c in pivot.columns]

    fig, ax = plt.subplots(figsize=(14, 5))
    sns.heatmap(
        pivot, ax=ax, cmap='YlOrRd',
        annot=True, fmt='.0f', linewidths=0.5, linecolor='white',
        cbar_kws={'label': 'Median RTT (ms)', 'shrink': 0.8},
        annot_kws={'size': 8},
    )
    ax.set_title('Median Ping RTT (ms) — All Probes × All Sites', fontsize=12)
    ax.set_xlabel('Destination Site')
    ax.set_ylabel('Probe')
    ax.tick_params(axis='x', rotation=35, labelsize=8)
    ax.tick_params(axis='y', rotation=0, labelsize=8)
    save(fig, os.path.join(out_dir, 'fig_rtt_heatmap.pdf'))

# ── FIGURE 2: Per-ISP KPI CDFs — RTT by hosting class ────────────────────────

def fig_kpi_cdfs(df, out_dir):
    print("Figure 2: Per-ISP KPI CDFs")
    probes = sorted(df['probe'].unique())
    classes = ['PK', 'CDN', 'Abroad']
    class_colors = {'PK': '#4daf4a', 'CDN': '#377eb8', 'Abroad': '#e41a1c'}

    n = len(probes)
    fig, axes = plt.subplots(1, n, figsize=(4 * n, 4), sharey=True)
    if n == 1:
        axes = [axes]

    for ax, probe in zip(axes, probes):
        for cls in classes:
            subset = df[(df['probe'] == probe) & (df['class'] == cls)]['rtt_min'].dropna()
            if len(subset) == 0:
                continue
            sorted_vals = np.sort(subset)
            cdf = np.arange(1, len(sorted_vals) + 1) / len(sorted_vals)
            ax.plot(sorted_vals, cdf, label=cls, color=class_colors[cls], linewidth=1.5)
        ax.set_title(probe, fontsize=9)
        ax.set_xlabel('RTT min (ms)', fontsize=8)
        ax.set_xlim(0, 400)
        ax.grid(True, alpha=0.3)
        ax.legend(fontsize=7)

    axes[0].set_ylabel('CDF')
    fig.suptitle('RTT Distribution by Hosting Class — Per ISP', fontsize=11)
    plt.tight_layout()
    save(fig, os.path.join(out_dir, 'fig_kpi_cdfs.pdf'))

# ── FIGURE 3: Trombone fraction per probe-site pair ──────────────────────────

def fig_trombone_heatmap(df, out_dir):
    print("Figure 3: Trombone fraction heatmap")
    trombone_frac = (
        df.groupby(['probe', 'target'])['tromboned']
        .mean()
        .unstack('target')
    )
    probe_order = trombone_frac.mean(axis=1).sort_values(ascending=False).index
    site_order  = trombone_frac.mean(axis=0).sort_values(ascending=False).index
    trombone_frac = trombone_frac.loc[probe_order, site_order]

    trombone_frac.columns = [c.replace('.com.pk','').replace('.gov.pk','')
                               .replace('.pk','').replace('.com','')
                               for c in trombone_frac.columns]

    fig, ax = plt.subplots(figsize=(14, 5))
    sns.heatmap(
        trombone_frac * 100, ax=ax, cmap='Reds',
        annot=True, fmt='.0f', linewidths=0.5, linecolor='white',
        cbar_kws={'label': 'Trombone rate (%)', 'shrink': 0.8},
        annot_kws={'size': 8},
        vmin=0, vmax=100,
    )
    ax.set_title('Tromboning Rate (%) — Fraction of Rounds Hairpinning Abroad', fontsize=12)
    ax.set_xlabel('Destination Site')
    ax.set_ylabel('Probe')
    ax.tick_params(axis='x', rotation=35, labelsize=8)
    ax.tick_params(axis='y', rotation=0, labelsize=8)
    save(fig, os.path.join(out_dir, 'fig_trombone_heatmap.pdf'))

# ── FIGURE 4: Trombone flipping — RQ3 ────────────────────────────────────────

def fig_trombone_flipping(df, out_dir):
    print("Figure 4: Trombone flipping (RQ3)")
    # find PK-hosted sites only
    pk_sites = df[df['class'] == 'PK']['target'].unique()
    df_pk = df[df['target'].isin(pk_sites)]

    # for each probe-site pair compute fraction of rounds tromboned
    frac = (
        df_pk.groupby(['probe', 'target'])['tromboned']
        .agg(['mean', 'count'])
        .reset_index()
    )
    frac.columns = ['probe', 'target', 'trombone_frac', 'n_rounds']

    # flipping = pairs where 0 < trombone_frac < 1 (sometimes local, sometimes not)
    flipping = frac[(frac['trombone_frac'] > 0.05) & (frac['trombone_frac'] < 0.95)]
    always_trombone = frac[frac['trombone_frac'] >= 0.95]
    always_local    = frac[frac['trombone_frac'] <= 0.05]

    print(f"  Always local:    {len(always_local)}")
    print(f"  Always trombone: {len(always_trombone)}")
    print(f"  Flipping:        {len(flipping)}")

    # plot trombone fraction distribution for PK-hosted sites
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.hist(frac['trombone_frac'] * 100, bins=20, color='steelblue', edgecolor='white')
    ax.axvline(5,  color='green', linestyle='--', linewidth=1, label='Always local (<5%)')
    ax.axvline(95, color='red',   linestyle='--', linewidth=1, label='Always trombone (>95%)')
    ax.set_xlabel('Trombone fraction (% of rounds)')
    ax.set_ylabel('Number of probe-site pairs')
    ax.set_title('PK-hosted Sites: How Often Does Traffic Trombone?')
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)

    # annotate
    ax.text(0.02, 0.95, f"Always local: {len(always_local)}", transform=ax.transAxes,
            color='green', fontsize=9, va='top')
    ax.text(0.98, 0.95, f"Always trombone: {len(always_trombone)}", transform=ax.transAxes,
            color='red', fontsize=9, va='top', ha='right')
    ax.text(0.5, 0.95, f"Flipping: {len(flipping)}", transform=ax.transAxes,
            color='steelblue', fontsize=9, va='top', ha='center')

    save(fig, os.path.join(out_dir, 'fig_trombone_flipping.pdf'))

    # also save a table of the most notable flippers
    if len(flipping) > 0:
        flipping_sorted = flipping.sort_values('trombone_frac', ascending=False)
        flipping_sorted.to_csv(os.path.join(out_dir, 'trombone_flippers.csv'), index=False)
        print(f"  saved trombone_flippers.csv")

# ── FIGURE 5: Diurnal pattern ─────────────────────────────────────────────────

def fig_diurnal(df, out_dir):
    print("Figure 5: Diurnal RTT pattern")
    df = df.copy()
    df['hour'] = df['ts_utc'].dt.hour

    # median RTT per hour per hosting class
    diurnal = (
        df.groupby(['hour', 'class'])['rtt_min']
        .median()
        .reset_index()
    )

    class_colors = {'PK': '#4daf4a', 'CDN': '#377eb8', 'Abroad': '#e41a1c'}

    fig, ax = plt.subplots(figsize=(10, 4))
    for cls, group in diurnal.groupby('class'):
        ax.plot(group['hour'], group['rtt_min'],
                label=cls, color=class_colors.get(cls, 'gray'),
                linewidth=2, marker='o', markersize=3)

    ax.set_xlabel('Hour of day (UTC)')
    ax.set_ylabel('Median RTT (ms)')
    ax.set_title('Diurnal RTT Pattern by Hosting Class')
    ax.set_xticks(range(0, 24, 2))
    ax.legend()
    ax.grid(True, alpha=0.3)
    save(fig, os.path.join(out_dir, 'fig_diurnal.pdf'))

# ── FIGURE 6: Anomaly detection — top N most variable probe-site pairs ────────

def fig_anomalies(df, out_dir, top_n=4):
    print(f"Figure 6: Top {top_n} anomalous probe-site pairs")
    variance = (
        df.groupby(['probe', 'target'])['rtt_min']
        .std()
        .reset_index()
        .sort_values('rtt_min', ascending=False)
    )
    # exclude sites that block ICMP (100% loss)
    loss_check = df.groupby(['probe', 'target'])['loss'].mean()
    high_loss = loss_check[loss_check > 0.9].index
    variance = variance[~variance.set_index(['probe', 'target']).index.isin(high_loss)]

    top_pairs = variance.head(top_n)

    fig, axes = plt.subplots(top_n, 1, figsize=(12, 4 * top_n))
    if top_n == 1:
        axes = [axes]

    for ax, (_, row) in zip(axes, top_pairs.iterrows()):
        probe  = row['probe']
        target = row['target']
        subset = df[(df['probe'] == probe) & (df['target'] == target)].copy()
        subset = subset.sort_values('ts_utc')

        color = isp_color(probe)
        ax.plot(subset['ts_utc'], subset['rtt_min'],
                linewidth=1.0, color=color, alpha=0.8)
        ax.set_title(f"{probe} → {target}  (std={row['rtt_min']:.0f} ms)", fontsize=10)
        ax.set_ylabel('RTT min (ms)')
        ax.grid(True, alpha=0.3)
        ax.xaxis.set_major_formatter(mdates.ConciseDateFormatter(
            mdates.AutoDateLocator()))

    axes[-1].set_xlabel('Time (UTC)')
    fig.suptitle(f'Top {top_n} Most Variable Probe-Site Pairs', fontsize=12)
    plt.tight_layout()
    save(fig, os.path.join(out_dir, 'fig_anomalies.pdf'))

# ── FIGURE 7: Route stability — distinct AS paths per probe-site ──────────────

def fig_route_stability(df, out_dir):
    print("Figure 7: Route stability")
    if 'transit' not in df.columns:
        print("  skipping — no transit column in this dataset")
        return

    stability = (
        df.groupby(['probe', 'target'])['transit']
        .nunique()
        .unstack('target')
    )
    probe_order = stability.mean(axis=1).sort_values().index
    site_order  = stability.mean(axis=0).sort_values().index
    stability = stability.loc[probe_order, site_order]

    stability.columns = [c.replace('.com.pk','').replace('.gov.pk','')
                          .replace('.pk','').replace('.com','')
                          for c in stability.columns]

    fig, ax = plt.subplots(figsize=(14, 5))
    sns.heatmap(
        stability, ax=ax, cmap='YlOrRd',
        annot=True, fmt='.0f', linewidths=0.5, linecolor='white',
        cbar_kws={'label': 'Distinct transit paths', 'shrink': 0.8},
        annot_kws={'size': 8},
    )
    ax.set_title('Route Stability — Distinct Transit Paths per Probe-Site Pair', fontsize=12)
    ax.set_xlabel('Destination Site')
    ax.set_ylabel('Probe')
    ax.tick_params(axis='x', rotation=35, labelsize=8)
    ax.tick_params(axis='y', rotation=0, labelsize=8)
    save(fig, os.path.join(out_dir, 'fig_route_stability.pdf'))

# ── STATISTICS TABLE ──────────────────────────────────────────────────────────

def stats_table(df, out_dir):
    print("Statistics table")
    table = (
        df.groupby(['probe', 'class'])
        .agg(
            median_rtt  = ('rtt_min',   'median'),
            mean_rtt    = ('rtt_min',   'mean'),
            loss_pct    = ('loss',      'mean'),
            median_hops = ('hop_count', 'median'),
            n_rounds    = ('rtt_min',   'count'),
        )
        .round(1)
        .reset_index()
    )
    table.to_csv(os.path.join(out_dir, 'stats_table.csv'), index=False)
    print(f"  saved stats_table.csv")
    print(table.to_string(index=False))

# ── MAIN ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description='Generate paper figures from longitudinal panel data')
    parser.add_argument('--results', required=True, help='Path to results directory')
    args = parser.parse_args()

    results_dir = args.results
    out_dir = os.path.join(results_dir, 'figures')
    os.makedirs(out_dir, exist_ok=True)
    print(f"Output directory: {out_dir}\n")

    df = load_panel(results_dir)

    # run all figures
    fig_rtt_heatmap(df, out_dir)
    fig_kpi_cdfs(df, out_dir)
    fig_trombone_heatmap(df, out_dir)
    fig_trombone_flipping(df, out_dir)
    fig_diurnal(df, out_dir)
    fig_anomalies(df, out_dir)
    fig_route_stability(df, out_dir)
    stats_table(df, out_dir)

    print(f"\nDone. All figures saved to {out_dir}")

if __name__ == '__main__':
    main()