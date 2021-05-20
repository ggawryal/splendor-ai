from os.path import abspath
import warnings
warnings.filterwarnings("ignore", message="numpy.dtype size changed")
warnings.filterwarnings("ignore", message="numpy.ufunc size changed")

import os
import pandas as pd
from copy import deepcopy
from environment import config


"""
actions: pick 1 token
return 1 token
buy card
no gold tokens
no nobles
"""

class MiniSplendor:
    def __init__(self):
        self.load_cards()
        self.reset()
        self.avaliable_actions = ['buy', 'pick', 'return']
        self.COLORS = ['green', 'white', 'blue', 'black', 'red']

    def reset(self, return_state=True):
        self.end = False
        self.return_tokens = False
        self.set_cards()
        self.create_players()
        self.place_tokens()
        self.winner = 0.5
        
        if return_state:
            return self.return_state()

    def return_state(self, shift=True):
        # Shift players so that player thats next to move will be first in list
        if shift:
            shifted_players = self.players[self.current_player:] + self.players[:self.current_player]
        else:
            shifted_players = deepcopy(self.players)

        shown_tier1 = self.tier1[-min(4, len(self.tier1)):]
        shown_tier2 = self.tier2[-min(4, len(self.tier2)):]
        shown_tier3 = self.tier3[-min(4, len(self.tier3)):]

        game = {
            'players': shifted_players,
            'tokens': self.tokens.copy(),
            'tier1': shown_tier1,
            'tier2': shown_tier2,
            'tier3': shown_tier3,
            'hidden_t1': len(self.tier1) - len(shown_tier1),
            'hidden_t2': len(self.tier2) - len(shown_tier2),
            'hidden_t3': len(self.tier3) - len(shown_tier3),
            'nobles': None,
            'player_index': self.current_player,
            'return_tokens': self.return_tokens,
            'end': self.end
        }

        return game
    
    def copy(self):
        cp = MiniSplendor()
        cp.players = deepcopy(self.players)
        cp.tier1 = deepcopy(self.tier1)
        cp.tier2 = deepcopy(self.tier2)
        cp.tier3 = deepcopy(self.tier3)
        cp.tokens = self.tokens.copy()
        cp.end = self.end
        cp.return_tokens = self.return_tokens
        cp.current_player = self.current_player
        cp.winner = self.winner
        return cp

    def move(self, move):
        action = list(move.keys())

        if len(action) != 1:
            assert False, 'move dict requires exactly one key'

        action = action[0]
        if action not in self.avaliable_actions:
            assert False, 'invalid action, avaliable actions: ' + str(self.avaliable_actions)

        if self.return_tokens and action != 'return':
            assert False, 'invalid action, when you have more than 10 tokens you can only return them'

        if action == 'buy':
            requested_card = move[action]
            if not self.can_afford(requested_card):
                assert False, 'invalid action you can\'t buy this card'

            self.buy(requested_card)

        elif action == 'pick':
            requested_tokens = move[action]
            if not self.can_pick(requested_tokens):
                assert False, 'invalid action you can\'t pick this tokens'

            self.pick(requested_tokens)

        elif action == 'reserve':
            assert False, 'invalid action you can\'t reserve in minisplendor'

        elif action == 'return':
            returning_tokens = move[action]
            if not self.can_return(returning_tokens):
                assert False, 'invalid action you can\'t return this tokens'

            self.do_return_tokens(returning_tokens)

        else:
            assert False, 'invalied action, avaliable actions: ' + str(self.avaliable_actions)

        if self.current_player == (config.PLAYERS-1):
            self.check_winners()

        if not self.return_tokens:
            self.current_player = (self.current_player + 1) % config.PLAYERS

        return self.return_state()

    def can_return(self, returning_tokens):
        returning_amount = sum(returning_tokens.values())
        if returning_amount != 1:
            return False 
        tokens = self.players[self.current_player]['tokens']
        current_amount = sum(tokens.values())
        if current_amount - returning_amount > 10:
            return False

        if any(tokens[i] < returning_tokens[i] for i in returning_tokens):
            return False

        return True

    def do_return_tokens(self, requested_tokens):
        for color in requested_tokens:
            self.players[self.current_player]['tokens'][color] -= requested_tokens[color]
            self.tokens[color] += requested_tokens[color]

        self.return_tokens = False

    def remove_card(self, card):
        if int(card['tier']) == 1:
            self.tier1 = self.tier1.drop(card.name)

        elif int(card['tier']) == 2:
            self.tier2 = self.tier2.drop(card.name)

        elif int(card['tier']) == 3:
            self.tier3 = self.tier3.drop(card.name)

        else:
            assert False, 'invalid tier'

    def card_to_colors(self, card):
        # Returns neccesary tokens for this card separated by comas
        return ','.join(str(int(card[c])) for c in self.COLORS)

    def can_reserve(self, card):
        return False

    def show_cards(self):
        # Returns string versions of all visible cards on board
        shown_tier1 = self.tier1[-min(4, len(self.tier1)):].reset_index(drop=True)
        shown_tier2 = self.tier2[-min(4, len(self.tier2)):].reset_index(drop=True)
        shown_tier3 = self.tier3[-min(4, len(self.tier3)):].reset_index(drop=True)

        str_tier1 = [self.card_to_colors(shown_tier1.iloc[i]) for i in range(len(shown_tier1))]
        str_tier2 = [self.card_to_colors(shown_tier2.iloc[i]) for i in range(len(shown_tier2))]
        str_tier3 = [self.card_to_colors(shown_tier3.iloc[i]) for i in range(len(shown_tier3))]

        return str_tier1 + str_tier2 + str_tier3

    def can_afford(self, card):
        # Current player assets
        tokens = self.players[self.current_player]['tokens']
        cards = self.players[self.current_player]['cards']

        # Tokens needed to buy this card by current player
        token_diff = [tokens[i] + cards[i] - card[i] for i in self.COLORS]
        missing_tokens = abs(sum(i for i in token_diff if i < 0))
        if missing_tokens > 0:
            return False
        return True

    def buy(self, card):
        # If player is buying card from board remove it
        self.remove_card(card)

        for color in self.COLORS:
            # Amount of this player's cards of certain color
            this_cards = self.players[self.current_player]['cards'][color]

            # If player doesnt have more cards of this color than needed
            if int(card[color]) > this_cards:

                # Subtract missing tokens of this color from player and put it back on the board
                necessary_tokens = int(card[color]) - this_cards
                self.players[self.current_player]['tokens'][color] -= necessary_tokens
                self.tokens[color] += necessary_tokens

                # Player tokens of this color after purchase
                this_tokens = self.players[self.current_player]['tokens'][color]
                
                assert this_tokens >= 0

        # Add card power (color) to player arsenal and card value to player score
        card_color = self.COLORS[int(card['type'])-1]
        self.players[self.current_player]['cards'][card_color] += 1
        self.players[self.current_player]['score'] += int(card['value'])

    def can_pick(self, tokens):
        # Unindexed amouns of certain tokens to pick
        values = tokens.values()

        # Amount of all picked tokens needs to be between 0 and 1
        if not 0 <= sum(values) <= 1:
            return False

        # Player can not pick more tokens than there is on board
        for color in tokens:
            if self.tokens[color] < tokens[color]:
                return False

        return True

    def pick(self, tokens):
        for color in tokens:
            self.players[self.current_player]['tokens'][color] += tokens[color]
            self.tokens[color] -= tokens[color]

        # If player have too many tokens he has to return excess in next move
        player_tokens = self.players[self.current_player]['tokens'].values()
        if sum(player_tokens) > config.MAXIMUM_TOKENS:
            self.return_tokens = True

    def check_winners(self):
        for i, player in enumerate(self.players):
            if player['score'] >= config.WINNING_SCORE:
                self.end = True
                self.winner = i

    def load_cards(self):
        abspath = os.path.dirname(__file__)
        if not os.path.isfile(os.path.join(abspath, 'cards.csv')):
            assert False, 'cards.csv file does not exist'

        self.primary_cards = pd.read_csv(os.path.join(abspath,'cards.csv'))

    def place_tokens(self):
        self.tokens = {
            'green': config.NOT_GOLD,
            'white': config.NOT_GOLD,
            'blue': config.NOT_GOLD,
            'black': config.NOT_GOLD,
            'red': config.NOT_GOLD,
            'gold': 0
        }

    def set_cards(self):
        # Don't shuffle cards
        shuffled_cards = self.primary_cards.copy()

        # Organize cards in relation to their tier
        t1_idx = shuffled_cards['tier'] == 1
        t2_idx = shuffled_cards['tier'] == 2
        t3_idx = shuffled_cards['tier'] == 3
        self.tier1 = shuffled_cards.loc[t1_idx].reset_index(drop=True)
        self.tier2 = shuffled_cards.loc[t2_idx].reset_index(drop=True)
        self.tier3 = shuffled_cards.loc[t3_idx].reset_index(drop=True)

    def create_players(self):
        # The player's index, which will move next
        self.current_player = 0

        primary_player = {
            'score': 0,
            'tokens': {
                'green': 0,
                'white': 0,
                'blue': 0,
                'black': 0,
                'red': 0,
                'gold': 0
            },
            'cards': {
                'green': 0,
                'white': 0,
                'blue': 0,
                'black': 0,
                'red': 0
            },
            'reservations': []
        }

        self.players = [deepcopy(primary_player) for _ in range(2)]

if __name__ == '__main__':
    env = MiniSplendor()