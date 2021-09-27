import os
import sys
from execjs import get
import glob
import csv
import xlsxwriter
import pandas as pd
import requests
import sha3
import json
import time
import datetime
from web3_input_decoder import decode_function
from function_track import get_insure, get_deposit_gauge, get_deposit_template, get_apply_cover, get_create_lock
import requests
from requests_oauthlib import OAuth1

decrypted_string = ''
runtime = get('Node')
context = runtime.compile('''
    module.paths.push('%s');
    const crypto = require('crypto');
    const ENCRYPTION_KEY = "HH95XH7sYAbznRBJSUE9W8RQxzQIGSas" // 32Byte
    const BUFFER_KEY = "RfHBdAR5RJHqp5ge" // 16Byte. 
    const ENCRYPT_METHOD = "aes-256-cbc" // encryption type
    const ENCODING = "hex" // encryption encoding
    function getDecryptedString(src,cfg, encrypted) {
        let iv = Buffer.from(BUFFER_KEY)
        let encryptedText = Buffer.from(encrypted, ENCODING)
        let decipher = crypto.createDecipheriv(ENCRYPT_METHOD, Buffer.from(ENCRYPTION_KEY), iv)
        let decrypted = decipher.update(encryptedText)
    
        decrypted = Buffer.concat([decrypted, decipher.final()])
    
        return decrypted.toString()
    }
''' % os.path.join(os.path.dirname(__file__),'node_modules'))

def decryptString(src,cfg=None):
    if cfg is None:
        cfg = dict(add=True)
    return context.call('getDecryptedString',src,cfg,decrypted_string)


# event topic array and event contract address
topicArray = [
    'Insured(uint256,uint256,bytes32,uint256,uint256,address)',
    'Deposit(address,uint256,uint256,uint256,uint256)',
    'Deposit(address,uint256)',
    'Deposit(address,uint256,uint256,int128,uint256)',
    'CoverApplied(uint256,uint256,uint256,uint256,bytes32[],string)'
]
topicAddress = [
    [
        '0x0A7B7A8dc9786777D813A5da5Aa0F62ed3165a25',
        '0x7Ef695C4Eb53e008616Fe332a30b752EB1824591',
        '0x69F10f16d088EBD74Ab96762B5cbA3D87818AC09',
        '0x7D976f20f27C042768a1659AE5a307e5e98EfcbD',
        '0xE4f0498eE8415b0BE861f1Ad22e3f6c42485acA0'
    ],
    [
        '0x819668109709acb70E0D3c735D92cea1E8F4D4F2',
        '0x4798786C63C26496bB462cBe6D2447FC9fD056E6',
        '0x86ef2D96b236FEb1cC62C90EEfDB4100dc8fcc24',
        '0x79d0A9ddF16E1C5D5dbA9e7bEc59E0fe049cb153',
        '0xF5B4a1A13558C0098904Da6B4a98dF07654f8231'
    ],
    '0xF46025D87F26d696bC1a60eAc4aDE1908134A089'
]
minBlockAddress = [
    [
        9066094,
        9067108,
        9067128,
        9056481,
        9067353
    ],
    [
        9057512,
        9057512,
        9057513,
        9057514,
        9057514
    ],
    9057507
]
logArray = [[],[],[],[],[]]
abiArray = [[[], [], []], [], []]
with open('ABI/PoolTemplate.json') as json_file:
    abiArray[0][0] = json.load(json_file)
with open('ABI/IndexTemplate.json') as json_file:
    abiArray[0][1] = json.load(json_file)
with open('ABI/CDS.json') as json_file:
    abiArray[0][2] = json.load(json_file)
with open('ABI/LiquidityGauge.json') as json_file:
    abiArray[1] = json.load(json_file)
with open('ABI/VotingEscrow.json') as json_file:
    abiArray[2] = json.load(json_file)

url = 'https://api-rinkeby.etherscan.io/api?'
headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'}
data = {"positions":[0,6,7,29]}

