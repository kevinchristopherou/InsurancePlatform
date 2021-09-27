from requests_oauthlib import OAuth1Session
import requests
from requests_oauthlib import OAuth1

url = 'https://api-rinkeby.etherscan.io/api?'
headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'}
data = {"positions":[0,6,7,29]}

params = {
    "module":"account",
    "action":"txlist",
    "address":"0x0A7B7A8dc9786777D813A5da5Aa0F62ed3165a25",
    "startblock":9072551,
    "endblock":9999999999,
    "sort": "asc",
    "apikey": "4EBDMX2VAVMIB8CUC6Q77S7R4TMMQD91TH"
}
r = requests.get(url, headers=headers, params=params, json=data)
print(len(r.json()['result']))