"""
Cache Memory Simulator
======================
Simulates three cache organization types:
  1. Direct Mapped Cache
  2. Set Associative Cache  (N-way)
  3. Fully Associative Cache

Address breakdown (for a 32-bit address):
  | TAG | INDEX | BLOCK OFFSET |

Performance metrics tracked:
  - Hits, Misses, Hit Rate, Miss Rate
  - AMAT = Hit_Time + Miss_Rate × Miss_Penalty
"""

import math
from dataclasses import dataclass, field
from replacement_policies import get_policy, POLICY_MAP


# ---------------------------------------------------------------------------
# Cache Block
# ---------------------------------------------------------------------------

@dataclass
class CacheBlock:
    """A single line/block in the cache."""
    valid: bool = False
    tag: int = -1


# ---------------------------------------------------------------------------
# Statistics
# ---------------------------------------------------------------------------

class CacheStats:
    """Tracks and computes cache performance metrics."""

    def __init__(self):
        self.hits = 0
        self.misses = 0
        self.accesses = 0

    @property
    def hit_rate(self) -> float:
        return self.hits / self.accesses if self.accesses > 0 else 0.0

    @property
    def miss_rate(self) -> float:
        return self.misses / self.accesses if self.accesses > 0 else 0.0

    def amat(self, hit_time: int = 1, miss_penalty: int = 100) -> float:
        """Average Memory Access Time (in cycles)."""
        return hit_time + self.miss_rate * miss_penalty

    def reset(self):
        self.hits = self.misses = self.accesses = 0

    def summary(self) -> dict:
        return {
            "accesses": self.accesses,
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": self.hit_rate,
            "miss_rate": self.miss_rate,
            "amat": self.amat(),
        }


# ---------------------------------------------------------------------------
# Direct Mapped Cache
# ---------------------------------------------------------------------------

class DirectMappedCache:
    """
    Direct Mapped Cache
    -------------------
    Each memory block maps to exactly ONE cache line.

    Address fields:
        | TAG (remaining) | INDEX (log2 num_blocks) | OFFSET (log2 block_size) |

    Parameters:
        cache_size  : Total cache size in bytes
        block_size  : Block (line) size in bytes
        address_bits: Width of memory addresses (default 32)
    """

    cache_type = "Direct Mapped"

    def __init__(self, cache_size: int, block_size: int, address_bits: int = 32):
        assert cache_size % block_size == 0, "cache_size must be divisible by block_size"

        self.cache_size = cache_size
        self.block_size = block_size
        self.address_bits = address_bits
        self.num_blocks = cache_size // block_size

        self.offset_bits = int(math.log2(block_size))
        self.index_bits  = int(math.log2(self.num_blocks))
        self.tag_bits    = address_bits - self.index_bits - self.offset_bits

        self.blocks: list[CacheBlock] = [CacheBlock() for _ in range(self.num_blocks)]
        self.stats = CacheStats()
        self.access_log: list[dict] = []

    # --- Address decomposition ---

    def _parse(self, address: int) -> tuple[int, int, int]:
        offset = address & ((1 << self.offset_bits) - 1)
        index  = (address >> self.offset_bits) & ((1 << self.index_bits) - 1)
        tag    = address >> (self.offset_bits + self.index_bits)
        return tag, index, offset

    # --- Memory access ---

    def access(self, address: int) -> str:
        tag, index, offset = self._parse(address)
        block = self.blocks[index]
        self.stats.accesses += 1

        if block.valid and block.tag == tag:
            self.stats.hits += 1
            result = "HIT"
        else:
            self.stats.misses += 1
            block.valid = True
            block.tag   = tag
            result = "MISS"

        self.access_log.append({
            "address": hex(address),
            "tag":     tag,
            "index":   index,
            "offset":  offset,
            "result":  result,
        })
        return result

    def reset(self):
        self.blocks = [CacheBlock() for _ in range(self.num_blocks)]
        self.stats.reset()
        self.access_log.clear()

    def config_info(self) -> dict:
        return {
            "type":        self.cache_type,
            "cache_size":  f"{self.cache_size} B",
            "block_size":  f"{self.block_size} B",
            "num_blocks":  self.num_blocks,
            "tag_bits":    self.tag_bits,
            "index_bits":  self.index_bits,
            "offset_bits": self.offset_bits,
        }


# ---------------------------------------------------------------------------
# Set Associative Cache
# ---------------------------------------------------------------------------

