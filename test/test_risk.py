from unittest import TestCase

from risk import *


class TestRisk(TestCase):
    def test_two_player_new_game(self):
        state = new_game(["Nate", "Chris"])

        self.assertEqual(eval(repr(state)), state)
        self.assertFalse(state.is_terminal())
        self.assertEqual("PrePlace", state.turn_type)

        for p in state.players:
            self.assertIsInstance(p, Player, "The state should always store Player objects")
            self.assertEqual(40, state.reinforcements(p), "Two player games should start with 40 troops/player.")
            self.assertListEqual([], list(state.territories_owned(p)))
            self.assertListEqual([], list(state.continents_owned(p)))
            self.assertEqual(3, state.calculate_reinforcements(p))

        self.assertEqual("Nate", state.current_player.name)
        self.assertEqual("Chris", state.next_player.name)

    def test_two_player(self):
        state = new_game(["Nate", "Chris"])

        for action in state.available_actions():
            self.assertIsInstance(action, PrePlace, "Players should only be able to PrePlace at this point")
        self.assertEqual(42, len(list(state.available_actions())), "There should be one PrePlace action per territory")

        self.assertEqual("Nate", state.current_player.name)
        self.assertIn(PrePlace("Alaska"), state.available_actions())

        state.transition(PrePlace("Alaska"))

        self.assertEqual("Chris", state.current_player.name)
        self.assertEqual("Nate", state.next_player.name)

        for i in range(41, 0, -1):
            self.assertEqual("PrePlace", state.turn_type)
            self.assertEqual(i, len(list(state.available_actions())))
            state.transition(next(state.available_actions()))

        self.assertEqual("PreAssign", state.turn_type)
        for p in state.players:
            self.assertEqual(19, state.reinforcements(p))

        for i in range(19):
            state.transition(next(state.available_actions()))
            state.transition(next(state.available_actions()))

        self.assertEqual("Place", state.turn_type)
        self.assertEqual("Nate", state.current_player.name)
        self.assertEqual(state.calculate_reinforcements("Nate"), state.reinforcements("Nate"))
        self.assertEqual("Chris", state.next_player.name)
        self.assertEqual(0, state.reinforcements("Chris"))

        state.transition(next(state.available_actions()))

        self.assertEqual("Attack", state.turn_type)
        self.assertEqual("Nate", state.current_player)