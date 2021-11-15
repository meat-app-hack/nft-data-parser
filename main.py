from web3 import Web3
import requests
import sqlite3
import base64
import urllib
from PIL import Image
import json
from io import BytesIO
import time
import copy

from svglib.svglib import svg2rlg
from reportlab.graphics import renderPM
from ABI import ABI

def stringToBase64(s):
    return base64.b64encode(s.encode('utf-8'))

def base64ToString(b):
    return base64.b64decode(b).decode('utf-8')

def fetchTokenURI(contract_address, token_id):
    
    w3 = Web3(Web3.HTTPProvider("https://mainnet.infura.io/v3/531cd98c6b1545c9ac016165b9c8ea9b"))
    contract = w3.eth.contract(contract_address, abi=ABI)
    return contract.functions.tokenURI(token_id).call()

def parse_colomns(size=9000, PATH_TO_DB='nfts.sqlite'):
    with open('9k_label.csv', 'w', encoding='utf-8') as csv:
        connection = sqlite3.connect(PATH_TO_DB)
        cursor = connection.cursor()
        print("Connected to database")

        sqlite_select_query = """SELECT * from current_market_values"""
        cursor.execute(sqlite_select_query)
        records = cursor.fetchmany(size)
        print("Fetching Total ", size," rows")
        print("Printing each row")
        last_nft_addres = 'last_nft_addres'
        j = -1
        counter = 0
        for row in records:
            print("nft_address: ", row[0])
            print("token_id: ", row[1])
            print("market_value: ", row[2])
            print("\n")
            if last_nft_addres != row[0]:
                last_nft_addres = copy.copy(row[0])
                j += 1
            counter += 1
            
            try:
                algo(row[0], int(row[1]), j)
                csv.write('{}_{}.png'.format(j, int(row[1])) + ',' + str(int(row[2])/(10**18)) + '\n')
            except:
                continue
        print('counter =', counter)
        cursor.close()

def algo(contract_address, token_id, j):
    res = fetchTokenURI(contract_address, token_id)
    if res.startswith( 'ipfs' ):
        replacement = 'https://cloudflare-ipfs.com/ipfs/'
        url = res.replace("ipfs://", replacement)

        response = requests.get(url)   
        dict = response.json()
        img_url = dict['image'].replace("ipfs://", replacement)

        response = requests.get(img_url)
        img_pil = Image.open(BytesIO(response.content))
        img_pil.save("./9k_imgs/{}_{}.png".format(j, token_id))

    elif res.startswith( 'data:application/json;base64' ):
        slice_ind = res.find(',') + 1
        b = res[slice_ind:].encode('ascii')

        decoded = json.loads(bytes.decode(base64.b64decode(b), "UTF-8"))

        base64image = decoded["image"].replace("data:image/svg+xml;base64,", "")

        with open('./test.svg', 'wb') as f:
            f.write(base64.b64decode(base64image))
        drawing = svg2rlg("test.svg")

        renderPM.drawToFile(drawing, "./9k_imgs/{}_{}.png".format(j, token_id), fmt="PNG")

    elif res.startswith( 'http' ):
        file = urllib.request.urlopen(res)
        
        for line in file:
            decoded_line = line.decode("utf-8")
            img_url = json.loads(decoded_line)["image"]
        
        response = requests.get(img_url)
        img_pil = Image.open(BytesIO(response.content))
        img_pil.save("./9k_imgs/{}_{}.png".format(j, token_id))

    else:
        print('res = ', res)
        print("nft_address: ", contract_address, "token_id: ", token_id)


start_time = time.time()
parse_colomns()
print('time = ', time.time() - start_time)