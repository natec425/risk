from concurrent.futures import ProcessPoolExecutor
import itertools

import risk


def play_game(players):
    state = risk.new_game([p for p in players])
    while not state.is_terminal():
        state = state.transition(
            players[state.current_player.name](state.copy()))
    return state.winner().name


def play_games(players, n):
    wins = {p: 0 for p in players}
    with ProcessPoolExecutor(max_workers=4) as executor:
        for winner in executor.map(play_game, itertools.repeat(players, n)):
            wins[winner] += 1
    return wins


def get_action(state):
    return next(state.available_actions().sample(1))


if __name__ == '__main__':
    players = {"Nate": get_action, "Chris": get_action}

    print(play_game(players))
