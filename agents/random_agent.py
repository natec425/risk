import risk

def strategy(state: risk.RiskState) -> risk.Move:
    return next(state.available_actions().sample(1))
