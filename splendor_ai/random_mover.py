from typing import AbstractSet
import numpy as np
from abstract_model import AbstractModel

class RandomMover(AbstractModel):
    def get_scores_for_each_move(self,env,):
        return np.random.rand(sum(self.output_nodes))

