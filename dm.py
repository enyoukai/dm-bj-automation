import requests
from time import sleep
import re
import numpy as np
import copy

with open('token.txt', 'r') as f:
    TOKEN = f.read()

USER = 'saber'
CHANNEL_ID = '804605889033273367'
DM_ID = "270904126974590976"
API_BASE = "https://discord.com/api/v8/"
MESSAGE_BASE = f"{API_BASE}channels/{CHANNEL_ID}/messages"

p2 = re.compile(r'[0-9,J,Q,K,A]+')

hard = np.array([['h', 'h', 'h','h','h','h','h','h','h','h'], #4
                 ['h', 'h', 'h','h','h','h','h','h','h','h'], #5
                 ['h', 'h', 'h','h','h','h','h','h','h','h'], #6
                 ['h', 'h', 'h','h','h','h','h','h','h','h'], #7
                 ['h', 'h', 'h','h','h','h','h','h','h','h'], #8
                 ['h', 'h', 'h','h','h','h','h','h','h','h'], #9
                 ['h', 'h', 'h','h','h','h','h','h','h','h'], #10
                 ['h', 'h', 'h','h','h','h','h','h','h','h'], #11
                 ['h', 'h', 's','s','s','h','h','h','h','h'], #12
                 ['s', 's', 's','s','s','h','h','h','h','h'], #13
                 ['s', 's', 's','s','s','h','h','h','h','h'], #14
                 ['s', 's', 's','s','s','h','h','h','h','h'], #15
                 ['s', 's', 's','s','s','h','h','h','e','e'], #16
                 ['s', 's', 's','s','s','s','s','s','s','s'], #17
                 ['s', 's', 's','s','s','s','s','s','s','s'], #18
                 ['s', 's', 's','s','s','s','s','s','s','s'], #19
                 ['s', 's', 's','s','s','s','s','s','s','s'], #20
                 ['s', 's', 's','s','s','s','s','s','s','s'], #21
                 ])
soft = np.array([['h','h','h','h','h','h','h','h','h','h'], #13
                 ['h','h','h','h','h','h','h','h','h','h'], #14
                 ['h','h','h','h','h','h','h','h','h','h'], #15
                 ['h','h','h','h','h','h','h','h','h','h'], #16
                 ['h','h','h','h','h','h','h','h','h','h'], #17
                 ['s','s','s','s','s','s','s','h','h','s'], #18
                 ['s','s','s','s','s','s','s','s','s','s'], #19
                 ['s','s','s','s','s','s','s','s','s','s'], #20
                 ['s','s','s','s','s','s','s','s','s','s'] #21
                 ]) 

def soft_strat(user, v):
    print(f"USER: {user}\nDEALER: {v}")
    return soft[user - 13][v - 2]


def hard_strat(user, v):   
    print(f"USER: {user}\nDEALER: {v}")
    return hard[user - 4][v - 2]

while True:
    r = requests.get(MESSAGE_BASE, headers={"Authorization": TOKEN})
    if r.json()[0]['author']['id'] != DM_ID:
        print('NEXT_SESSION')
        sleep(1)
        continue
    try:
        if r.json()[0]['content'] == 'you need to respond to me damn' or r.json()[0]['content'] == 'you ended the game' or 'Results' in r.json()[0]['embeds'][0]['fields'][0]['name'] or [i for i in ["lose", "win", "tie"] if(i in r.json()[0]['embeds'][0]['description'])]:
            requests.post(MESSAGE_BASE, headers={"Authorization":TOKEN}, json={"content":"pls bj 50"})
            continue

    except (KeyError, IndexError):
        pass
    
    r = requests.get(MESSAGE_BASE, headers={"Authorization": TOKEN})

    user_cards = p2.findall(r.json()[0]['embeds'][0]['fields'][0]['value'].split('\n')[0])
    print(f"USER_CARDS: {user_cards}")
    user_total = int(p2.findall(r.json()[0]['embeds'][0]['fields'][0]['value'].split('\n')[1])[0])

    dealer_card = p2.findall(r.json()[0]['embeds'][0]['fields'][1]['value'].split('\n')[0])[0]

    int_user_cards = [int(i) for i in user_cards if i.isdigit()]
    ace_user_cards = [i for i in user_cards if i == 'A']
    face_user_cards = [i for i in user_cards if i in ['J', 'Q', 'K']]

    if dealer_card in ['K', 'Q', 'J']: 
        dealer_card = 10
    elif dealer_card == 'A': 
        dealer_card = 11
    else: 
        dealer_card = int(dealer_card)

    if ace_user_cards and sum(int_user_cards) + (len(face_user_cards) * 10) + (len(ace_user_cards) * 11) < 22: # check if hand is soft
        print("SOFT_HAND")
        idk_what_to_name_this = soft_strat(user_total, dealer_card)
        requests.post(MESSAGE_BASE, headers={"Authorization":TOKEN}, json={"content":idk_what_to_name_this})


    else:
        print("HARD_HAND")
        idk = hard_strat(user_total, dealer_card)
        requests.post(MESSAGE_BASE, headers={"Authorization":TOKEN}, json={"content":idk})

    sleep(8)