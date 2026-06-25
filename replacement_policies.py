"""
Replacement Policies for Cache Memory Simulation
=================================================
Implements three common cache replacement policies:
  - LRU   : Least Recently Used
  - FIFO  : First In, First Out
  - Random: Random eviction
"""

from collections import deque
import random


class LRUPolicy:
    """
    Least Recently Used (LRU) Replacement Policy.

    Evicts the cache way that was accessed least recently.
    Maintains an ordered list where the front = LRU, back = MRU.
    """

    def __init__(self, ways: int):
        self.ways = ways
        # Order: index 0 = least recently used, -1 = most recently used
        self.order: list[int] = list(range(ways))

    def on_hit(self, way: int):
        """Move the accessed way to the most-recently-used position."""
        self.order.remove(way)
        self.order.append(way)

    def on_miss(self, way: int):
        """Record newly loaded way as most recently used."""
        if way in self.order:
            self.order.remove(way)
        self.order.append(way)

    def get_victim(self) -> int:
        """Return the way index to evict (least recently used)."""
        return self.order[0]

    def reset(self):
        self.order = list(range(self.ways))


class FIFOPolicy:
    """
    First In, First Out (FIFO) Replacement Policy.

    Evicts the way that was loaded into the cache first,
    regardless of how often it has been accessed since.
    """

    def __init__(self, ways: int):
        self.ways = ways
        self.queue: deque[int] = deque()
        self._in_queue: set[int] = set()

    def on_hit(self, way: int):
        """FIFO does NOT update order on a cache hit."""
        pass

    def on_miss(self, way: int):
        """Record newly loaded way at the back of the FIFO queue."""
        if way not in self._in_queue:
            self.queue.append(way)
            self._in_queue.add(way)

    def get_victim(self) -> int:
        """Return the oldest-loaded way (front of queue)."""
        victim = self.queue.popleft()
        self._in_queue.discard(victim)
        return victim

    def reset(self):
        self.queue = deque()
        self._in_queue = set()


class RandomPolicy:
    """
    Random Replacement Policy.

    Evicts a randomly chosen cache way.
    Simple to implement in hardware; performance depends on workload.
    """

    def __init__(self, ways: int):
        self.ways = ways

    def on_hit(self, way: int):
        pass

    def on_miss(self, way: int):
        pass

    def get_victim(self) -> int:
        """Return a randomly selected way index."""
        return random.randint(0, self.ways - 1)

    def reset(self):
        pass


# Factory helper
POLICY_MAP = {
    "LRU": LRUPolicy,
    "FIFO": FIFOPolicy,
    "Random": RandomPolicy,
}


def get_policy(name: str, ways: int):
    """Instantiate a replacement policy by name."""
    cls = POLICY_MAP.get(name)
    if cls is None:
        raise ValueError(f"Unknown policy '{name}'. Choose from: {list(POLICY_MAP)}")
    return cls(ways)
