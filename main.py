"""
Design and Performance Analysis of Cache Memory in a Computer System
=====================================================================
Main entry point — interactive menu-driven CLI simulator.

Usage:
    python main.py

Menu options:
    1. Full Demo         — Compare all cache types & policies, generate graphs
    2. Manual Simulation — Choose cache type, set parameters, enter addresses
    3. Policy Comparison — Compare LRU vs FIFO vs Random on same workload
    4. Workload Analysis — See how different access patterns affect performance
    5. Exit
"""

import sys
from cache_simulator import (
    DirectMappedCache,
    SetAssociativeCache,
    FullyAssociativeCache,
    generate_workload,
)
from analysis import (
    plot_cache_comparison,
    plot_access_pattern,
    plot_policy_comparison,
    plot_workload_sensitivity,
    print_stats_table,
    print_access_log,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

BANNER = """
╔══════════════════════════════════════════════════════════════════╗
║   Design and Performance Analysis of Cache Memory               ║
║   in a Computer System                                          ║
║                                                                  ║
║   COA Project  |  Cache Types: Direct / Set-Assoc / Fully-Assoc ║
║   Policies    : LRU  /  FIFO  /  Random                         ║
╚══════════════════════════════════════════════════════════════════╝
"""

MENU = """
  Main Menu
  ---------
  [1]  Full Demo            (compare all cache types, generate graphs)
  [2]  Manual Simulation    (enter your own memory addresses)
  [3]  Replacement Policy   (compare LRU vs FIFO vs Random)
  [4]  Workload Analysis    (sequential / random / loop / strided)
  [5]  Exit
"""


def prompt(msg: str, default=None):
    val = input(f"  {msg}: ").strip()
    return val if val else default


def int_prompt(msg: str, default: int) -> int:
    while True:
        val = prompt(f"{msg} [default={default}]", str(default))
        try:
            return int(val)
        except ValueError:
            print("  Please enter a valid integer.")


def _run_cache(cache, addresses: list[int]) -> dict:
    cache.reset()
    for addr in addresses:
        cache.access(addr)
    s = cache.stats
    return {
        "name":      cache.config_info().get("type", "Cache"),
        "accesses":  s.accesses,
        "hits":      s.hits,
        "misses":    s.misses,
        "hit_rate":  s.hit_rate,
        "miss_rate": s.miss_rate,
        "amat":      s.amat(),
    }


def print_config(info: dict):
    print()
    for k, v in info.items():
        print(f"    {k:<14}: {v}")
    print()


# ---------------------------------------------------------------------------
# 1. Full Demo
# ---------------------------------------------------------------------------

def run_full_demo():
    print("\n" + "=" * 60)
    print("  FULL DEMO — Cache Type Comparison")
    print("=" * 60)

    # Standard parameters
    CACHE_SIZE = 1024   # 1 KB
    BLOCK_SIZE = 16     # 16 B per block
    ADDR_BITS  = 16     # 16-bit addresses for readability

    print(f"\n  Config : cache={CACHE_SIZE}B, block={BLOCK_SIZE}B, addresses={ADDR_BITS}-bit")
    print("  Workload: Loop pattern (16-element array, repeated 20× = 320 accesses)\n")

    addresses = generate_workload("loop", num_accesses=320)

    caches = [
        DirectMappedCache(CACHE_SIZE, BLOCK_SIZE, ADDR_BITS),
        SetAssociativeCache(CACHE_SIZE, BLOCK_SIZE, ways=2,  policy="LRU", address_bits=ADDR_BITS),
        SetAssociativeCache(CACHE_SIZE, BLOCK_SIZE, ways=4,  policy="LRU", address_bits=ADDR_BITS),
        FullyAssociativeCache(CACHE_SIZE, BLOCK_SIZE, policy="LRU",        address_bits=ADDR_BITS),
    ]
    labels = [
        "Direct Mapped",
        "2-Way Set Assoc (LRU)",
        "4-Way Set Assoc (LRU)",
        "Fully Assoc (LRU)",
    ]

    results = []
    for cache, label in zip(caches, labels):
        r = _run_cache(cache, addresses)
        r["name"] = label
        results.append(r)
        print(f"  {label:<26} | Hit Rate: {r['hit_rate']*100:5.1f}%  | AMAT: {r['amat']:.2f} cycles")

    print()
    print_stats_table(results)

    print("  Generating comparison chart ...")
    plot_cache_comparison(results, title="Cache Type Comparison — Loop Workload")

    # Show access log for direct mapped
    caches[0].reset()
    for addr in addresses[:30]:
        caches[0].access(addr)
    print("  Access log (first 30 accesses — Direct Mapped):")
    print_access_log(caches[0].access_log)
    plot_access_pattern(caches[0].access_log, "Access Pattern — Direct Mapped Cache (first 30)")


# ---------------------------------------------------------------------------
# 2. Manual Simulation
# ---------------------------------------------------------------------------

def run_manual():
    print("\n" + "=" * 60)
    print("  MANUAL SIMULATION")
    print("=" * 60)

    print("""
  Cache types:
    [1] Direct Mapped
    [2] Set Associative
    [3] Fully Associative
""")
    choice = prompt("Choose cache type [1/2/3]", "1")

    cache_size  = int_prompt("Cache size (bytes, must be power of 2)", 512)
    block_size  = int_prompt("Block size  (bytes, must be power of 2)", 16)
    addr_bits   = int_prompt("Address width (bits)", 16)

    if choice == "2":
        ways   = int_prompt("Number of ways (associativity)", 2)
        policy = prompt("Replacement policy [LRU/FIFO/Random]", "LRU").upper()
        if policy not in ("LRU", "FIFO", "RANDOM"):
            policy = "LRU"
        policy = policy.capitalize() if policy == "RANDOM" else policy
        cache = SetAssociativeCache(cache_size, block_size, ways=ways,
                                    policy=policy, address_bits=addr_bits)
    elif choice == "3":
        policy = prompt("Replacement policy [LRU/FIFO/Random]", "LRU")
        cache = FullyAssociativeCache(cache_size, block_size,
                                      policy=policy, address_bits=addr_bits)
    else:
        cache = DirectMappedCache(cache_size, block_size, addr_bits)

    print("\n  Cache configuration:")
    print_config(cache.config_info())

    print("  Enter memory addresses (decimal or 0x hex).")
    print("  Type 'done' when finished, or 'workload' to use a preset.\n")

    addresses = []
    while True:
        raw = prompt(f"  Address #{len(addresses)+1} ('done'/'workload')", "done")
        if raw.lower() == "done":
            break
        if raw.lower() == "workload":
            wl = prompt("  Workload [sequential/random/temporal_locality/loop/strided/mixed]", "loop")
            n  = int_prompt("  Number of accesses", 100)
            addresses = generate_workload(wl, num_accesses=n)
            print(f"  Generated {len(addresses)} addresses.")
            break
        try:
            addr = int(raw, 0)
            result = cache.access(addr)
            print(f"    => {result}")
            addresses.append(addr)
        except ValueError:
            print("    Invalid address. Try again.")

    if not addresses:
        print("  No addresses provided. Returning to menu.")
        return

    # If workload mode was selected, run all addresses through the (still fresh) cache
    if len(addresses) > len(cache.access_log):
        cache.reset()
        for addr in addresses:
            cache.access(addr)

    s = cache.stats
    print(f"\n  Results:")
    print(f"    Accesses : {s.accesses}")
    print(f"    Hits     : {s.hits}")
    print(f"    Misses   : {s.misses}")
    print(f"    Hit Rate : {s.hit_rate*100:.1f}%")
    print(f"    Miss Rate: {s.miss_rate*100:.1f}%")
    print(f"    AMAT     : {s.amat():.2f} cycles")

    if len(cache.access_log) <= 50:
        print("\n  Full access log:")
        print_access_log(cache.access_log, max_rows=50)

    show_graph = prompt("\n  Show access pattern graph? [y/n]", "y").lower()
    if show_graph == "y":
        plot_access_pattern(cache.access_log, f"Access Pattern — {cache.config_info()['type']}")


# ---------------------------------------------------------------------------
# 3. Replacement Policy Comparison
# ---------------------------------------------------------------------------

def run_policy_comparison():
    print("\n" + "=" * 60)
    print("  REPLACEMENT POLICY COMPARISON")
    print("=" * 60)

    CACHE_SIZE = 512
    BLOCK_SIZE = 16
    WAYS       = 4
    ADDR_BITS  = 16

    wl = prompt("  Workload [sequential/random/temporal_locality/loop/strided/mixed]", "loop")
    n  = int_prompt("  Number of accesses", 200)
    addresses = generate_workload(wl, num_accesses=n)

    print(f"\n  Config: {WAYS}-Way Set Associative, {CACHE_SIZE}B cache, {BLOCK_SIZE}B blocks")
    print(f"  Workload: {wl}, {n} accesses\n")

    results_by_policy = {}
    for policy in ("LRU", "FIFO", "Random"):
        cache = SetAssociativeCache(CACHE_SIZE, BLOCK_SIZE, ways=WAYS,
                                    policy=policy, address_bits=ADDR_BITS)
        for addr in addresses:
            cache.access(addr)
        s = cache.stats
        results_by_policy[policy] = {
            "hit_rate":  s.hit_rate,
            "miss_rate": s.miss_rate,
            "amat":      s.amat(),
        }
        print(f"  {policy:<8} | Hit Rate: {s.hit_rate*100:5.1f}%  | AMAT: {s.amat():.2f}")

    print()
    plot_policy_comparison(results_by_policy,
                           title=f"Policy Comparison — {WAYS}-Way Set Assoc, {wl} workload")


# ---------------------------------------------------------------------------
# 4. Workload Analysis
# ---------------------------------------------------------------------------

def run_workload_analysis():
    print("\n" + "=" * 60)
    print("  WORKLOAD SENSITIVITY ANALYSIS")
    print("=" * 60)

    CACHE_SIZE = 512
    BLOCK_SIZE = 16
    ADDR_BITS  = 16
    N          = 200

    workloads = ["sequential", "random", "temporal_locality", "loop", "strided"]

    caches_cfg = [
        ("Direct Mapped",       lambda: DirectMappedCache(CACHE_SIZE, BLOCK_SIZE, ADDR_BITS)),
        ("2-Way Set (LRU)",     lambda: SetAssociativeCache(CACHE_SIZE, BLOCK_SIZE, 2, "LRU", ADDR_BITS)),
        ("4-Way Set (LRU)",     lambda: SetAssociativeCache(CACHE_SIZE, BLOCK_SIZE, 4, "LRU", ADDR_BITS)),
        ("Fully Assoc (LRU)",   lambda: FullyAssociativeCache(CACHE_SIZE, BLOCK_SIZE, "LRU", ADDR_BITS)),
    ]

    print(f"\n  Cache: {CACHE_SIZE}B, {BLOCK_SIZE}B blocks, {N} accesses per workload\n")

    workload_results = {}
    for wl in workloads:
        addresses = generate_workload(wl, num_accesses=N)
        wl_res = []
        for label, factory in caches_cfg:
            cache = factory()
            for addr in addresses:
                cache.access(addr)
            s = cache.stats
            wl_res.append({
                "name":      label,
                "hit_rate":  s.hit_rate,
                "miss_rate": s.miss_rate,
                "amat":      s.amat(),
            })
        workload_results[wl] = wl_res

    # Print table
    print(f"  {'Workload':<22}", end="")
    for label, _ in caches_cfg:
        print(f"  {label:<22}", end="")
    print()
    print("  " + "-" * (22 + len(caches_cfg) * 24))
    for wl, res in workload_results.items():
        print(f"  {wl:<22}", end="")
        for r in res:
            print(f"  {r['hit_rate']*100:5.1f}%  AMAT={r['amat']:.1f}   ", end="")
        print()

    print()
    plot_workload_sensitivity(workload_results, title="Hit Rate by Workload & Cache Type")


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------

def main():
    print(BANNER)

    while True:
        print(MENU)
        choice = prompt("Select option [1-5]", "5")

        if choice == "1":
            run_full_demo()
        elif choice == "2":
            run_manual()
        elif choice == "3":
            run_policy_comparison()
        elif choice == "4":
            run_workload_analysis()
        elif choice == "5":
            print("\n  Goodbye!\n")
            sys.exit(0)
        else:
            print("  Invalid option. Please enter 1-5.")


if __name__ == "__main__":
    main()
