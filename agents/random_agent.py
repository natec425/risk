import risk
from .helpers import available_actions

def strategy(state: risk.RiskState) -> risk.Move:
    return next(available_actions(state).sample(1))
