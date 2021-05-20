
import os
import time
import sys

from environment import splendor,config, minisplendor
from print_board import PrintBoard
sys.setrecursionlimit(10000)
sys.path.insert(0, 'splendor_ai')
from splendor_state_encoder import SplendorStateEncoder
from mini_splendor_state_encoder import MiniSplendorStateEncoder
from model_loader import load_model


def is_int(x):
    try:
        int(x)
        return True
    except:
        return False

def get_card(s, player_index, card_idx):
    player_reservations = s['players'][player_index]['reservations']

    if card_idx in s['tier1'].index:
        return s['tier1'].loc[card_idx]
    elif card_idx in s['tier2'].index:
        return s['tier2'].loc[card_idx]
    elif card_idx in s['tier3'].index:
        return s['tier3'].loc[card_idx]
    elif any(card_idx in i.index for i in player_reservations):
        reservation = [i for i in player_reservations if card_idx in i.index][0]
        return reservation.iloc[0]


def play_game(show_game, training_mode, names_and_models, env):
    players = names_and_models
            
    if show_game:
        os.system('clear')
        print('USAGE')
        print('\tpick tokens:')
        print('\t\tp[5 integers corresponding to amount of tokens of each color]')
        print('\t\texample: „gkr“ will pick 1 green, 1 black and 1 red, „bb“ will pick 2 blue tokens')
        print('\tbuy card:')
        print('\t\tb[index of card to pick]')
        print('\t\texample: „b36“')
        print('\treserve card:')
        print('\t\tr[index of card to reserve]')
        print('\t\texample: „r17“')
        print('\tto end game simply type one of following: „end“, „q“, „bye“, CTRIL-C or CTRIL-D')
        print()

    s = env.return_state()

    short = {'g': 'green', 'w': 'white', 'b': 'blue', 'k': 'black', 'r': 'red'}
    player_index = 0
    game_round = 1
    anty_nystagmus = 0
    if show_game:
        input('Press ENTER to start game')
        PrintBoard.print_state(s, game_round, player_index)

    while True:
        if players[player_index][1] is None:
            sys.stdout.write('player' + str(player_index+1) + ' >> ')
            try:
                user_input = input()
            except:
                print()
                break

            if user_input in ['end', 'q', 'bye']:
                break

            if user_input == '' or user_input == '0':
                move = {'pick': {}}

            elif user_input[0] == 'b' and is_int(user_input[1:]):
                card_idx = int(user_input[1:])
                card = get_card(s,player_index,card_idx)
                move = {'buy': card}

            elif user_input[0] == 'r' and is_int(user_input[1:]):
                card_idx = int(user_input[1:])
                card = get_card(s,player_index,card_idx)

                move = {'reserve': card}

            elif all(map(lambda x: x in short, user_input)):
                try:
                    to_pick = {i: 0 for i in env.COLORS}
                    for color_letter in user_input:
                        to_pick[short[color_letter]] += 1

                    if s['return_tokens']:
                        move = {'return': to_pick}
                    else:
                        move = {'pick': to_pick}

                except Exception as e:
                    if s['return_tokens']:
                        print('can\'t return, error: ' + str(e))
                    else:
                        print('can\'t pick, error: ' + str(e))
                    continue

            else:
                print('invalid action, avaliable actions: p b r')
                continue

            try:
                s = env.move(move)
            except Exception as e:
                print('wrong move, error: ' + str(e))
                continue

        else:
            model_name, model = players[player_index]
            if show_game:
                sys.stdout.write('player' + str(player_index+1) + ' [' + model_name + '] >> ')
            thinking_start = time.time()
            
            move = model.get_best_move(env)
            s = env.move(move)
            if show_game:
                print(move)
                sys.stdout.write('Press ENTER to confirm')
                input()
            
                thinking_time = time.time() - thinking_start
                if thinking_time < anty_nystagmus:
                    time.sleep(anty_nystagmus - thinking_time)

        s = env.return_state(False)
        player_index = s['player_index']

        if player_index == 0 and not s['return_tokens'] and not s['end']:
            game_round += 1
        if game_round >= 80:
            env.end = True

        if show_game:
            PrintBoard.print_state(s, game_round, player_index)
        if s['end']:
            if training_mode:
                for model_name, model in players:
                    if model_name != 'p':
                        model.update_model_after_game(env)
            return env.winner
            
if __name__ == '__main__':
    version = sys.argv[1]
    if version == 'm' or version == 'mini':
        env = minisplendor.MiniSplendor()
        state_encoder = MiniSplendorStateEncoder()
    else:
        env = splendor.Splendor()
        state_encoder = SplendorStateEncoder()

    names_and_models = [('p',None)] * config.PLAYERS
    for i, name in enumerate(sys.argv[2:]):
        if name != 'p':
            names_and_models[i] = (name, load_model(name,state_encoder))

    play_game(True, False, names_and_models, env)