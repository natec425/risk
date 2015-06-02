import random
import sys
import time

from risk import new_game, PlaceState

if __name__ == '__main__':
    state = new_game(['Bot1', 'Bot2'])
    while not state.is_terminal():
        if isinstance(state, PlaceState):
            print('Number of Territories owned: ', len(list(state.territories_owned(state.current_player))))
            print('Number of Continents owned: ', len(list(state.continents_owned(state.current_player))))
            print('Number of Reinforcements: ', state.reinforcements(state.current_player))
            start = time.time()
            count = 0
            for a in state.available_actions():
                count += 1
            print('Time to generate all actions: ', time.time() - start)
            print('Number of actions: ', count)
            sys.exit()
        else:
            print(state.__class__)
            choice = random.choice(state.available_actions())
            state = state.transition(choice)
