"""Candidate hosted ADK tool operating only on supplied validated context.

This file is intentionally not labelled as executed IBM code until the team imports it
into its provisioned account and saves a genuine trace.
"""
from typing import Literal
from pydantic import BaseModel, Field, ConfigDict
from ibm_watsonx_orchestrate.agent_builder.tools import tool


class GameContext(BaseModel):
    model_config = ConfigDict(extra='forbid', allow_inf_nan=False)
    sessionId: str
    stateVersion: int = Field(ge=0)
    scoreA: int = Field(ge=0)
    scoreB: int = Field(ge=0)
    quarter: int = Field(ge=1, le=8)
    clockSeconds: float = Field(ge=0)
    paused: bool
    fanAway: bool
    scenario: Literal['critical', 'timeout', 'resumed', 'steady']
    possession: str | None = None
    significantEvent: str | None = None
    availableWindowMinutes: float = Field(ge=0)


class GameResult(BaseModel):
    sessionId: str
    stateVersion: int
    riskScore: int = Field(ge=0, le=100)
    scoreMeaning: str = 'Explainable heuristic score; not a calibrated probability'
    breakdown: list[dict]
    mustReturn: bool
    preferStay: bool


def _derive(context: GameContext):
    rows=[]
    def add(label, points, detail): rows.append({'label':label,'points':points,'detail':detail})
    diff=abs(context.scoreA-context.scoreB)
    if diff<=2: add('One-possession score',25,f'{diff}-point margin')
    elif diff<=5: add('Close score',18,f'{diff}-point margin')
    elif diff<=10: add('Competitive score',8,f'{diff}-point margin')
    if context.quarter>=4 and context.clockSeconds<=120: add('Final two minutes',30,f'{int(context.clockSeconds)} seconds remaining')
    elif context.quarter>=4 and context.clockSeconds<=300: add('Late fourth quarter',20,'Late fourth-quarter context')
    elif context.quarter>=3: add('Late-game context',5,f'Quarter {context.quarter}')
    add('Play paused' if context.paused else 'Live play',-45 if context.paused else 15,'Safer movement window' if context.paused else 'Play is active')
    if context.significantEvent: add('Significant event',20,context.significantEvent)
    if context.scenario=='resumed': add('Play just resumed',10,'Movement window closed')
    if context.possession: add('Possession active',5,f'{context.possession} possession')
    return max(0,min(100,sum(row['points'] for row in rows))),rows


@tool()
def calculate_moment_risk(context: GameContext) -> GameResult:
    """Calculate explainable game-risk constraints from a supplied snapshot."""
    score,breakdown=_derive(context)
    return GameResult(
        sessionId=context.sessionId,
        stateVersion=context.stateVersion,
        riskScore=score,
        breakdown=breakdown,
        mustReturn=context.fanAway and (not context.paused or score>=75),
        preferStay=score>=75,
    )
