"""This module contains all the logic required to represent and
manipulate a game of risk.

There are two major points of interest in this module, the new_game
function and the State class. The new_game function can be used to
create a fresh State. Once you have a State object, its methods
should be all you need. Most users shouldn't need to access anything
else in the module.

Available Classes:
    - State: state of the entire game
    - Board: state of the board
    - Territory: state of a territory
    - Continent: state of a continent
    - Player: state of a player

Available Functions:
    - new_game: constructs a fresh game state.
"""
import itertools
import json
from copy import deepcopy
from collections import namedtuple
from enum import Enum
import os
import random
from abc import ABCMeta, abstractmethod

import util

TERRITORIES_FILE = os.path.join(os.path.dirname(__file__), 'territories.json')
CONTINENTS_FILE = os.path.join(os.path.dirname(__file__), 'continents.json')


class State(metaclass=ABCMeta):
    @abstractmethod
    def available_actions(self):
        ...

    @abstractmethod
    def transition(self, action):
        ...

    @abstractmethod
    def is_terminal(self):
        ...


class RiskState(State):
    def __init__(self, board, players, current_player_i=0, card_turnins=0):
        if len(players) < 1:
            raise ValueError('At least 1 player is needed.')
        if current_player_i >= len(players):
            raise IndexError('current_player_i must be <= len(players)')

        self.board = board

        if all(isinstance(p, Player) for p in players):
            self.players = players
        elif all(isinstance(p, str) for p in players):
            initial_reinforcements = 40 - (5 * (len(players) - 2))
            self.players = [
                Player(name, reinforcements=initial_reinforcements)
                for name in players
            ]
        else:
            raise ValueError(
                'Argument to players must either be a list of names of Player objects.'
            )

        self.current_player_i = current_player_i % len(players)
        self.card_turnins = card_turnins

    def reinforcements(self, player):
        """Returns the number of reinforcements currently owned by player.
        :type player: Player | str
        :rtype: int
        """
        if isinstance(player, Player):
            player = player.name

        for p in self.players:
            if p.name == player:
                return p.reinforcements
        raise KeyError('{} not in players'.format(player))

    @property
    def current_player(self):
        """Returns the current player.
        :rtype: Player
        """
        return self.players[self.current_player_i]

    @property
    def next_player(self):
        """Returns the player next in line for a turn.
        :rtype: Player
        """
        return self.players[(self.current_player_i + 1) % len(self.players)]

    @property
    def territories(self):
        return self.board.territories.values()

    @property
    def continents(self):
        return self.board.continents

    def troops(self, terr):
        """Returns the number of troops occupying the given territory.

        :type terr: Territory | str
        :rtype: int"""
        if isinstance(terr, Territory):
            terr = terr.name
        return self.board.troops(terr)

    def owner(self, terr):
        """Returns the owner of the given territory.

        Territories may not be occupied. If they are occupied, the
        player occupying the territory is returned, otherwise None
        is returned.

        :type terr: Territory | str
        :rtype: Player
        """
        if isinstance(terr, Territory):
            terr = terr.name
        return self.board.owner(terr)

    def territories_owned(self, player):
        """Returns an iterable of territories owned by the given player.

        :type player: Player | str
        :rtype: Iterable[Territory]"""
        if isinstance(player, Player):
            player = player.name
        return self.board.territories_owned(player)

    def continents_owned(self, player):
        """Returns an iterable of continents owned by the given player.

        :type player: Player | str
        :rtype: Iterable[Continents]"""
        if isinstance(player, Player):
            player = player.name
        return self.board.continents_owned(player)

    def neighbors(self, terr):
        """Returns an iterable of all territories neighboring terr.

        :type terr: Territory | str
        :rtype: Iterable[Territory]"""
        if isinstance(terr, Territory):
            terr = terr.name
        return self.board.neighbors(terr)

    def calculate_reinforcements(self, player):
        """Returns the number of expected reinforcements the given player will receive
        at the beginning of their next turn (assuming the board stays changed).

        :type player: Player | str
        :rtype: int
        """
        if isinstance(player, Player):
            player = player.name

        terr_contrib = len(list(self.territories_owned(player))) // 3
        cont_contrib = sum(c.bonus for c in self.continents_owned(player))
        return max(3, terr_contrib + cont_contrib)

    def copy(self):
        return deepcopy(self)

    def is_terminal(self):
        return False

    def __eq__(self, other):
        return (isinstance(other, self.__class__) and
                self.__dict__ == other.__dict__)

    def __str__(self):
        return "\n\t".join(str(terr) for terr in self.territories)

    def __repr__(self):
        return (str(self.__class__.__name__) + "(" + ",\n\t".join(
            k + "=" + repr(v) for k, v in self.__dict__.items()) + ")")


