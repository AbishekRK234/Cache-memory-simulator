"""
Cache Memory Simulator — Flask Web Application
================================================
Replaces the Tkinter GUI with a web-based interface.
Backend logic (cache_simulator.py, replacement_policies.py) remains unchanged.

Run:
    python app.py
Then open http://localhost:5000 in your browser.
"""

from flask import Flask, jsonify, request, render_template
from cache_simulator import (
    DirectMappedCache,
    SetAssociativeCache,
    FullyAssociativeCache,
    generate_workload,
)

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


def _make_cache(params):
    """Create a cache object from request parameters."""
    cache_type = params.get("cache_type", "Direct Mapped")
    cache_size = int(params.get("cache_size", 512))
    block_size = int(params.get("block_size", 16))
    addr_bits = int(params.get("addr_bits", 16))
    ways = int(params.get("ways", 4))
    policy = params.get("policy", "LRU")

    if cache_type == "Direct Mapped":
        return DirectMappedCache(cache_size, block_size, addr_bits)
    elif cache_type == "Set Associative":
        return SetAssociativeCache(cache_size, block_size, ways, policy, addr_bits)
    else:
        return FullyAssociativeCache(cache_size, block_size, policy, addr_bits)


@app.route("/api/simulate", methods=["POST"])
def simulate():
    """Run a single simulation with given config and workload."""
    try:
        data = request.json
        cache = _make_cache(data)
        workload = data.get("workload", "loop")
        n_accesses = int(data.get("n_accesses", 200))

        addresses = generate_workload(workload, n_accesses)
        for addr in addresses:
            cache.access(addr)

        s = cache.stats
        return jsonify({
            "config": cache.config_info(),
            "stats": {
                "accesses": s.accesses,
                "hits": s.hits,
                "misses": s.misses,
                "hit_rate": s.hit_rate,
                "miss_rate": s.miss_rate,
                "amat": s.amat(),
            },
            "access_log": cache.access_log[:50],
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/api/compare", methods=["POST"])
def compare():
    """Compare Direct Mapped / 2-Way / 4-Way / Fully Associative."""
    try:
        data = request.json
        cache_size = int(data.get("cache_size", 512))
        block_size = int(data.get("block_size", 16))
        addr_bits = int(data.get("addr_bits", 16))
        workload = data.get("workload", "loop")
        n_accesses = int(data.get("n_accesses", 200))

        addresses = generate_workload(workload, n_accesses)

        configs = [
            ("Direct Mapped", DirectMappedCache(cache_size, block_size, addr_bits)),
            ("2-Way Set (LRU)", SetAssociativeCache(cache_size, block_size, 2, "LRU", addr_bits)),
            ("4-Way Set (LRU)", SetAssociativeCache(cache_size, block_size, 4, "LRU", addr_bits)),
            ("Fully Assoc (LRU)", FullyAssociativeCache(cache_size, block_size, "LRU", addr_bits)),
        ]

        results = []
        for label, cache in configs:
            for addr in addresses:
                cache.access(addr)
            s = cache.stats
            results.append({
                "name": label,
                "hit_rate": s.hit_rate,
                "miss_rate": s.miss_rate,
                "amat": s.amat(),
            })

        return jsonify({"results": results, "workload": workload})
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/api/policy", methods=["POST"])
def policy_compare():
    """Compare LRU / FIFO / Random on 4-Way Set Associative."""
    try:
        data = request.json
        cache_size = int(data.get("cache_size", 512))
        block_size = int(data.get("block_size", 16))
        addr_bits = int(data.get("addr_bits", 16))
        workload = data.get("workload", "loop")
        n_accesses = int(data.get("n_accesses", 200))

        addresses = generate_workload(workload, n_accesses)

        results = {}
        for policy in ("LRU", "FIFO", "Random"):
            cache = SetAssociativeCache(cache_size, block_size, 4, policy, addr_bits)
            for addr in addresses:
                cache.access(addr)
            s = cache.stats
            results[policy] = {
                "hit_rate": s.hit_rate,
                "miss_rate": s.miss_rate,
                "amat": s.amat(),
            }

        return jsonify({"results": results, "workload": workload})
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/api/workload", methods=["POST"])
def workload_analysis():
    """Run all workload types across all cache configurations."""
    try:
        data = request.json
        cache_size = int(data.get("cache_size", 512))
        block_size = int(data.get("block_size", 16))
        addr_bits = int(data.get("addr_bits", 16))
        n_accesses = int(data.get("n_accesses", 200))

        workloads = ["sequential", "random", "temporal_locality", "loop", "strided"]
        cache_cfgs = [
            ("Direct Mapped", lambda: DirectMappedCache(cache_size, block_size, addr_bits)),
            ("2-Way Set (LRU)", lambda: SetAssociativeCache(cache_size, block_size, 2, "LRU", addr_bits)),
            ("4-Way Set (LRU)", lambda: SetAssociativeCache(cache_size, block_size, 4, "LRU", addr_bits)),
            ("Fully Assoc (LRU)", lambda: FullyAssociativeCache(cache_size, block_size, "LRU", addr_bits)),
        ]

        results = {}
        for wl in workloads:
            addresses = generate_workload(wl, n_accesses)
            wl_res = []
            for label, factory in cache_cfgs:
                cache = factory()
                for addr in addresses:
                    cache.access(addr)
                s = cache.stats
                wl_res.append({
                    "name": label,
                    "hit_rate": s.hit_rate,
                    "miss_rate": s.miss_rate,
                    "amat": s.amat(),
                })
            results[wl] = wl_res

        return jsonify({"results": results})
    except Exception as e:
        return jsonify({"error": str(e)}), 400


if __name__ == "__main__":
    app.run(debug=True, port=5000)
