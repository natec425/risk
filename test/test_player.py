from unittest import TestCase

from risk import Player


class TestPlayer(TestCase):
    def test_eq(self):
        p1 = Player('a')
        p2 = Player('b')
        p3 = Player('a', ['some card'])

        self.assertNotEqual(p1, p2, 'p1 has a different name from p2')
        self.assertNotEqual(p1, p3, 'p1 doesn\'t have any cards, but p3 does')

        self.assertEqual(p1, Player('a'), 'Players with equal attribute values are equal')
        self.assertEqual(p3, Player('a', ['some card']), 'Players with equal attribute values are equal')
        self.assertEqual(Player('foo', ['card'], 3),
                         Player('foo', ['card'], 3),
                         'Players with equal attribute values are equal')
        self.assertNotEqual(Player('foo', ['card'], 3),
                            Player('foo', ['card'], 2),
                            'Players with different attribute values are not equal')

    def test_repr(self):
        self.assertEqual(eval(repr(Player('a'))),
                         Player('a'))
        self.assertNotEqual(eval(repr(Player('a'))),
                            Player('b'))

        self.assertEqual(eval(repr(Player('a', ['card']))),
                         Player('a', ['card']))
        self.assertNotEqual(eval(repr(Player('a', ['card']))),
                            Player('a', ['card', 'card']))
        self.assertNotEqual(eval(repr(Player('a', ['card']))),
                            Player('a', ['not card']))
        self.assertNotEqual(eval(repr(Player('a', ['card']))),
                            Player('b', ['card']))

        self.assertEqual(eval(repr(Player('a', ['card'], 4))),
                         Player('a', ['card'], 4))
        self.assertNotEqual(eval(repr(Player('a', ['card'], 4))),
                            Player('b', ['card'], 4))
        self.assertNotEqual(eval(repr(Player('a', ['card'], 4))),
                            Player('a', ['card'], 3))
