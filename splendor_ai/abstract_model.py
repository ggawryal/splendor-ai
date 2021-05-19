import itertools as it
import numpy as np
from environment import config

class AbstractModel:
    def __init__(self):
        self.COLORS = ['green', 'white', 'blue', 'black', 'red']
        self.pick_tokens = {cnt : list(it.combinations(self.COLORS.copy(),cnt)) for cnt in [3,2,1]}
        self.pick_tokens['doubles'] = self.COLORS.copy()
        self.output_nodes = [
            sum(len(i) for i in self.pick_tokens.values()), #TOKEN PICKING
            sum(len(i) for i in self.pick_tokens.values()), #TOKEN RETURNING
            3 * 4 * 2, #BUYING AND RESERVING BOARD CARDS
            config.MAXIMUM_RESERVATIONS, #BUYING RESERVED CARDS
            1 #EMPTY MOVE (pick nothing)
        ]
        self.input_nodes = 157

    def get_scores_for_each_move(self,state): #abstract method, convert state using state_to_vector if needed
        pass

    def update_model_after_game(self, v):
        pass

    def combination_to_tokens(self, combination):
        to_pick = {c: 0 for c in self.COLORS}
        for color in combination:
            to_pick[color] += 1
        return to_pick

    def output_to_move(self, move_id, state):
        if move_id < self.output_nodes[0] + self.output_nodes[1]:
            for action_name in ('pick','return'):
                for cnt in [3,2,1]:
                    if move_id < len(self.pick_tokens[cnt]):
                        combination = self.pick_tokens[cnt][move_id]
                        tokens = self.combination_to_tokens(combination)
                        return {action_name: tokens}
                    move_id -= len(self.pick_tokens[cnt])

                if move_id < len(self.pick_tokens['doubles']):
                    tokens = {self.COLORS[move_id]: 2}
                    return {action_name: tokens}

                move_id -= len(self.pick_tokens['doubles'])
        move_id -= self.output_nodes[0] + self.output_nodes[1]

        for action_name in ('buy','reserve'):
            if move_id < 12:
                tier, card_pos = (move_id//4)+1, move_id%4
                return {action_name: state['tier'+str(tier)].iloc[card_pos]}
            move_id -= 12

        if move_id < config.MAXIMUM_RESERVATIONS:
            return {'buy': state['players'][0]['reservations'][move_id].iloc[0]}
        move_id -= config.MAXIMUM_RESERVATIONS

        if move_id == 0:
            return {'pick': {}}        
        else:
            assert False, 'invalid move: ' + str(move_id)

    def available_outputs(self, env):
        if env.return_tokens:
            return self.available_outputs_when_returning(env)
        return self.available_outputs_when_normal_move(env)
    
    def available_outputs_when_normal_move(self, env):
        mask = [0]*sum(self.output_nodes)
        offset = 0
        player_tokens = env.players[env.current_player]['tokens']
        for tokens_to_return in [3,2,1]:
            for combination in self.pick_tokens[tokens_to_return]:
                #SECOND CONDITION ISN'T NEEDED, BUT REDUCES NUMBER OF RETURNS BY AI - ONLY CASE, WHEN IT CAN RETURN IS RESERVATION
                if all(env.tokens[color] >= 1 for color in combination):
                    mask[offset] = 1
                offset += 1

        for color in self.pick_tokens['doubles']:
            if env.tokens[color] >= 2 and sum(player_tokens.values()) <= 8:
                mask[offset] = 1
            offset += 1

        offset *= 2 #SKIPPING RETURNINGS

        state = env.return_state()
        player_reservations = env.players[env.current_player]['reservations']

        for action in ('buy', 'reserve'):
            for tier in (1,2,3):
                for card in range(4):
                    if card < len(state['tier'+str(tier)]) and ((action == 'buy' and env.can_afford(state['tier'+str(tier)].iloc[card])) or (action == 'reserve' and env.can_reserve(state['tier'+str(tier)].iloc[card]))):
                        mask[offset] = 1
                    offset += 1

        for reservation in player_reservations:
            if env.can_afford(reservation.iloc[0]):
                mask[offset] = 1
            offset += 1
        #warning, offset now doesn't necessarily points to index after reservations
        assert sum(mask) > 0
        return np.array(mask)
                    
    def available_outputs_when_returning(self, env):
        mask = [0]*sum(self.output_nodes)
        offset = self.output_nodes[0]
        player_tokens = env.players[env.current_player]['tokens']

        for tokens_to_return in [3,2,1]:
            for combination in self.pick_tokens[tokens_to_return]:
                if all(player_tokens[color] >= 1 for color in combination) and sum(player_tokens.values())-tokens_to_return <= 10:
                    mask[offset] = 1
                offset += 1

        for color in self.pick_tokens['doubles']:
            if player_tokens[color] >= 2 and sum(player_tokens.values())-2 <= 10:
                mask[offset] = 1
            offset += 1

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

    def get_best_move(self,env):
        state = env.return_state()
        aval_vector = self.available_outputs(env)

        #empty move not possible when other is possible
        if sum(aval_vector) != 1: 
            aval_vector[-1] = 0

        raw_prediction = self.get_scores_for_each_move(env)
        prediction = raw_prediction * aval_vector
        a = np.argmax(prediction)
        if prediction[a] <= 0:
            not0 = prediction != 0
            a = np.argmax(not0)

        return self.output_to_move(a,state)
