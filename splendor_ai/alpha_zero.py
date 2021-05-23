import numpy as np
from abstract_model import AbstractModel
from nnet import NNet

class AlphaZero(AbstractModel):
    def __init__(self, state_encoder, exploration_rate, number_of_mcts_simulations):
        super().__init__(state_encoder)
        self.exploration_rate = exploration_rate
        self.number_of_mcts_simulations = number_of_mcts_simulations
        self.visited_states = set()
        self.examples = []
        self.P = {} #P[s][a] = policy value for move a in state s
        self.Q = {} #Q[s][a] = q-value of taking action a from state s
        self.N = {} #N[s][a] = number of times algorithm played action a from state s
        self.is_learning = False
        self.net = NNet(self.input_nodes, self.output_nodes)

    def simulate_game(self, env,depth=0):
        s = self.state_encoder.state_to_vector(env.return_state(False))
        if s not in self.visited_states:
            self.Q[s] = [0]*self.output_nodes
            self.N[s] = [0]*self.output_nodes
            
        if env.end or depth >= 200:
            return self.get_score_at_end_pos(env.current_player, env.winner)

        
        if s not in self.visited_states:
            self.visited_states.add(s)
            prediction = self.net.predict(s)
            self.P[s] = prediction[0][0]
            v = prediction[1][0][0]
            print(v)
            return v
    
        best_action = (-float("inf"), -1)

        for action, avail in enumerate(self.state_encoder.available_outputs(env)):
            if avail:
                upper_confidence_bound = self.Q[s][action] + self.exploration_rate * self.P[s][action]*(sum(self.N[s])**0.5)/(1+self.N[s][action])
                best_action = max(best_action, (upper_confidence_bound, action))
        
        action = best_action[1]
        cur_player = env.current_player
        #print("moving", self.output_to_move(action, env.return_state()))
        env.move(self.state_encoder.output_to_move(action, env.return_state()))
        player_after_move = env.current_player
        v = self.simulate_game(env,depth+1)
        if cur_player != player_after_move:
            v *= -1
    
        
        self.Q[s][action] = (self.N[s][action]*self.Q[s][action] + v)/(self.N[s][action]+1)
        self.N[s][action] += 1
        return v

    def get_pi(self, state):
        ns = np.array(self.N[state])
        if sum(ns) == 0:
            ns = np.ones(self.output_nodes)
        return ns/sum(ns)


    def get_scores_for_each_move(self,env):
        for _ in range(self.number_of_mcts_simulations):
            ecp = env.copy()
            result = self.simulate_game(ecp,0)
            #print('game_result = ',result)
             
        s = self.state_encoder.state_to_vector(env.return_state(False))
        pi = self.get_pi(s)
        if self.is_learning:
            self.examples.append((s, pi.copy(),None))
        return pi

    def get_best_move(self,env):
        state = env.return_state()
        aval_vector = self.state_encoder.available_outputs(env)
        raw_prediction = self.get_scores_for_each_move(env)
        prediction = raw_prediction * aval_vector
        assert sum(prediction) > 0
        prediction /= sum(prediction)
        #for i in range(len(prediction)):
        #    assert prediction[i] == raw_prediction[i]
        return self.state_encoder.output_to_move(np.random.choice(len(prediction), p=prediction),state)


    def update_model_after_game(self,env):
        if self.is_learning:
            #abs(ex[0][0] - loser) is 1 if current player is winner, 0 is he lost and 0.5 if loser == 0.5
            self.examples = [(ex[0],ex[1], ex[2] if ex[2] is not None else self.get_score_at_end_pos(ex[0][0],env.winner)) for ex in self.examples]

    def produce_new_version(self):
        new_net = NNet(self.input_nodes, self.output_nodes)
        new_net.train(self.examples)

        az = AlphaZero(self.state_encoder, self.exploration_rate, self.number_of_mcts_simulations)
        az.net = new_net
        return az

    def get_score_at_end_pos(self,current_player, winner):
        if current_player == winner:
            return 1
        elif current_player == 1-winner:
            return -1
        return 0