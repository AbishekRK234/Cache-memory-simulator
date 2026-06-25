"""
Performance Analysis & Visualization
=====================================
Functions to plot and display cache performance results.
Generates bar charts, access-pattern timelines, and comparison plots.
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

# Consistent color palette
COLORS = ["#2196F3", "#4CAF50", "#FF5722", "#9C27B0", "#FF9800", "#00BCD4", "#E91E63"]


def _save(fig: plt.Figure, filename: str):
    fig.savefig(filename, dpi=150, bbox_inches="tight")
    print(f"  [Saved] {filename}")


# ---------------------------------------------------------------------------
# 1. Cache-type comparison (Direct vs Set-Assoc vs Fully Assoc)
# ---------------------------------------------------------------------------

def plot_cache_comparison(results: list[dict], title: str = "Cache Type Comparison"):
    """
    Bar chart comparing hit rate, miss rate, and AMAT across cache configurations.

    Each entry in `results` must have:
        name, hit_rate, miss_rate, amat
    """
    names     = [r["name"]      for r in results]
    hit_rates = [r["hit_rate"]  * 100 for r in results]
    miss_rates= [r["miss_rate"] * 100 for r in results]
    amats     = [r["amat"]      for r in results]
    colors    = COLORS[:len(names)]

    fig, axes = plt.subplots(1, 3, figsize=(16, 6))
    fig.suptitle(title, fontsize=15, fontweight="bold", y=1.02)

    def _bar(ax, values, ylabel, title_, fmt=".1f", suffix=""):
        bars = ax.bar(names, values, color=colors, edgecolor="black", linewidth=0.6, zorder=3)
        ax.set_title(title_, fontweight="bold", pad=8)
        ax.set_ylabel(ylabel)
        ax.tick_params(axis="x", rotation=20)
        ax.grid(axis="y", alpha=0.3, zorder=0)
        for bar, val in zip(bars, values):
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + max(values) * 0.02,
                f"{val:{fmt}}{suffix}",
                ha="center", va="bottom", fontsize=9, fontweight="bold",
            )

    _bar(axes[0], hit_rates,  "Percentage (%)", "Hit Rate",  suffix="%")
    axes[0].set_ylim(0, 110)

    _bar(axes[1], miss_rates, "Percentage (%)", "Miss Rate", suffix="%")
    axes[1].set_ylim(0, 110)

    _bar(axes[2], amats,      "Cycles",         "AMAT (cycles)")

    plt.tight_layout()
    _save(fig, "cache_comparison.png")
    plt.show()


# ---------------------------------------------------------------------------
# 2. Access-pattern timeline + cumulative hit rate
# ---------------------------------------------------------------------------

def plot_access_pattern(access_log: list[dict], title: str = "Cache Access Pattern"):
    """
    Two-panel plot:
      Top   : Green/red bar per access (HIT / MISS)
      Bottom: Cumulative hit rate over time
    """
    if not access_log:
        print("  No access log to plot.")
        return

    results = [1 if e["result"] == "HIT" else 0 for e in access_log]
    n = len(results)

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 7))
    fig.suptitle(title, fontsize=13, fontweight="bold")

    # --- Hit/Miss timeline ---
    bar_colors = ["#4CAF50" if r else "#F44336" for r in results]
    ax1.bar(range(n), results, color=bar_colors, width=1.0, zorder=3)
    ax1.set_title("Access Pattern  (Green = HIT, Red = MISS)", pad=6)
    ax1.set_xlabel("Access Number")
    ax1.set_ylabel("HIT(1) / MISS(0)")
    ax1.set_ylim(-0.15, 1.35)
    ax1.grid(axis="y", alpha=0.3, zorder=0)
    hit_patch  = mpatches.Patch(color="#4CAF50", label="HIT")
    miss_patch = mpatches.Patch(color="#F44336", label="MISS")
    ax1.legend(handles=[hit_patch, miss_patch], loc="upper right")

    # --- Cumulative hit rate ---
    cum_hits = np.cumsum(results)
    cum_rate = cum_hits / (np.arange(n) + 1) * 100

    ax2.plot(cum_rate, color="#2196F3", linewidth=1.8, zorder=3)
    ax2.fill_between(range(n), cum_rate, alpha=0.15, color="#2196F3")
    ax2.axhline(y=cum_rate[-1], color="#E91E63", linestyle="--", linewidth=1.2,
                label=f"Final hit rate: {cum_rate[-1]:.1f}%")
    ax2.set_title("Cumulative Hit Rate Over Time", pad=6)
    ax2.set_xlabel("Access Number")
    ax2.set_ylabel("Hit Rate (%)")
    ax2.set_ylim(0, 105)
    ax2.grid(alpha=0.3, zorder=0)
    ax2.legend(loc="lower right")

    plt.tight_layout()
    _save(fig, "access_pattern.png")
    plt.show()


# ---------------------------------------------------------------------------
# 3. Replacement policy comparison
# ---------------------------------------------------------------------------

def plot_policy_comparison(
    results_by_policy: dict[str, dict],
    title: str = "Replacement Policy Comparison",
):
    """
    Compare LRU, FIFO, Random across hit rate and AMAT.

    results_by_policy = {
        "LRU":    {"hit_rate": 0.85, "miss_rate": 0.15, "amat": 16.0},
        "FIFO":   {...},
        "Random": {...},
    }
    """
    policies  = list(results_by_policy.keys())
    hit_rates = [results_by_policy[p]["hit_rate"] * 100 for p in policies]
    amats     = [results_by_policy[p]["amat"] for p in policies]
    colors    = COLORS[:len(policies)]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 6))
    fig.suptitle(title, fontsize=14, fontweight="bold")

    def _bar(ax, values, ylabel, subtitle, suffix=""):
        bars = ax.bar(policies, values, color=colors, edgecolor="black", linewidth=0.6, zorder=3)
        ax.set_title(subtitle, fontweight="bold", pad=8)
        ax.set_ylabel(ylabel)
        ax.grid(axis="y", alpha=0.3, zorder=0)
        for bar, val in zip(bars, values):
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + max(values) * 0.02,
                f"{val:.1f}{suffix}",
                ha="center", va="bottom", fontsize=11, fontweight="bold",
            )

    _bar(ax1, hit_rates, "Hit Rate (%)", "Hit Rate by Policy", suffix="%")
    ax1.set_ylim(0, 110)

    _bar(ax2, amats, "Cycles", "AMAT by Policy")

    plt.tight_layout()
    _save(fig, "policy_comparison.png")
    plt.show()


# ---------------------------------------------------------------------------
# 4. Workload sensitivity analysis
# ---------------------------------------------------------------------------

def plot_workload_sensitivity(
    workload_results: dict[str, list[dict]],
    title: str = "Hit Rate vs Workload Type",
):
    """
    Grouped bar chart: for each workload type show hit rates of all cache types.

    workload_results = {
        "sequential": [{"name": "Direct Mapped", "hit_rate": 0.9}, ...],
        "random":     [...],
        ...
    }
    """
    workloads = list(workload_results.keys())
    cache_names = [r["name"] for r in next(iter(workload_results.values()))]
    n_caches = len(cache_names)
    n_workloads = len(workloads)

    x = np.arange(n_workloads)
    width = 0.7 / n_caches

    fig, ax = plt.subplots(figsize=(14, 7))
    fig.suptitle(title, fontsize=14, fontweight="bold")

    for i, cache_name in enumerate(cache_names):
        rates = [workload_results[wl][i]["hit_rate"] * 100 for wl in workloads]
        offset = (i - n_caches / 2 + 0.5) * width
        bars = ax.bar(x + offset, rates, width, label=cache_name,
                      color=COLORS[i % len(COLORS)], edgecolor="black", linewidth=0.5, zorder=3)

    ax.set_xticks(x)
    ax.set_xticklabels([w.replace("_", "\n") for w in workloads], fontsize=10)
    ax.set_ylabel("Hit Rate (%)")
    ax.set_ylim(0, 110)
    ax.set_xlabel("Workload Type")
    ax.legend(loc="upper right", fontsize=9)
    ax.grid(axis="y", alpha=0.3, zorder=0)

    plt.tight_layout()
    _save(fig, "workload_sensitivity.png")
    plt.show()


# ---------------------------------------------------------------------------
# Console print helpers
# ---------------------------------------------------------------------------

def print_stats_table(results: list[dict]):
    """Print a formatted table of performance results."""
    col_w = [28, 10, 10, 10, 10, 10]
    header = ["Cache Configuration", "Accesses", "Hits", "Misses", "Hit Rate", "AMAT"]
    sep = "+" + "+".join("-" * w for w in col_w) + "+"

    print()
    print(sep)
    print("|" + "|".join(f" {h:<{col_w[i]-1}}" for i, h in enumerate(header)) + "|")
    print(sep)
    for r in results:
        row = [
            r["name"],
            str(r.get("accesses", "-")),
            str(r.get("hits", "-")),
            str(r.get("misses", "-")),
            f"{r['hit_rate']*100:.1f}%",
            f"{r['amat']:.2f}",
        ]
        print("|" + "|".join(f" {v:<{col_w[i]-1}}" for i, v in enumerate(row)) + "|")
    print(sep)
    print()


def print_access_log(access_log: list[dict], max_rows: int = 20):
    """Print a formatted access log table."""
    col_w = [12, 10, 10, 10, 8]
    header = ["Address", "Tag", "Index", "Offset", "Result"]
    sep = "+" + "+".join("-" * w for w in col_w) + "+"
    print(sep)
    print("|" + "|".join(f" {h:<{col_w[i]-1}}" for i, h in enumerate(header)) + "|")
    print(sep)
    for entry in access_log[:max_rows]:
        row = [
            entry.get("address", "-"),
            str(entry.get("tag", "-")),
            str(entry.get("index", "-")),
            str(entry.get("offset", "-")),
            entry.get("result", "-"),
        ]
        print("|" + "|".join(f" {v:<{col_w[i]-1}}" for i, v in enumerate(row)) + "|")
    print(sep)
    if len(access_log) > max_rows:
        print(f"  ... ({len(access_log) - max_rows} more accesses not shown)")
    print()
