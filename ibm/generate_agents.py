"""Generate import candidates only after selecting a model actually available in account."""
import argparse,json
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--model',required=True);p.add_argument('--output',default='ibm/generated')
a=p.parse_args();out=Path(a.output);out.mkdir(parents=True,exist_ok=True)
for name,description,instructions,tools,collaborators in [
 ('game_intelligence','Analyze game risk from supplied state','Always invoke calculate_moment_risk using the supplied validated snapshot. Return the tool result with sessionId and stateVersion. Never invent a game event.', ['calculate_moment_risk'],[]),
 ('momentguard_coordinator','Coordinate safe stadium trip proposals','Delegate game analysis to game_intelligence. Use supplied facility options only. Propose JSON with sessionId, stateVersion, action, destination and summary. Do not place orders. The backend has final authority. Never claim an uninvoked tool ran.',[],['game_intelligence'])]:
    (out/f'{name}.json').write_text(json.dumps(dict(spec_version='v1',style='react',name=name,llm=a.model,description=description,instructions=instructions,tools=tools,collaborators=collaborators),indent=2))
