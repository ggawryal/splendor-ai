from random_mover import RandomMover

def load_model(name):
    if name == 'random':
        return RandomMover()
    else:
        raise RuntimeError("Unknown AI name")