class SetAssociativeCache:
    """
    N-Way Set Associative Cache
    ---------------------------
    Cache is divided into sets; each set holds N ways (lines).
    A memory block maps to one specific set, but any way within it.

    Address fields:
        | TAG (remaining) | SET INDEX (log2 num_sets) | OFFSET (log2 block_size) |

    Parameters:
        cache_size  : Total cache size in bytes
        block_size  : Block (line) size in bytes
        ways        : Number of ways (associativity) per set
        policy      : Replacement policy name ("LRU", "FIFO", "Random")
        address_bits: Width of memory addresses (default 32)
    """

    cache_type = "Set Associative"

    def __init__(
        self,
        cache_size: int,
        block_size: int,
        ways: int,
        policy: str = "LRU",
        address_bits: int = 32,
    ):
        assert cache_size % (block_size * ways) == 0, \
            "cache_size must be divisible by (block_size × ways)"

        self.cache_size  = cache_size
        self.block_size  = block_size
        self.ways        = ways
        self.policy_name = policy
        self.address_bits = address_bits
        self.num_sets    = cache_size // (block_size * ways)

        self.offset_bits = int(math.log2(block_size))
        self.index_bits  = int(math.log2(self.num_sets)) if self.num_sets > 1 else 0
        self.tag_bits    = address_bits - self.index_bits - self.offset_bits

        self._init_storage()
        self.stats = CacheStats()
        self.access_log: list[dict] = []

    def _init_storage(self):
        num_sets = max(self.num_sets, 1)
        self.sets: list[list[CacheBlock]] = [
            [CacheBlock() for _ in range(self.ways)]
            for _ in range(num_sets)
        ]
        self.policies = [
            get_policy(self.policy_name, self.ways)
            for _ in range(num_sets)
        ]

    def _parse(self, address: int) -> tuple[int, int, int]:
        offset = address & ((1 << self.offset_bits) - 1)
        index  = (address >> self.offset_bits) & ((1 << self.index_bits) - 1) \
                 if self.index_bits > 0 else 0
        tag    = address >> (self.offset_bits + self.index_bits)
        return tag, index, offset

    def access(self, address: int) -> str:
        tag, index, offset = self._parse(address)
        cache_set = self.sets[index]
        policy    = self.policies[index]
        self.stats.accesses += 1

        # Check for hit
        for way, block in enumerate(cache_set):
            if block.valid and block.tag == tag:
                self.stats.hits += 1
                policy.on_hit(way)
                self.access_log.append({
                    "address": hex(address), "tag": tag,
                    "index": index, "offset": offset,
                    "result": "HIT", "way": way,
                })
                return "HIT"

        # Miss — find an empty slot first, then use policy
        self.stats.misses += 1
        victim_way = next(
            (w for w, b in enumerate(cache_set) if not b.valid), None
        )
        if victim_way is None:
            victim_way = policy.get_victim()

        cache_set[victim_way].valid = True
        cache_set[victim_way].tag   = tag
        policy.on_miss(victim_way)

        self.access_log.append({
            "address": hex(address), "tag": tag,
            "index": index, "offset": offset,
            "result": "MISS", "way": victim_way,
        })
        return "MISS"

    def reset(self):
        self._init_storage()
        self.stats.reset()
        self.access_log.clear()

    def config_info(self) -> dict:
        return {
            "type":        f"{self.ways}-Way {self.cache_type}",
            "policy":      self.policy_name,
            "cache_size":  f"{self.cache_size} B",
            "block_size":  f"{self.block_size} B",
            "num_sets":    self.num_sets,
            "ways":        self.ways,
            "tag_bits":    self.tag_bits,
            "index_bits":  self.index_bits,
            "offset_bits": self.offset_bits,
        }


# ---------------------------------------------------------------------------
# Fully Associative Cache
# ---------------------------------------------------------------------------

class FullyAssociativeCache(SetAssociativeCache):
    """
    Fully Associative Cache
    -----------------------
    Special case of Set Associative with a SINGLE set.
    Any memory block can occupy any cache line.
    Requires comparing tag with ALL cache lines on every access.

    Address fields:
        | TAG (all remaining bits) | OFFSET (log2 block_size) |
        (No index field)

    Parameters:
        cache_size  : Total cache size in bytes
        block_size  : Block (line) size in bytes
        policy      : Replacement policy ("LRU", "FIFO", "Random")
        address_bits: Width of memory addresses (default 32)
    """

    cache_type = "Fully Associative"

    def __init__(
        self,
        cache_size: int,
        block_size: int,
        policy: str = "LRU",
        address_bits: int = 32,
    ):
        ways = cache_size // block_size  # 1 set with all ways
        super().__init__(cache_size, block_size, ways=ways, policy=policy, address_bits=address_bits)

    def config_info(self) -> dict:
        info = super().config_info()
        info["type"]   = self.cache_type
        info["policy"] = self.policy_name
        info["num_sets"] = 1
        return info


# ---------------------------------------------------------------------------
# Workload Generator
# ---------------------------------------------------------------------------

def generate_workload(workload_type: str, num_accesses: int = 200, seed: int = 42) -> list[int]:
    """
    Generate a memory address trace for testing.

    Types:
        sequential       : Linear scan — good spatial locality
        random           : Fully random — no locality
        temporal_locality: Small hot working set accessed repeatedly
        loop             : Array loop (repeated sequential scan)
        strided          : Fixed stride — can cause conflict misses
        mixed            : Combination of all patterns
    """
    import random as rng
    rng.seed(seed)

    if workload_type == "sequential":
        return [i * 4 for i in range(num_accesses)]

    elif workload_type == "random":
        return [rng.randint(0, 4095) * 4 for _ in range(num_accesses)]

    elif workload_type == "temporal_locality":
        hot = [i * 16 for i in range(8)]          # 8 "hot" addresses
        addrs = []
        while len(addrs) < num_accesses:
            addrs.extend(rng.choices(hot, k=len(hot)))
        return addrs[:num_accesses]

    elif workload_type == "loop":
        loop_body = [i * 4 for i in range(16)]     # 16-element array
        addrs = []
        while len(addrs) < num_accesses:
            addrs.extend(loop_body)
        return addrs[:num_accesses]

    elif workload_type == "strided":
        stride = 64                                 # bytes — 4 blocks at 16 B/block
        return [(i * stride) % 4096 for i in range(num_accesses)]

    elif workload_type == "mixed":
        seq  = [i * 4 for i in range(50)]
        hot  = [0, 16, 32, 48] * 25
        rand = [rng.randint(0, 4095) * 4 for _ in range(num_accesses - 100)]
        addrs = seq + hot + rand
        rng.shuffle(addrs)
        return addrs[:num_accesses]

    else:
        raise ValueError(f"Unknown workload type: '{workload_type}'")
