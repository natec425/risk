import unittest

from risk import *


class TestRisk(unittest.TestCase):
    def assertIsOneOf(self, obj, *types):
        if not any(isinstance(obj, t) for t in types):
            self.fail("{} is not an instance of any of the following types: {}".format(obj, types))

    def test_too_few_players(self):
        with self.assertRaises(ValueError):
            new_game([])

    def test_invalid_current_player_i(self):
        state = new_game(['foo'])
        state.players = state.players[1:]
        with self.assertRaises(ValueError):
            eval(repr(state))

    def test_invalid_players_arg(self):
        with self.assertRaises(ValueError):
            new_game(["foo", Player("bar")])

        with self.assertRaises(ValueError):
            new_game(["foo", 1])

        with self.assertRaises(ValueError):
            new_game([1])

    def test_two_player_new_game(self):
        state = new_game(["Nate", "Chris"])

        self.assertEqual(eval(repr(state)), state)

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

        state = state.transition(PrePlace("Alaska"))

        self.assertEqual("Chris", state.current_player.name)
        self.assertEqual("Nate", state.next_player.name)

        for i in range(41, 0, -1):
            self.assertIsInstance(state, PrePlaceState)
            self.assertEqual(i, len(list(state.available_actions())))
            state = state.transition(next(iter(state.available_actions())))

        for t in state.territories:
            self.assertEqual(1, state.troops(t))

        self.assertIsInstance(state, PreAssignState)
        for p in state.players:
            self.assertEqual(19, state.reinforcements(p))

        for i in range(19):
            state = state.transition(next(iter(state.available_actions())))
            state = state.transition(next(iter(state.available_actions())))

        self.assertIsInstance(state, PlaceState)
        self.assertEqual("Nate", state.current_player.name)
        self.assertEqual(state.calculate_reinforcements("Nate"), state.reinforcements("Nate"))
        self.assertEqual("Chris", state.next_player.name)
        self.assertEqual(0, state.reinforcements("Chris"))

        state = state.transition(next(iter(state.available_actions())))

        self.assertIsInstance(state, AttackState)
        self.assertEqual("Nate", state.current_player.name)
        self.assertEqual(0, state.reinforcements("Nate"))

        for action in state.available_actions():
            self.assertIsOneOf(action, Attack, DontAttack)
            if isinstance(action, Attack):
                self.assertIn(action.from_territory,
                              (t.name for t in state.territories_owned(state.current_player)))
                self.assertNotIn(action.to_territory,
                                 (t.name for t in state.territories_owned(state.current_player)))

        state = state.transition(next(a
                                      for a in state.available_actions()
                                      if isinstance(a, Attack)))
        self.assertEqual("Nate", state.current_player.name)
        self.assertIsInstance(state, AttackState)
        state = state.transition(DontAttack())

        self.assertEqual("Nate", state.current_player.name)
        self.assertIsInstance(state, FortifyState)