class PrePlaceState(RiskState):
    def available_actions(self):
        unoccupied_territories = list(t.name for t in self.territories
                                      if t.owner is None)

        def sample(n):
            for t in random.sample(unoccupied_territories, n):
                yield PrePlace(t)

        def _iter():
            for name in unoccupied_territories:
                yield PrePlace(name)

        return Actions(sample, _iter, len(unoccupied_territories))

    def transition(self, action):
        if not isinstance(action, PrePlace):
            raise ValueError(
                "PrePlaceState cannot process {!r}".format(action))

        if self.owner(action.territory) is not None:
            raise ValueError(
                '{!r} is already claimed.'.format(action.territory))

        self.board.territories[action.territory].owner = self.current_player
        self.board.territories[action.territory].troops += 1
        self.current_player.reinforcements -= 1

        if any(terr.owner is None for terr in self.territories):
            return PrePlaceState(
                self.board, self.players,
                (self.current_player_i + 1) % len(self.players),
                self.card_turnins)
        else:
            return PreAssignState(
                self.board, self.players,
                (self.current_player_i + 1) % len(self.players),
                self.card_turnins)


class PreAssignState(RiskState):
    def available_actions(self):
        owned_terrs = list(
            t.name for t in self.territories_owned(self.current_player))

        def sample(n):
            for t in random.sample(owned_terrs, n):
                yield PreAssign(t)

        def _iter():
            for name in owned_terrs:
                yield PreAssign(name)

        return Actions(sample, _iter, len(owned_terrs))

    def transition(self, action):
        if not isinstance(action, PreAssign):
            raise ValueError(
                "PreAssignState cannot process {!r}".format(action))

        if self.owner(action.territory).name != self.current_player.name:
            raise ValueError('Can only place troops on territories you own.')

        self.board.territories[action.territory].troops += 1
        self.current_player.reinforcements -= 1

        if any(pl.reinforcements != 0 for pl in self.players):
            return PreAssignState(
                self.board, self.players,
                (self.current_player_i + 1) % len(self.players),
                self.card_turnins)
        else:
            self.next_player.reinforcements += self.calculate_reinforcements(
                self.next_player)
            return PlaceState(self.board, self.players, 0, self.card_turnins)


