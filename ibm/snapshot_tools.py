"""Hosted ADK tool: operates only on supplied context, with no localhost calls.
Not imported, deployed or executed on IBM until account capability verification.
"""
from pydantic import BaseModel, Field, ConfigDict
from ibm_watsonx_orchestrate.agent_builder.tools import tool

class GameContext(BaseModel):
    model_config = ConfigDict(extra='forbid', allow_inf_nan=False)
    sessionId: str
    stateVersion: int = Field(ge=0)
    momentIntensity: int = Field(ge=0,le=100)
    paused: bool
    fanAway: bool
    availableWindowMinutes: float = Field(ge=0)

class GameResult(BaseModel):
    sessionId: str
    stateVersion: int
    riskScore: int
    scoreMeaning: str = 'Heuristic score; not a calibrated probability'
    mustReturn: bool
    preferStay: bool

@tool()
def calculate_moment_risk(context: GameContext) -> GameResult:
    """Calculate deterministic game constraints from a validated simulation snapshot.

    Args:
        context: Supplied game snapshot; never retrieve localhost or invent game facts.
    Returns:
        Versioned game risk constraints for the coordinator to consider.
    """
    return GameResult(sessionId=context.sessionId,stateVersion=context.stateVersion,riskScore=context.momentIntensity,mustReturn=context.fanAway and (not context.paused or context.momentIntensity>=75),preferStay=context.momentIntensity>=75)