# Get user wallet address list from csv file
testnet_date = "1/8/2021"
userList = []
for csvfile in glob.glob('input.csv'):  
    with open(csvfile, 'r', errors='ignore') as f:          
        in_data = [row for row in csv.reader(f)]
        df = pd.read_csv('input.csv', encoding = "UTF-8")
        count = 0
        for i in range(1, len(df)+1):
            if len(in_data[i][0]) != 42:
                continue
            if in_data[i][0][0]!='0' or in_data[i][0][1]!='x':
                continue
            if in_data[i][2].find('https://twitter.com/') != 0 and in_data[i][2].find('https://mobile.twitter.com/') != 0 and in_data[i][2].find('https://www.twitter.com/') != 0:
                continue
            if in_data[i][2].find('/status/') == -1:
                continue
            if in_data[i][3].find('https://twitter.com/') != 0 and in_data[i][3].find('https://mobile.twitter.com/') != 0 and in_data[i][3].find('https://www.twitter.com/') != 0:
                continue
            if in_data[i][3].find('/status/') == -1:
                continue

            if in_data[i][1].find('https://twitter.com/') == 0:
                twitter_account = in_data[i][1][20:]
            if in_data[i][1].find('https://www.twitter.com/') == 0:
                twitter_account = in_data[i][1][24:]
            if in_data[i][1].find('https://mobile.twitter.com/') == 0:
                twitter_account = in_data[i][1][27:]
            if in_data[i][1][0] == '@':
                twitter_account = in_data[i][1][1:]
            if twitter_account.find('?s=') != -1:
                twitter_account = twitter_account[0:twitter_account.find('?s=')]
            if twitter_account.find('/status/') != -1:
                twitter_account = twitter_account[0:twitter_account.find('/status/')]
            if twitter_account.find('?t=') != -1:
                twitter_account = twitter_account[0:twitter_account.find('?t=')]
                
            is_in = False
            for user in userList:
                if user[0] == in_data[i][0]:
                    is_in = True
                    break                
                if user[2] == twitter_account:
                    is_in = True
                    break           
                
            if is_in == True:
                continue
            
            url_twitter = u'https://api.twitter.com/1.1/users/show.json?screen_name='+twitter_account
            queryoauth = OAuth1('8medq0BoEpX8Pk8BuEG9XImnU', 'Pk3zkP6oRvmzQNyFrZ5dU3SN4NoLuKjd4TbL2luuqqbH6ugrpP',
                            '2328436789-2iKolxAdt9h7wMP2UVSIszutIQzuqShjtuyZWIX', 'm03o1YQitrGXagjl5xBQ9MhIPYjJviMDS5lKaPSpm0dlc',
                            signature_type='query')
            response = requests.get(url_twitter, auth=queryoauth)
            if 'status' in response.json():
                date = time.strftime('%d/%m/%Y', time.strptime(response.json()['status']['created_at'],'%a %b %d %H:%M:%S +0000 %Y'))  
                if time.mktime(datetime.datetime.strptime(date,"%d/%m/%Y").timetuple()) < time.mktime(datetime.datetime.strptime(testnet_date,"%d/%m/%Y").timetuple()):
                    continue
            else:
                continue


            user = []
            mission = [0,0,0,0,0,0,0,0,0]

            if in_data[i][4] == '1':
                mission[7] = 1
            if in_data[i][5] == '1':
                mission[8] = 1

            user.append(in_data[i][0])
            user.append(mission)
            user.append(twitter_account)

            str_ind = in_data[i][2].find('/status/')+8
            end_ind = in_data[i][2].find('?s=') if in_data[i][2].find('?s=') != -1 else len(in_data[i][2])
            user.append(in_data[i][2][str_ind:end_ind])

            str_ind = in_data[i][3].find('/status/')+8
            end_ind = in_data[i][3].find('?s=') if in_data[i][3].find('?s=') != -1 else len(in_data[i][3])
            user.append(in_data[i][3][str_ind:end_ind])

            user.append(in_data[i][2])
            user.append(in_data[i][3])

            userList.append(user)


# Mission 1
print("---------- Mission 1 ----------")
for l in range(0, len(userList)):
    if userList[l][5].find(userList[l][2]) == -1:
        continue
    url_twitter = u'https://api.twitter.com/1.1/statuses/show.json?id='+userList[l][3]+'&tweet_mode=extended'
    queryoauth = OAuth1('8medq0BoEpX8Pk8BuEG9XImnU', 'Pk3zkP6oRvmzQNyFrZ5dU3SN4NoLuKjd4TbL2luuqqbH6ugrpP',
                    '2328436789-2iKolxAdt9h7wMP2UVSIszutIQzuqShjtuyZWIX', 'm03o1YQitrGXagjl5xBQ9MhIPYjJviMDS5lKaPSpm0dlc',
                    signature_type='query')
    response = requests.get(url_twitter, auth=queryoauth)
    print(url_twitter)
    if 'full_text' in response.json():        
        if response.json()['full_text'].find('#InsureDAO') == -1 and response.json()['full_text'].find('#insuredao') == -1 and response.json()['full_text'].find('#insureDAO') == -1:            
            continue
        split_text = response.json()['full_text'].split()
        for text in split_text:
            if text[0]=='0' and text[1]=='x' and text == userList[l][0]:
                print(userList[l][0])
                userList[l][1][0] = 1
            if len(text) > 60:
                decrypted_string = text
                if decryptString(open(sys.argv[-1],'r').read()) == userList[l][0]:
                    print(userList[l][0])
                    userList[l][1][0] = 1
 
