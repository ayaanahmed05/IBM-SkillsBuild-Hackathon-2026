from typing import Protocol

class GameProvider(Protocol):
    """A replacement must supply one coherent game and explicit provenance."""
    def snapshot(self) -> dict: ...

class VenueProvider(Protocol):
    def facilities(self) -> list[dict]: ...

class SimulatedGameProvider:
    def __init__(self, runtime): self.runtime=runtime
    def snapshot(self):
        return {'data':dict(self.runtime.game),'provenance':{'kind':'Simulated','source':'MomentGuard seeds'}}

class SimulatedVenueProvider:
    def __init__(self,runtime): self.runtime=runtime
    def facilities(self):
        from copy import deepcopy
        return deepcopy(self.runtime.facilities)
