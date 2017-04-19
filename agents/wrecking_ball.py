import risk
from .console_agent import show_game_state


def most_friendly_connections(state: risk.RiskState) -> risk.Territory:
    available_territories = [t for t in state.territories if t.owner is None]
    my_territories = {t.name for t in state.territories_owned(state.current_player)}
    num_friendly_neighbors = lambda t: len(set(state.neighbors(t)).intersection(my_territories))
    return max(available_territories, key=num_friendly_neighbors)


def most_fortified_frontline_territory(state: risk.RiskState) -> risk.Territory:
    frontline_territories = [
        t for t in state.territories_owned(state.current_player)
        if any(state.owner(n) != state.current_player for n in state.neighbors(t))
    ]
    return max(frontline_territories, key=lambda t: state.troops(t))


def can_attack(state: risk.RiskState, t: risk.Territory) -> bool:
    neighbors_enemy = len([n for n in state.neighbors(t)
                           if state.owner(n) != state.current_player]) != 0
    return neighbors_enemy and state.troops(t) > 5


def strategy(state: risk.RiskState) -> risk.Move:
    if isinstance(state, risk.PrePlaceState):
        return risk.PrePlace(most_friendly_connections(state).name)
    elif isinstance(state, risk.PreAssignState):
        return risk.PreAssign(most_fortified_frontline_territory(state).name)
    elif isinstance(state, risk.PlaceState):
        return risk.Place([most_fortified_frontline_territory(state).name],
                          [state.reinforcements(state.current_player)])
    elif isinstance(state, risk.AttackState):
        attackable_states = [
            t for t in state.territories_owned(state.current_player) if can_attack(state, t)
        ]
        if attackable_states:
            from_territory = max(attackable_states, key=lambda t: state.troops(t))
            enemy_neighbors = [
                n for n in state.neighbors(from_territory) if state.owner(n) != state.current_player
            ]
            to_territory = max(enemy_neighbors, key=state.troops)
            return risk.Attack(from_territory.name, to_territory, state.troops(from_territory))
        else:
            return risk.DontAttack()
    elif isinstance(state, risk.FortifyState):
        return risk.DontFortify()