class PlaceState(RiskState):
    def _action_space_len(self):
        num_territories = sum(
            1 for _ in self.territories_owned(self.current_player))
        num_reinforcements = self.reinforcements(self.current_player)

        return int(
            sum(
                util.choose(num_territories, n) * util.choose(
                    num_reinforcements - 1, n - 1)
                for n in range(1, min(num_territories, num_reinforcements))))

    def available_actions(self):
        territories_owned = list(self.territories_owned(self.current_player))
        reinforcements = self.reinforcements(self.current_player)
        max_n = min(len(territories_owned), reinforcements)

        def sample(n):
            actions = []
            while len(actions) < n:
                n = random.randint(1, max_n)
                combo_i = random.randint(
                    0, util.choose(len(territories_owned), n) - 1)
                alloc_i = random.randint(
                    0, util.choose(reinforcements - 1, n - 1) - 1)
                combo = util.kth_n_combination(territories_owned, n, combo_i)
                alloc = util.kth_n_integer_composition(reinforcements, n,
                                                       alloc_i)
                action = Place(combo, alloc)
                if action not in actions:
                    yield action
                    actions.append(action)

        def _iter():
            for n in range(1, max_n):
                for terrs in itertools.combinations(territories_owned, n):
                    for troops in util.integer_compositions(reinforcements, n):
                        yield Place(terrs, troops)

        return Actions(sample, _iter, self._action_space_len())

    def transition(self, action):
        if not isinstance(action, Place):
            raise ValueError("PlaceState cannot process {!r}".format(action))

        owned_terrs = [t for t in self.territories_owned(self.current_player)]
        if any(terr not in owned_terrs for terr in action.territories):
            raise ValueError(
                """You can only place troops on territories you own.
            Owned: {}
            Targets: {}""".format(
                    list(
                        map(str, self.territories_owned(self.current_player))),
                    action.territories))
        if sum(action.troops) != self.reinforcements(self.current_player):
            raise ValueError(
                "You must place exactly however many reinforcements you have.")
        if len(action.territories) != len(action.troops):
            raise ValueError(
                "You must provide an troop allocation for each territory.")

        for terr, troop in zip(action.territories, action.troops):
            self.board.territories[terr.name].troops += troop
            self.current_player.reinforcements -= troop

        return AttackState(self.board, self.players, self.current_player_i,
                           self.card_turnins)


class AttackState(RiskState):
    def __init__(self,
                 board,
                 players,
                 current_player_i=0,
                 card_turnins=0,
                 occupied=False):
        super().__init__(board, players, current_player_i, card_turnins)
        self.occupied = occupied

    def available_actions(self):
        actions = [
            Attack(owned.name, neighbor, troops)
            for owned in self.territories_owned(self.current_player)
            for neighbor in self.neighbors(owned)
            if self.owner(neighbor).name != self.current_player.name
            for troops in range(2, self.troops(owned))
        ] + [DontAttack()]

        def sample(n):
            yield from random.sample(actions, n)

        def _iter():
            return iter(actions)

        return Actions(sample, _iter, len(actions))

    def transition(self, action):
        attack = isinstance(action, Attack)
        dont_attack = isinstance(action, DontAttack)
        if not (attack or dont_attack):
            raise ValueError("AttackState cannot process {!r}".format(action))
        if attack:
            if action.from_territory not in (
                    t.name
                    for t in self.territories_owned(self.current_player)):
                raise ValueError(
                    "You can only attack from territories you own.")
            if action.to_territory in (
                    t.name
                    for t in self.territories_owned(self.current_player)):
                raise ValueError("You can't attack your own territories.")
            if action.to_territory not in self.neighbors(
                    action.from_territory):
                raise ValueError(
                    "You can only attack neighboring territories.")
            if action.troops < 2:
                raise ValueError("You can't attack with less than 2 troops.")

            attacker_rolls = iter(
                sorted(
                    (random.randint(1, 6) for _ in range(action.troops - 1)),
                    reverse=True))
            defender_rolls = iter(
                sorted(
                    (random.randint(1, 6)
                     for _ in range(self.troops(action.to_territory))),
                    reverse=True))

            for attacker_roll, defender_roll in zip(attacker_rolls,
                                                    defender_rolls):
                if attacker_roll > defender_roll:
                    self.board.territories[action.to_territory].troops -= 1
                else:
                    self.board.territories[action.from_territory].troops -= 1

            if self.troops(action.to_territory) == 0:
                if sum(1
                       for _ in self.territories_owned(
                           self.owner(action.to_territory))) == 0:
                    self.current_player.cards.extend(
                        self.owner(action.to_territory).cards)
                remaining_troops = len(list(attacker_rolls)) + 1
                self.board.territories[
                    action.to_territory].owner = self.current_player
                self.board.territories[
                    action.to_territory].troops = remaining_troops
                self.board.territories[
                    action.from_territory].troops -= remaining_troops
                self.occupied = True

            if all(t.owner == self.current_player for t in self.territories):
                return TerminalState(self.board, [self.current_player], 0,
                                     self.card_turnins)
            return AttackState(self.board, [
                p for p in self.players
                if any(t.owner == p for t in self.territories)
            ], self.current_player_i, self.card_turnins, self.occupied)
        else:
            if self.occupied:
                self.current_player.cards.append(Cards.new_card())
            return FortifyState(self.board, self.players,
                                self.current_player_i, self.card_turnins)


