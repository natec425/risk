import risk
import random
import util
import itertools

class Actions:
    def __init__(self, sample, iter, length):
        self.sample = sample
        self.iter = iter
        self.length = length

    def __iter__(self):
        return self.iter()

    def sample(self, n):
        yield from self.sample(n)

    def __len__(self):
        return self.length


def available_actions(state: risk.RiskState) -> Actions:
    if isinstance(state, risk.PrePlaceState):
        return preplace_actions(state)
    elif isinstance(state, risk.PreAssignState):
        return preassign_actions(state)
    elif isinstance(state, risk.PlaceState):
        return place_actions(state)
    elif isinstance(state, risk.AttackState):
        return attack_actions(state)
    elif isinstance(state, risk.FortifyState):
        return fortify_actions(state)
    elif isinstance(state, risk.TerminalState):
        return terminal_actions(state)
    else:
        raise ValueError(f"Invalid state type {type(state)}")


def preplace_actions(state: risk.PrePlaceState) -> Actions:
    unoccupied_territories = [t.name for t in state.territories if t.owner is None]

    def sample(n):
        for t in random.sample(unoccupied_territories, n):
            yield risk.PrePlace(t)

    def _iter():
        for name in unoccupied_territories:
            yield risk.PrePlace(name)

    return Actions(sample, _iter, len(unoccupied_territories))


def preassign_actions(state: risk.PreAssignState) -> Actions:
    owned_terrs = [t.name for t in state.territories_owned(state.current_player)]

    def sample(n):
        for t in random.sample(owned_terrs, n):
            yield risk.PreAssign(t)

    def _iter():
        for name in owned_terrs:
            yield risk.PreAssign(name)

    return Actions(sample, _iter, len(owned_terrs))


def place_actions(state: risk.PlaceState) -> Actions:
    num_territories = sum(1 for _ in state.territories_owned(state.current_player))
    num_reinforcements = state.reinforcements(state.current_player)

    action_space_len = int(
        sum(
            util.choose(num_territories, n) * util.choose(num_reinforcements - 1, n - 1)
            for n in range(1, min(num_territories, num_reinforcements))))

    territories_owned = [t.name for t in state.territories_owned(state.current_player)]
    reinforcements = state.reinforcements(state.current_player)
    max_n = min(len(territories_owned), reinforcements)

    def sample(n):
        actions = []
        while len(actions) < n:
            n = random.randint(1, max_n)
            combo_i = random.randint(0, util.choose(len(territories_owned), n) - 1)
            alloc_i = random.randint(0, util.choose(reinforcements - 1, n - 1) - 1)
            combo = util.kth_n_combination(territories_owned, n, combo_i)
            alloc = util.kth_n_integer_composition(reinforcements, n, alloc_i)
            action = risk.Place(combo, alloc)
            if action not in actions:
                yield action
                actions.append(action)

    def _iter():
        for n in range(1, max_n):
            for terrs in itertools.combinations(territories_owned, n):
                for troops in util.integer_compositions(reinforcements, n):
                    yield risk.Place(terrs, troops)

    return Actions(sample, _iter, action_space_len)


def attack_actions(state: risk.AttackState) -> Actions:
    actions = [
        risk.Attack(owned.name, neighbor, troops)
        for owned in state.territories_owned(state.current_player)
        for neighbor in state.neighbors(owned)
        if state.owner(neighbor).name != state.current_player.name
        for troops in range(2, state.troops(owned))
    ] + [risk.DontAttack()]

    def sample(n):
        yield from random.sample(actions, n)

    def _iter():
        return iter(actions)

    return Actions(sample, _iter, len(actions))


def fortify_actions(state: risk.FortifyState) -> Actions:
    terrs_owned = set(state.territories_owned(state.current_player))
    actions = [
        risk.Fortify(source.name, dest, n)
        for source in terrs_owned for dest in state.neighbors(source)
        if dest in terrs_owned for n in range(1, state.troops(source) - 1)
    ] + [risk.DontFortify()]

    def sample(n):
        yield from random.sample(actions, n)

    def _iter():
        return iter(actions)

    return Actions(sample, _iter, len(actions))


def terminal_actions(state: risk.TerminalState) -> Actions:
    def sample(n):
        raise ValueError('No Actions from Terminal state')

    return Actions(sample, lambda: iter([]), 0)
