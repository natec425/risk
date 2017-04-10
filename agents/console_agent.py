from risk import *
import blessed
from tabulate import tabulate
from typing import List
import sys

terminal = blessed.Terminal()

def show_current_player(current_player: Player) -> str:
    return '\n'.join([
        f"Current player: {current_player.name}",
        f"Reinforcements: {current_player.reinforcements}",
        f"Cards: {current_player.cards}"])

def show_current_phase(state: RiskState) -> str:
    return f"Current Phase: {state.__class__.__name__}"

def show_current_board(state: RiskState) -> str:
    board = state.board

    def color(t):
        return terminal.green(t) if state.owner(t) == state.current_player else terminal.red(t)

    def territory_line(t: str) -> List[str]:
        return [t,
            f"{board.owner(t).name if board.owner(t) else 'None'} ({board.troops(t)})",
            f"Neighbors: {', '.join(color(n) for n in board.neighbors(t))}"
        ]

    def show_owners_territories(owner: str) -> str:
        return tabulate([territory_line(t.name) for t in sorted(state.territories_owned(owner), key=lambda t: t.name)])

    return '\n\n'.join([show_owners_territories(owner) for owner in state.players])

def show_game_state(state: RiskState) -> str:
    return '\n'.join([
        show_current_player(state.current_player),
        '',
        show_current_phase(state),
        show_current_board(state)
    ])

def get_action(state: RiskState) -> Move:
    if isinstance(state, PreAssignState) or isinstance(state, PrePlaceState):
        return next(state.available_actions().sample(1))
    while True:
        try:
            return eval(input("What would you like to do: "))
        except KeyboardInterrupt:
            print()
            sys.exit()
        except Exception as e:
            print("Invalid Input")
            print(e)

def strategy(state: RiskState):
    print(show_game_state(state))
    return get_action(state)