class FortifyState(RiskState):
    def available_actions(self):
        terrs_owned = set(self.territories_owned(self.current_player))
        actions = [
            Fortify(source.name, dest, n)
            for source in terrs_owned for dest in self.neighbors(source)
            if dest in terrs_owned for n in range(1, self.troops(source) - 1)
        ] + [DontFortify()]

        def sample(n):
            yield from random.sample(actions, n)

        def _iter():
            return iter(actions)

        return Actions(sample, _iter, len(actions))

    def transition(self, action):
        fortify = isinstance(action, Fortify)
        dont_fortify = isinstance(action, DontFortify)
        if not (fortify or dont_fortify):
            raise ValueError("FortifyState cannot process {!r}".format(action))
        if fortify:
            if (self.owner(action.from_territory) != self.current_player or
                    self.owner(action.to_territory) != self.current_player):
                raise ValueError(
                    "You can only fortify between territories you own.")
            if action.troops >= self.troops(action.from_territory):
                raise ValueError(
                    "You must leave at least 1 troop behind when fortifying.")

            self.board.territories[
                action.from_territory].troops -= action.troops
            self.board.territories[action.to_territory].troops += action.troops

        self.next_player.reinforcements += self.calculate_reinforcements(
            self.next_player)
        return PlaceState(self.board, self.players,
                          (self.current_player_i + 1) % len(self.players),
                          self.card_turnins)


class TerminalState(RiskState):
    def transition(self, action):
        raise NotImplemented

    def available_actions(self):
        yield

    def is_terminal(self):
        return True

    def winner(self):
        return self.current_player


class Board:
    """Represents the state of the board.

    Board objects are largely just a list of territories and a list
    of continents.

    :type territories: dict[str, Territory]
    :type continents: dict[str, Continent]
    """

    def __init__(self, territories, continents):
        self.territories = territories
        self.continents = continents

    def troops(self, terr):
        """Returns the number of troops at terr.

        :type terr: str
        :rtype: int
        """
        return self.territories[terr].troops

    def owner(self, terr):
        """Returns the Player that owns terr.

        :type terr: str
        :rtype: Player
        """
        return self.territories[terr].owner

    def territories_owned(self, player):
        """Returns an Iterable of all the territries owned by player

        :type player: str
        :rtype: Iterable[Territory]
        """
        return (terr for terr in self.territories.values()
                if terr.owner is not None and terr.owner.name == player)

    def continents_owned(self, player):
        """ Returns an Iterable of all the continents owned by player.

        :type player: str
        :rtype: Iterable[Continent]
        """
        return (c for c in self.continents.values()
                if c.owner is not None and c.owner.name == player)

    def neighbors(self, terr):
        """Returns an Iterable of the names of the territories that neighbor terr.

        :type terr: str
        :rtype: Iterable[str]
        """
        return self.territories[terr].neighbors

    def __eq__(self, other):
        try:
            return (self.territories == other.territories and
                    self.continents == other.continents)
        except AttributeError:
            return False

    def __repr__(self):
        return 'Board({b.territories!r},\n\t{b.continents!r})'.format(b=self)


