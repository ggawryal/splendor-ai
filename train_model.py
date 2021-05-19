import sys
sys.path.insert(0, 'splendor_ai')
from splendor_ai.alpha_zero import AlphaZero
import interactive_splendor

model = AlphaZero(0.4,20)
num_iters = 10
num_comparision_games = 10
needed_wins = 7

while True:
    model.is_learning = True
    print('self play')
    for i in range(num_iters):
        print('game ',i)
        interactive_splendor.play_game(False,True,(('m1',model), ('m2',model)))

    model2 = model.produce_new_version()
    model.is_learning, model2.is_learning = False, False

    r = [0,0]
    print('fight!')
    input()
    for i in range(num_comparision_games):  
        r[interactive_splendor.play_game(False,False,(('m1',model), ('m2',model2)))] += 1
    print(r[0],r[1])
    input()
    if r[1] >= needed_wins:
        print('better model')
        model = model2
        model.model.save('saved/my_model')