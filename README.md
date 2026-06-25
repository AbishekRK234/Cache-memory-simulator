# Cache Memory Simulator

A Flask-based web application that simulates CPU cache memory behavior across different cache organizations, replacement policies, and access workloads. Built as a Computer Organization & Architecture (COA) project to visualize how cache design choices affect hit rate, miss rate, and average memory access time (AMAT).

## Features

* **Three cache organizations:** Direct Mapped, Set Associative (N-way), and Fully Associative
* **Three replacement policies:** LRU (Least Recently Used), FIFO (First In First Out), and Random
* **Five workload patterns:** sequential, random, temporal locality, loop, and strided access
* **Performance metrics:** hit rate, miss rate, and AMAT (Average Memory Access Time, computed as `hit_time + miss_rate × miss_penalty`)
* **Comparison modes:**
  * Compare Direct Mapped vs 2-Way vs 4-Way vs Fully Associative
  * Compare LRU vs FIFO vs Random on a 4-way set associative cache
  * Run all workload types across all cache configurations at once

## Project Structure

```
Cache-memory-simulator/
├── app.py                      # Flask web app (run this)
├── cache_simulator.py          # Core cache classes & workload generator
├── replacement_policies.py     # LRU, FIFO, Random policy implementations
├── analysis.py                 # Analysis / comparison helpers
├── main.py                     # Standalone simulation runner
├── requirements.txt            # Python dependencies
├── How to run.txt              # Quick setup steps
└── templates/
    └── index.html              # Web interface
```

## Setup Instructions

**Recommended Python Version:** 3.10 or 3.11

### Step 1: Create a virtual environment

```bash
# Windows
python -m venv myenv
myenv\Scripts\activate

# macOS / Linux
python3 -m venv myenv
source myenv/bin/activate
```

### Step 2: Install dependencies

```bash
pip install -r requirements.txt
```

### Step 3: Run the application

```bash
python app.py
```

Then open your browser to **http://localhost:5000**

## How to Use

1. **Configure the cache** — set cache size, block size, address bits, associativity (ways), and replacement policy.
2. **Choose a workload** — pick an access pattern (sequential, random, temporal locality, loop, or strided) and the number of accesses.
3. **Simulate** — run a single configuration to see hits, misses, hit/miss rate, AMAT, and an access log.
4. **Compare** — use the comparison modes to benchmark cache organizations against each other, evaluate replacement policies, or sweep every workload across every configuration.

## Cache Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| Cache size | Total cache size in bytes | 512 |
| Block size | Bytes per cache block | 16 |
| Address bits | Width of the memory address space | 16 |
| Ways | Associativity (for set associative) | 4 |
| Policy | Replacement policy (LRU / FIFO / Random) | LRU |

## AMAT Model

Average Memory Access Time is calculated with a hit time of 1 cycle and a miss penalty of 100 cycles:

```
AMAT = hit_time + (miss_rate × miss_penalty)
```

## Tech Stack

Python, Flask, NumPy, Matplotlib

## Author

* Abishek R.K (24WU0101048)