# Mission 7
print("---------- Mission 7 ----------")
for l in range(0, len(userList)):
    if userList[l][6].find(userList[l][2]) == -1:
        continue
    url_twitter = u'https://api.twitter.com/1.1/statuses/show.json?id='+userList[l][4]+'&tweet_mode=extended'
    queryoauth = OAuth1('8medq0BoEpX8Pk8BuEG9XImnU', 'Pk3zkP6oRvmzQNyFrZ5dU3SN4NoLuKjd4TbL2luuqqbH6ugrpP',
                    '2328436789-2iKolxAdt9h7wMP2UVSIszutIQzuqShjtuyZWIX', 'm03o1YQitrGXagjl5xBQ9MhIPYjJviMDS5lKaPSpm0dlc',
                    signature_type='query')
    response = requests.get(url_twitter, auth=queryoauth)
    if 'full_text' in response.json() and response.json()['entities']['urls'][0]['display_url'].find("insuredao") != -1:
        print(userList[l][0])
        userList[l][1][6] = 1  
'''

# Mission 2
print("---------- Mission 2 ----------")
k = sha3.keccak_256()
k.update(topicArray[0].encode('utf-8'))
for i in range(0,3):    
    minBlock = minBlockAddress[0][i]
    maxBlock = 9999999999    
    while True:      
        params = {
            "module":"account",
            "action":"txlist",
            "address":topicAddress[0][i],
            "startblock":minBlock,
            "endblock":maxBlock,
            "sort": "asc",
            "apikey": "4EBDMX2VAVMIB8CUC6Q77S7R4TMMQD91TH"
        }
        r = requests.get(url, headers=headers, params=params, json=data)
        if r.status_code==200 and 'result' in r.json():
            for item in r.json()['result']:
                print(item['input'])
                if item['input'] == '0x':
                    continue
                arg = decode_function(abiArray[0][0], item['input'])
                if get_insure(arg) == True:
                    for l in range(0, len(userList)):
                        if item['from'].lower() == userList[l][0].lower():
                            print(item['from'].lower())
                            userList[l][1][1] = 1
        else:
            break
        len_result = len(r.json()['result'])
        if len_result == 10000:
            minBlock = int(r.json()['result'][len_result-1]['blockNumber']) + 1
        else:
            break

with open('test_output.csv', 'w') as file:
    writer = csv.writer(file, lineterminator='\n')
    writer.writerows(userList)

# Mission 3
print("---------- Mission 3 ----------")
k = sha3.keccak_256()
k.update(topicArray[1].encode('utf-8'))
for i in range(0, 5):
    minBlock = minBlockAddress[0][i]
    maxBlock = 9999999999    
    while True:      
        params = {
            "module":"account",
            "action":"txlist",
            "address":topicAddress[0][i],
            "startblock":minBlock,
            "endblock":maxBlock,
            "sort": "asc",
            "apikey": "4EBDMX2VAVMIB8CUC6Q77S7R4TMMQD91TH"
        }
        r = requests.get(url, headers=headers, params=params, json=data)
        if r.status_code==200 and 'result' in r.json():
            for item in r.json()['result']:
                if item['input'] == '0x':
                    continue
                if i == 3:
                    arg = decode_function(abiArray[0][1], item['input'])
                elif i == 4:
                    arg = decode_function(abiArray[0][2], item['input'])
                else:
                    arg = decode_function(abiArray[0][0], item['input'])
                if get_deposit_template(arg) == True:
                    for l in range(0, len(userList)):
                        if item['from'].lower() == userList[l][0].lower():
                            print(item['from'].lower())
                            userList[l][1][2] = 1
        else:
            break
        len_result = len(r.json()['result'])
        if len_result == 10000:
            minBlock = int(r.json()['result'][len_result-1]['blockNumber']) + 1
        else:
            break

# Mission 4
print("---------- Mission 4 ----------")
k = sha3.keccak_256()
k.update(topicArray[2].encode('utf-8'))
for i in range(0,5):   
    minBlock = minBlockAddress[1][i]
    maxBlock = 9999999999    
    while True:     
        params = {
            "module":"account",
            "action":"txlist",
            "address":topicAddress[1][i],
            "startblock":minBlock,
            "endblock":maxBlock,
            "sort": "asc",
            "apikey": "4EBDMX2VAVMIB8CUC6Q77S7R4TMMQD91TH"
        }
        r = requests.get(url, headers=headers, params=params, json=data)
        if r.status_code==200 and 'result' in r.json():
            for item in r.json()['result']:
                if item['input'] == '0x':
                    continue
                arg = decode_function(abiArray[1], item['input'])
                if get_deposit_gauge(arg) == True:
                    for l in range(0, len(userList)):
                        if item['from'].lower() == userList[l][0].lower():
                            print(item['from'].lower())
                            userList[l][1][3] = 1
        else:
            break
        len_result = len(r.json()['result'])
        if len_result == 10000:
            minBlock = int(r.json()['result'][len_result-1]['blockNumber']) + 1
        else:
            break


# Mission 5
print("---------- Mission 5 ----------")
k = sha3.keccak_256()
k.update(topicArray[2].encode('utf-8')) 
minBlock = minBlockAddress[2]
maxBlock = 9999999999    
while True:     
    params = {
        "module":"account",
        "action":"txlist",
        "address":topicAddress[2],
        "startblock":minBlock,
        "endblock":maxBlock,
        "sort": "asc",
        "apikey": "4EBDMX2VAVMIB8CUC6Q77S7R4TMMQD91TH"
    }
    r = requests.get(url, headers=headers, params=params, json=data)
    if r.status_code==200 and 'result' in r.json():
        for item in r.json()['result']:
            if item['input'] == '0x':
                continue
            arg = decode_function(abiArray[2], item['input'])
            if get_create_lock(arg) == True:
                for l in range(0, len(userList)):
                    if item['from'].lower() == userList[l][0].lower():
                        print(item['from'].lower())
                        userList[l][1][4] = 1
    else:
        break
    len_result = len(r.json()['result'])
    if len_result == 10000:
        minBlock = int(r.json()['result'][len_result-1]['blockNumber']) + 1
    else:
        break

# Mission 6
print("---------- Mission 6 ----------")
k = sha3.keccak_256()
k.update(topicArray[4].encode('utf-8'))
for i in range(0,3):    
    minBlock = minBlockAddress[0][i]
    maxBlock = 9999999999    
    while True:        
        params = {
            "module":"account",
            "action":"txlist",
            "address":topicAddress[0][i],
            "startblock":minBlock,
            "endblock":maxBlock,
            "sort": "asc",
            "apikey": "4EBDMX2VAVMIB8CUC6Q77S7R4TMMQD91TH"
        }
        r = requests.get(url, headers=headers, params=params, json=data)
        if r.status_code==200 and 'result' in r.json():
            for item in r.json()['result']:
                if item['input'] == '0x':
                    continue
                arg = decode_function(abiArray[0][0], item['input'])
                if get_apply_cover(arg) == True:
                    for l in range(0, len(userList)):
                        if item['from'].lower() == userList[l][0].lower():
                            print(item['from'].lower())
                            userList[l][1][5] = 1
        else:
            break
        len_result = len(r.json()['result'])
        if len_result == 10000:
            minBlock = int(r.json()['result'][len_result-1]['blockNumber']) + 1
        else:
            break

print(userList)


# output.xlsx prepare
workbook = xlsxwriter.Workbook('output.xlsx')
worksheet = workbook.add_worksheet()
worksheet.write('A1', "Wallet Address")
worksheet.write('B1', "Number of Lines")

# Line number calculate
i = 2
for user in userList:
    track = user[1]
    count = 0
    if track[0] == 1 and track[1] == 1 and track[2] == 1:
        count = count + 1
    if track[3] == 1 and track[4] == 1 and track[5] == 1:
        count = count + 1
    if track[6] == 1 and track[7] == 1 and track[8] == 1:
        count = count + 1
    if track[0] == 1 and track[3] == 1 and track[6] == 1:
        count = count + 1
    if track[1] == 1 and track[4] == 1 and track[7] == 1:
        count = count + 1
    if track[2] == 1 and track[5] == 1 and track[8] == 1:
        count = count + 1
    if track[0] == 1 and track[4] == 1 and track[8] == 1:
        count = count + 1
    if track[2] == 1 and track[4] == 1 and track[6] == 1:
        count = count + 1
    worksheet.write('A'+str(i), user[0])
    worksheet.write('B'+str(i), count)
    i = i + 1

workbook.close()
'''