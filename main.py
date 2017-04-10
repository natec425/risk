import itertools
from concurrent.futures import ProcessPoolExecutor
from multiprocessing import cpu_count

import agents
import risk


def play_game(players):
    state = risk.new_game([p for p in players])
    while not state.is_terminal():
        state = state.transition(
            players[state.current_player.name](state.copy()))
    return state.winner().name


def play_games(players, n):
    wins = {p: 0 for p in players}
    with ProcessPoolExecutor(max_workers=cpu_count()) as executor:
        for winner in executor.map(play_game, itertools.repeat(players, n)):
            wins[winner] += 1
    return wins

if __name__ == '__main__':
    players = {"Wrecking Ball": agents.wrecking_ball, "Random": agents.random_agent}
    print('Winner:', play_game(players))
