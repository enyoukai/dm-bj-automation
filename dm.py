import aiohttp
import re
import numpy as np
import asyncio
import json
import logging

from enum import Enum

with open('token.txt', 'r') as f:
    TOKEN = f.read()

CHANNEL_ID = ''
DM_ID = "270904126974590976"
API_BASE = "https://discord.com/api/v9/"
MESSAGE_ENDPOINT = f"{API_BASE}channels/{CHANNEL_ID}/messages"
GATEWAY_ENDPOINT = "wss://gateway.discord.gg/?v=9&encoding=json"

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

class OpCodes(): # seems to break with enum. fix later i guess
    DISPATCH = 0
    HEARTBEAT = 1
    IDENTIFY = 2
    HELLO = 10
    ACK = 11

async def main():
    async with aiohttp.ClientSession() as session, session.ws_connect(GATEWAY_ENDPOINT) as ws:
        await handle_ws(ws)

async def handle_ws(ws):
    while True:
        msg = await ws.receive() 

        if msg.type == aiohttp.WSMsgType.TEXT:     
            payload = json.loads(msg.data) 

            if payload['op'] == OpCodes.HELLO:
                logging.info("Hello received")

                asyncio.create_task(identify(ws))
                asyncio.create_task(heartbeat(ws, payload))

            if payload['op'] == OpCodes.ACK:
                logging.info("ACK received")

            if payload['op'] == OpCodes.DISPATCH:
                asyncio.create_task(handle_event(ws, payload))

        elif msg.type == aiohttp.WSMsgType.CLOSE:
            logging.info("Closing connection")
            await ws.close()
            break

async def heartbeat(ws, payload):
    heartbeat_payload = {'op': OpCodes.HEARTBEAT, 'd': 'null'}
    interval_s = payload['d']['heartbeat_interval'] / 1000 # heartbeat interval comes in milliseconds

    while True:
        await asyncio.sleep(interval_s)
        await send(ws, heartbeat_payload)

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
    await send(ws, identify_payload)
    logging.info("Connected")

async def send(ws, payload):
    await ws.send_str(json.dumps(payload))

async def handle_event(ws, payload):
    logging.debug(payload)
    
    type = payload['t']
    data = payload['d']

    if type == 'MESSAGE_CREATE':
        author = data['author']
        logging.info(f"{author['username']}#{author['discriminator']}: {data['content']}")

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
