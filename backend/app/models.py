from typing import Literal, Any
from pydantic import BaseModel, Field, ConfigDict

Need = Literal['food', 'restroom', 'shop']
Action = Literal['GO', 'WAIT', 'STAY', 'RETURN']


class StrictModel(BaseModel):
    model_config = ConfigDict(extra='forbid', allow_inf_nan=False)


class ScenarioInput(StrictModel):
    scenario: Literal['critical', 'timeout', 'resumed', 'steady']


class NeedInput(StrictModel):
    need: Need


class Fan(StrictModel):
    id: str = Field(default='primary', max_length=64)
    seat: str = 'seat-101'
    position: str = 'seat-101'
    section: str = '101'
    speed: float = Field(default=72, ge=15, le=150, description='metres per minute')
    accessible: bool = False
    delivery: bool = False
    need: Need = 'food'
    trip: dict | None = None


class Preferences(StrictModel):
    accessible: bool = False
    delivery: bool = False
    speed: float = Field(default=72, ge=15, le=150)


class FacilityChange(StrictModel):
    queue: int | None = Field(default=None, ge=0, le=1000)
    open: bool | None = None
    congestion: float | None = Field(default=None, ge=1, le=5)


class Tick(StrictModel):
    seconds: int = Field(default=10, ge=1, le=600)


class Auto(StrictModel):
    enabled: bool


class OrderInput(StrictModel):
    facility: str
    item: str
    quantity: int = Field(default=1, ge=1, le=10)
    mode: Literal['pickup', 'delivery'] = 'pickup'
    confirmed: bool = False


class Proposal(StrictModel):
    sessionId: str
    stateVersion: int
    action: Action
    destination: str | None = None
    summary: str = Field(max_length=2000)


class Event(StrictModel):
    type: str
    timestamp: str
    sessionId: str
    stateVersion: int
    payload: dict[str, Any]


class RouteResult(StrictModel):
    path: list[str]
    distanceMeters: float = Field(ge=0)
    minutes: float = Field(ge=0)


class Calculation(StrictModel):
    destination: str
    name: str
    route: RouteResult
    returnRoute: RouteResult
    queueMinutes: float = Field(ge=0)
    serviceMinutes: float = Field(ge=0)
    safetyBufferMinutes: float = Field(ge=0)
    roundTripMinutes: float = Field(ge=0)
    accessible: bool = True
    delivery: bool = False
    predictedPeople: int = Field(default=0, ge=0)


class TripEstimate(StrictModel):
    walkMinutes: float = Field(ge=0)
    queueMinutes: float = Field(ge=0)
    distanceMeters: float = Field(ge=0)


class Recommendation(StrictModel):
    action: Action
    confidence: None = None
    title: str
    explanation: str
    reason: str
    roundTripMinutes: float | None
    tripEstimate: TripEstimate
    destination: str | None
    options: list[Calculation]
    calculation: Calculation | None
    riskScore: int = Field(ge=0, le=100)
    riskScale: str
    riskBreakdown: list[dict[str, Any]] = Field(default_factory=list)
    availableWindowMinutes: float = Field(ge=0)
    safeWindow: dict[str, Any] = Field(default_factory=dict)
    bestAlternative: dict[str, Any] | None = None
    recommendedMode: Literal['trip', 'delivery', 'none'] = 'none'
    metrics: dict[str, float]


class GameState(BaseModel):
    model_config = ConfigDict(extra='allow', allow_inf_nan=False)
    scenario: Literal['critical', 'timeout', 'resumed', 'steady']
    need: Need
    venue: str
    dataMode: Literal['SIMULATED']
    trip: TripEstimate
    scoreA: int = Field(ge=0)
    scoreB: int = Field(ge=0)
    clock: str
    gameState: str
    momentIntensity: int = Field(ge=0, le=100)
    availableWindowMinutes: float = Field(ge=0)
    fanAwayFromSeat: bool


class Snapshot(BaseModel):
    state: GameState
    recommendation: Recommendation
    updatedAt: str
    sessionId: str
    stateVersion: int
    facilities: list[dict]
    routeConnections: list[dict]
    fans: list[Fan]
    fan: Fan
    orders: list[dict]
    agents: list[dict]
    automatic: bool
    provenance: dict
