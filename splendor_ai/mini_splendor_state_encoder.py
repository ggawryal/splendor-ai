import numpy as np
from environment import config

class MiniSplendorStateEncoder:
    def __init__(self):
        self.COLORS = ['green', 'white', 'blue', 'black', 'red']
        self.output_nodes = 5+5+12
        self.pick_tokens = [
            {'green':1,'white':0,'blue':0,'black':0,'red':0},
            {'green':0,'white':1,'blue':0,'black':0,'red':0},
            {'green':0,'white':0,'blue':1,'black':0,'red':0},
            {'green':0,'white':0,'blue':0,'black':1,'red':0},
            {'green':0,'white':0,'blue':0,'black':0,'red':1},
        ]
        self.input_nodes = 157
    
    def output_to_move(self, move_id, state):
        if move_id < 10:
            for action_name in ('pick','return'):
                if move_id < 5:
                    tokens = self.pick_tokens[move_id]
                    return {action_name: tokens}
                move_id -= 5

        move_id -= 10
        tier, card_pos = (move_id//4)+1, move_id%4
        return {'buy': state['tier'+str(tier)].iloc[card_pos]}

    def available_outputs(self, env):
        if env.return_tokens:
            return self.available_outputs_when_returning(env)
        return self.available_outputs_when_normal_move(env)
    
    def available_outputs_when_normal_move(self, env):
        mask = [0]*self.output_nodes
        for i,color in enumerate(self.COLORS):
            if env.tokens[color] >= 1:
                mask[i] = 1
        
       
        state = env.return_state()

        offset = 10
        for tier in (1,2,3):
            for card in range(4):
                if card < len(state['tier'+str(tier)]) and env.can_afford(state['tier'+str(tier)].iloc[card]):
                    mask[offset] = 1
                offset += 1

        assert sum(mask) > 0
        return np.array(mask)
                    
    def available_outputs_when_returning(self, env):
        mask = [0]*self.output_nodes

        player_tokens = env.players[env.current_player]['tokens']
        for i,color in enumerate(self.COLORS):
            if player_tokens[color] >= 1:
                mask[5+i] = 1
        return np.array(mask)
    
    def state_to_vector(self, state):
        return tuple([state['player_index']] + self.encode_player(state['players'][0]) + self.encode_player(state['players'][1]) + self.encode_tokens(state['tokens']) +self.encode_tiers(state))

    def encode_player(self, player):
        v = [player['score']] 
        v += list(player['tokens'].values())
        v += list(player['cards'].values())
        for i in range(config.MAXIMUM_RESERVATIONS):
            if i < len(player['reservations']):
                v += self.encode_card(player['reservations'][i].iloc[0])
            else:
                v += self.encode_card(None)
        return v

    def encode_card(self, card):
        if card is None:
            return [0]*(2+len(self.COLORS))
        v = [card.value, card.type]
        for color in self.COLORS:
            v += [card[color]]
        return v
    
    def encode_tiers(self,state):
        v = []
        for tier in [3,2,1]:
            for card_pos in range(4):
                card = state['tier'+str(tier)].iloc[card_pos] if card_pos < len(state['tier'+str(tier)]) else None
                v += self.encode_card(card)
        return v

    def encode_tokens(self,tokens):
        return list(tokens.values())
