from random_mover import RandomMover

def load_model(name, state_encoder):
    if name == 'random':
        return RandomMover(state_encoder)
    else:
        raise RuntimeError("Unknown AI name")