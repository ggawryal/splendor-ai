import itertools as it
import numpy as np
from environment import config

class AbstractModel:
    def __init__(self, state_encoder):
        self.output_nodes = np.sum(state_encoder.output_nodes)
        self.input_nodes = state_encoder.input_nodes
        self.state_encoder = state_encoder

    def get_scores_for_each_move(self,state): #abstract method, convert state using state_to_vector if needed
        pass

    def update_model_after_game(self, v):
        pass

    def get_best_move(self,env):
        state = env.return_state()
        aval_vector = self.state_encoder.available_outputs(env)

        #empty move not possible when other is possible
        if sum(aval_vector) != 1: 
            aval_vector[-1] = 0

        raw_prediction = self.get_scores_for_each_move(env)
        prediction = raw_prediction * aval_vector
        a = np.argmax(prediction)
        if prediction[a] <= 0:
            not0 = prediction != 0
            a = np.argmax(not0)

        return self.state_encoder.output_to_move(a,state)