class Territory:
    """Represents the state of a territory.

    Territory objects have a name, (possibly) an owner, and a number
    of occupying troops.

    :type name: str
    :type neighbors: Iterable[str]
    :type owner: Player
    :type troops: int
    """

    def __init__(self, name, neighbors, owner=None, troops=0):
        self.name = name
        self.neighbors = neighbors
        self.owner = owner
        self.troops = troops

    def __eq__(self, other):
        try:
            return (self.name == other.name and
                    self.neighbors == other.neighbors and
                    self.owner == other.owner and self.troops == other.troops)
        except AttributeError:
            return False

    def __hash__(self):
        return hash(self.name)

    def __str__(self):
        return "Territory({}, {}, {}, \n\t{})".format(
            self.name, self.owner, self.troops, self.neighbors)

    def __repr__(self):
        return ('Territory({t.name!r}, '
                '{t.neighbors!r}, '
                '{t.owner!r}, '
                '{t.troops!r})').format(t=self)


class Continent:
    """Represents the state of a continent.

    Continent objects have a name, (possibly) an owner, a collection
    of territories, and an ownership bonus.

    :type name: str
    :type territories: Iterable[Territory]
    :type bonus: int
    """

    def __init__(self, name, bonus, territories):
        self.name = name
        self.territories = territories
        self.bonus = bonus

    @property
    def owner(self):
        if len(set(t.owner for t in self.territories)) == 1:
            return next(iter(self.territories)).owner
        else:
            return None

    def __eq__(self, other):
        try:
            return (self.name == other.name and self.owner == other.owner and
                    self.territories == other.territories and
                    self.bonus == other.bonus)
        except AttributeError:
            return False

    def __repr__(self):
        return ('Continent({c.name!r}, '
                '{c.bonus!r}, '
                '{c.territories!r})').format(c=self)


class Player:
    """Represents the state of a player.

    Player objects are a name, a list of cards.
    """

    def __init__(self, name, cards=None, reinforcements=0):
        self.name = name
        self.reinforcements = reinforcements
        self.cards = cards or []

    def __hash__(self):
        return hash(self.name)

    def __eq__(self, other):
        try:
            return (self.name == other.name and self.cards == other.cards and
                    self.reinforcements == other.reinforcements)
        except AttributeError:
            return False

    def __repr__(self):
        return ('Player({p.name!r}, '
                '{p.cards!r}, '
                '{p.reinforcements!r})').format(p=self)


# Moves
PrePlace = namedtuple('PrePlace', ['territory'])
PreAssign = namedtuple('PreAssign', ['territory'])
Place = namedtuple('Place', ['territories', 'troops'])
Attack = namedtuple('Attack', ['from_territory', 'to_territory', 'troops'])
DontAttack = namedtuple('DontAttack', [])
Fortify = namedtuple('Fortify', ['from_territory', 'to_territory', 'troops'])
DontFortify = namedtuple('DontFortify', [])
TurnInCards = namedtuple('TurnInCards', [])


class Actions:
    def __init__(
            self,
            sample,
            iter,
            length, ):
        self.sample = sample
        self.iter = iter
        self.length = length

    def __iter__(self):
        return self.iter()

    def sample(self, n):
        yield from self.sample(n)

    def __len__(self):
        return self.length


# Cards
class Cards(Enum):
    Infantry, Cavalry, Artillery = range(3)

    @classmethod
    def new_card(cls):
        return random.choice(list(cls))


def _load_territories(file_name):
    with open(file_name) as handle:
        territories = {
            name: Territory(name, set(neighbors))
            for name, neighbors in json.load(handle).items()
        }
    return territories


def _load_continents(file_name, territories):
    continents = {}
    with open(file_name) as handle:
        for cont in json.load(handle):
            cont_terrs = {territories[t] for t in cont['territories']}
            continents[cont['name']] = Continent(cont['name'], cont['bonus'],
                                                 cont_terrs)
    return continents


def new_game(players):
    """Returns a fresh game State to start a game from."""
    territories = _load_territories(TERRITORIES_FILE)
    continents = _load_continents(CONTINENTS_FILE, territories)
    board = Board(territories, continents)
    return PrePlaceState(board, players)
