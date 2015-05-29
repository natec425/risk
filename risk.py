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

TERRITORIES_FILE = 'territories.json'
CONTINENTS_FILE = 'continents.json'


class State:
    """Represents a given state in the boardgame Risk.

    :type board: Board
    :type players: list[Player] | list[str]
    :type turn_type: str
    :type current_player_i: int
    :type card_turnins: int"""
    # .cards : [Cards]                 The deck of cards
    # .last_attacker : terr_id         Last territory to attack from
    # .last_defender : terr_id         Last territory to be attacked
    def __init__(self, board, players, turn_type,
                 current_player_i=0, card_turnins=0):
        if len(players) < 1:
            raise ValueError('At least 1 player is needed.')
        if current_player_i >= len(players):
            raise IndexError('current_player_i must be <= len(players)')

        self.board = board

        if all(isinstance(p, Player) for p in players):
            self.players = players
        elif all(isinstance(p, str) for p in players):
            initial_reinforcements = 40 - (5 * (len(players) - 2))
            self.players = [Player(name, reinforcements=initial_reinforcements)
                            for name in players]
        else:
            raise ValueError('Argument to players must either be a list of names of Player objects.')

        self._current_player_i = current_player_i
        self.card_turnins = card_turnins
        self.turn_type = turn_type

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
        return self.players[self._current_player_i]

    @property
    def next_player(self):
        """Returns the player next in line for a turn.
        :rtype: Player
        """
        return self.players[(self._current_player_i + 1) % len(self.players)]

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

    def available_actions(self):
        """Returns all actions available from the current state.

        :rtype: Iterable[Action]"""
        # TODO
        if self.turn_type == 'PrePlace':
            return (PrePlace(t.name)
                    for t in self.board.territories.values()
                    if t.owner is None)
        elif self.turn_type == 'PreAssign':
            return (PreAssign(terr.name)
                    for terr in self.territories_owned(self.current_player.name))
        elif self.turn_type == 'Place':
            return self._place_actions(self.current_player)
        else:
            raise ValueError("I don't know how to handle that action.")

    def _place_actions(self, player):
        """Helper method that generates all possible actions a player can take during their
        "Place" phase.

        :type player: Player
        :rtype: Iterable[Action]
        """
        territories_owned = [t.name for t in self.territories_owned(player.name)]
        return (Place(terrs, troops)
                for n in range(1, len(territories_owned))
                for terrs in itertools.combinations(territories_owned, n)
                for troops in integer_partitions(self.reinforcements(player.name), n))

    def transition(self, action):
        """Mutates the current state to be the resulting state from applying
        the provided action.

        :type action: Action"""
        # TODO
        if self.turn_type == 'PrePlace':
            self._preplace(self.current_player, action.territory)
        elif self.turn_type == 'PreAssign':
            self._preassign(self.current_player, action.territory)
        elif self.turn_type == 'Place':
            pass
        else:
            raise ValueError("I don't know how to handle that action.")

    def _advance_player(self):
        self._current_player_i = (self._current_player_i + 1) % len(self.players)

    def _advance_turn_type(self):
        if self.turn_type == 'PrePlace':
            if all(t.owner is not None for t in self.board.territories.values()):
                self.turn_type = 'PreAssign'
            return

        if self.turn_type == 'PreAssign':
            if all(p.reinforcements == 0 for p in self.players):
                self._current_player_i = -1
                self.turn_type = 'Place'

        if self.turn_type == 'Place':
            self.next_player.reinforcements += self.calculate_reinforcements(self.next_player)

    def _preplace(self, player, terr):
        """
        :type player: Player
        :type terr: str
        """
        if self.owner(terr) is not None:
            raise ValueError('{} is already claimed.'.format(terr))

        self.board.territories[terr].owner = player
        self.board.territories[terr].troops += 1
        player.reinforcements -= 1

        self._advance_turn_type()
        self._advance_player()

    def _preassign(self, player, terr):
        """
        :type player: Player
        :type terr: str
        """
        if self.owner(terr).name != player.name:
            raise ValueError('Can only place troops on territories you own.')

        self.board.territories[terr].troops += 1
        player.reinforcements -= 1

        self._advance_turn_type()
        self._advance_player()

    def is_terminal(self):
        """Return True if the State is an end game state.
        :rtype: bool
        """
        return len(self.players) == 1

    def copy(self):
        """Returns a deepcopy of the state.

        :rtype: State
        """
        return deepcopy(self)

    def __eq__(self, other):
        try:
            # noinspection PyProtectedMember
            return (self.board == other.board and
                    self.players == other.players and
                    self._current_player_i == other._current_player_i and
                    self.card_turnins == other.card_turnins and
                    self.turn_type == other.turn_type)
        except AttributeError:
            return False

    def __repr__(self):
        return ('State({s.board!r},'
                '\n\t{s.players!r},'
                '\n\t{s.turn_type!r},'
                '\n\t{s._current_player_i!r},'
                '\n\t{s.card_turnins!r})').format(s=self)


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
        return (terr
                for terr in self.territories.values()
                if terr.owner is not None and terr.owner.name == player)

    def continents_owned(self, player):
        """ Returns an Iterable of all the continents owned by player.

        :type player: str
        :rtype: Iterable[Continent]
        """
        return (c
                for c in self.continents.values()
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
                    self.owner == other.owner and
                    self.troops == other.troops)
        except AttributeError:
            return False

    def __hash__(self):
        return hash(self.name)

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
            return (self.name == other.name and
                    self.owner == other.owner and
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
            return (self.name == other.name and
                    self.cards == other.cards)
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


def integer_partitions(total, n):
    """Generates all positive integer n-tuples that sum to total"""
    if total == 0 or n == 0:
        yield
    elif n == 1:
        yield total,
    else:
        for i in range(1, total):
            for sub_partition in integer_partitions(total-i, n-1):
                yield (i,) + sub_partition


def _load_territories(file_name):
    with open(file_name) as handle:
        territories = {name: Territory(name, set(neighbors))
                       for name, neighbors in json.load(handle).items()}
    return territories


def _load_continents(file_name, territories):
    continents = {}
    with open(file_name) as handle:
        for cont in json.load(handle):
            cont_terrs = {territories[t] for t in cont['territories']}
            continents[cont['name']] = Continent(cont['name'],
                                                 cont['bonus'],
                                                 cont_terrs)
    return continents


def new_game(players=None):
    """Returns a fresh game State to start a game from."""
    territories = _load_territories(TERRITORIES_FILE)
    continents = _load_continents(CONTINENTS_FILE, territories)
    board = Board(territories, continents)
    return State(board, players or [], 'PrePlace')


if __name__ == '__main__':
    players = ['Nate', 'Chris', 'Josh', 'Ben']
    state = new_game(players)

    assert eval(repr(state)) == new_game(players)

    assert state.current_player.name == 'Nate', state.current_player.name

    for p in players:
        assert state.reinforcements(p) == 30, state.reinforcements(p)

    assert PrePlace('Alaska') in state.available_actions(), state.available_actions()
    state.transition(PrePlace('Alaska'))
    assert state.owner('Alaska').name == 'Nate'
    assert 'Alaska' in [t.name for t in state.territories_owned('Nate')]
    assert 'Alaska' not in [t.name for t in state.territories_owned('Chris')]
    assert state.reinforcements('Nate') == 29

    assert state.turn_type == 'PrePlace'
    assert state.current_player.name == 'Chris'
    assert PrePlace('Alaska') not in state.available_actions()
    assert len(list(state.available_actions())) == 41

    try:
        state.transition(PrePlace('Alaska'))
    except ValueError:
        pass
    else:
        print('ValueError not raised for invalid Alaska Claim')

    state.transition(PrePlace('Ontario'))

    assert state.owner('Ontario').name == 'Chris'
    assert 'Ontario' in [t.name for t in state.territories_owned('Chris')]
    assert 'Ontario' not in [t.name for t in state.territories_owned('Nate')]
    assert state.reinforcements('Nate') == 29
    assert state.reinforcements('Chris') == 29

    assert state.turn_type == 'PrePlace'
    assert state.current_player.name == 'Josh'
    assert PrePlace('Ontario') not in state.available_actions()
    assert PrePlace('Alaska') not in state.available_actions()

    state.transition(next(state.available_actions()))
    state.transition(next(state.available_actions()))

    assert state.turn_type == 'PrePlace'
    assert state.current_player.name == 'Nate'

    i = 0
    while state.turn_type == 'PrePlace':
        i += 1
        state.transition(next(state.available_actions()))
    assert state.turn_type == 'PreAssign'
    assert i == 38

    assert len(list(state.territories_owned('Nate'))) == 11
    assert len(list(state.territories_owned('Chris'))) == 11
    assert len(list(state.territories_owned('Josh'))) == 10
    assert len(list(state.territories_owned('Ben'))) == 10

    assert state.reinforcements('Nate') == 19
    assert state.reinforcements('Chris') == 19
    assert state.reinforcements('Josh') == 20
    assert state.reinforcements('Ben') == 20

    assert state.current_player.name == 'Josh'

    i = 0
    while state.turn_type == 'PreAssign':
        i += 1
        state.transition(next(state.available_actions()))

    assert i == 78, i
    assert state.turn_type == 'Place'

    print([t.name for t in state.territories_owned(state.current_player.name)])
    i = 0
    for a in state.available_actions():
        i += 1
        print(a)
    print(i)
