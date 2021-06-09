import aiohttp
import re
import numpy as np
import asyncio
import json
import logging
import yaml
from enum import Enum

with open('config.yaml', 'r') as f:
    config = yaml.safe_load(f)

TOKEN = config['token']
CHANNEL_ID = config['channel']
BET = config['bet']

DM_ID = "270904126974590976"
API_BASE = "https://discord.com/api/v9/"
MESSAGE_ENDPOINT = f"{API_BASE}channels/{CHANNEL_ID}/messages"
GATEWAY_ENDPOINT = "wss://gateway.discord.gg/?v=9&encoding=json"
HEADERS = {"Authorization": TOKEN}

CARD_PATTERN = re.compile(r'[0-9,J,Q,K,A]+')
SLEEP_PATTERN = re.compile(r'[0-9]')
HARD_ARRAY = np.array([
                 # 2-------------------------------------A
                 ['h', 'h', 'h','h','h','h','h','h','h','h'], #4
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
                 ['s', 's', 's','s','s','h','h','h','e','e'], #15
                 ['s', 's', 's','s','s','h','h','e','e','e'], #16
                 ['s', 's', 's','s','s','s','s','s','s','e'], #17
                 ['s', 's', 's','s','s','s','s','s','s','s'], #18
                 ['s', 's', 's','s','s','s','s','s','s','s'], #19
                 ['s', 's', 's','s','s','s','s','s','s','s'], #20
                 ['s', 's', 's','s','s','s','s','s','s','s'], #21
                 ])
SOFT_ARRAY = np.array([
                 ['h','h','h','h','h','h','h','h','h','h'], #13
                 ['h','h','h','h','h','h','h','h','h','h'], #14
                 ['h','h','h','h','h','h','h','h','h','h'], #15
                 ['h','h','h','h','h','h','h','h','h','h'], #16
                 ['h','h','h','h','h','h','h','h','h','h'], #17
                 ['s','s','s','s','s','s','s','h','h','h'], #18
                 ['s','s','s','s','s','s','s','s','s','s'], #19
                 ['s','s','s','s','s','s','s','s','s','s'], #20
                 ['s','s','s','s','s','s','s','s','s','s'] #21
                 ]) 

class OpCodes(): # TODO: have it stop breaking when subclassing Enum
    DISPATCH = 0
    HEARTBEAT = 1
    IDENTIFY = 2
    HELLO = 10
    ACK = 11

async def main():
    async with aiohttp.ClientSession(headers=HEADERS) as session, session.ws_connect(GATEWAY_ENDPOINT) as ws:
        await session.post(MESSAGE_ENDPOINT, json={"content": f"pls bj {BET}"})
        await handle_ws(ws, session)

async def handle_ws(ws, session):
    while True:
        msg = await ws.receive() 

        if msg.type == aiohttp.WSMsgType.TEXT:     
            payload = json.loads(msg.data) 

            if payload['op'] == OpCodes.HELLO:
                logging.info("Hello received")

                await identify(ws)
                asyncio.create_task(heartbeat_loop(ws, payload))

            if payload['op'] == OpCodes.ACK:
                logging.info("ACK received")

            if payload['op'] == OpCodes.DISPATCH:
                asyncio.create_task(handle_event(ws, session, payload))

            if payload['op'] == OpCodes.HEARTBEAT:
                await heartbeat(ws)

        elif msg.type == aiohttp.WSMsgType.CLOSE:
            logging.info("Closing connection")
            break
        
        elif msg.type == aiohttp.WSMsgType.ERROR:
            logging.error(msg)
            break

async def heartbeat_loop(ws, payload):
    interval_s = payload['d']['heartbeat_interval'] / 1000 # heartbeat interval comes in milliseconds

    while True:
        await asyncio.sleep(interval_s)
        await heartbeat(ws)


async def heartbeat(ws):
    heartbeat_payload = {'op': OpCodes.HEARTBEAT, 'd': 'null'}
    
    await ws_send(ws, heartbeat_payload)
    logging.info("Heartbeat sent")

async def identify(ws):
    identify_payload = {
        "op": OpCodes.IDENTIFY,
        "d": {
            "token": TOKEN,
            "properties": {
                "$os": "linux",
                "$browser": "my_library",
                "$device": "my_library"
            }
        }
    }
    await ws_send(ws, identify_payload)
    logging.info("Connected")

async def ws_send(ws, payload):
    await ws.send_str(json.dumps(payload))

async def handle_event(ws, session, payload): 
    type = payload['t']
    data = payload['d']

    if type == 'MESSAGE_CREATE':
        game_message = "Type `h` to **hit**, type `s` to **stand**, or type `e` to **end** the game."
        bj_command = f"pls bj {str(BET)}"      

        author = data['author']
        content = data['content']

        # wtf
        try:
            embed = data['embeds'][0] # get the first embed
            embed_desc = embed['description']
        except (KeyError, IndexError):
            embed_desc = ""


        if author['id'] == DM_ID: 
            logging.debug(f"{data}")

            if "ended" in content or any(x in embed_desc for x in ['win', 'lose', 'tie']): # start new game
                async with session.post(MESSAGE_ENDPOINT, json={"content":bj_command}) as r:
                    logging.info("Started new game")
                    return
                
            elif "Wait" in embed_desc:
                sleep_time = int(SLEEP_PATTERN.findall(embed_desc)[0])
                logging.info(f"Sleeping for {str(sleep_time)}s")
                await asyncio.sleep(sleep_time)

                # copy pasting code
                async with session.post(MESSAGE_ENDPOINT, json={"content":bj_command}) as r:
                    logging.info("Started new game after sleeping")
                    return
        
            elif game_message in content:
                embed_fields = embed['fields']
                user_fields = embed_fields[0]['value'].split('\n')
                dealer_fields = embed_fields[1]['value'].split('\n')

                user_cards = CARD_PATTERN.findall(user_fields[0])
                user_total = int(CARD_PATTERN.findall(user_fields[1])[0])

                dealer_card = CARD_PATTERN.findall(dealer_fields[0])[0]
                dealer_total = card_to_value(dealer_card)
                is_soft = is_hand_soft(user_cards, int(user_total))

                move = soft_strat(user_total, dealer_total) if is_soft else hard_strat(user_total, dealer_total)

                async with session.post(MESSAGE_ENDPOINT, json={"content":move}) as r:
                    logging.info("Played with " + move)
                    return

def is_hand_soft(hand, total):
    # i have absolutely no clue if the math here works lol
    
    pip_value = sum([int(i) for i in hand if i.isdigit()])
    face_value = sum([10 for i in hand if i in ['J', 'Q', 'K']])

    value_before_ace = pip_value + face_value
    ace_value = total - value_before_ace

    if ace_value >= 11:
        return True
    
    return False

def card_to_value(card):
    if card.isdigit():
        return int(card)
    elif card == 'A':
        return 11
    else:
        return 10

def soft_strat(user, dealer):
    return SOFT_ARRAY[user - 13][dealer - 2]


def hard_strat(user, dealer):   
    return HARD_ARRAY[user - 4][dealer - 2]

logging.basicConfig(level=logging.INFO)
asyncio.run(main())

'''
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
'''
