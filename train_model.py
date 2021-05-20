import sys
sys.path.insert(0, 'splendor_ai')
from splendor_ai.alpha_zero import AlphaZero
from splendor_ai.mini_splendor_state_encoder import MiniSplendorStateEncoder
import interactive_splendor
from environment import minisplendor


model = AlphaZero(MiniSplendorStateEncoder(),0.2,10)
model.net.train_heuristic()
num_iters = 1
num_comparision_games = 1
needed_wins = 0

it = 0
while True:
    model.is_learning = True
    print('self play')
    for i in range(num_iters):
        print('game',i)
        interactive_splendor.play_game(False,True,(('m1',model), ('m2',model)), minisplendor.MiniSplendor())

    model2 = model.produce_new_version()
    model.is_learning, model2.is_learning = True, True

    r = [0,0]
    print('fight!')
    for i in range(num_comparision_games):
        players = (('m1',model), ('m2',model2))
        swapped = False
        if i > num_comparision_games//2:
            players = (('m2',model2), ('m1',model))
            swapped = True
        
        result = interactive_splendor.play_game(False,False,players,minisplendor.MiniSplendor())
        print('game result = ',result if not swapped else 1-result)
        r[result if not swapped else 1-result] += 1

    print('loses = ',r[0],',wins = ',r[1])
    if r[1] >= needed_wins:
        print('better model')
        model = model2
        model.net.model.save('saved/my_model'+str(it))
        it += 1