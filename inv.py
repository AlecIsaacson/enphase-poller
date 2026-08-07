#!/home/alec/GitHub/enphase-poller/venv/bin/python3

import requests
import json
import urllib3
import re
from dotenv import dotenv_values
import logging
import time

urllib3.disable_warnings()

secrets = dotenv_values('/home/alec/GitHub/enphase-poller/.env')

# Get inventory from Enphase box.
def getInventory(inventoryEndpoint):
        try:
                headers = {'Authorization' : 'Bearer ' + secrets['solarApiKey'], 'Accept' : 'application/json'}
                # print(headers)

                response = requests.get(secrets['baseURL'] + inventoryEndpoint, verify=False, headers=headers)
                print(response.text)

                if response.status_code != 200:
                        print('getInventory bad response code: ' + response.status_code)
                print(response.status_code)
                # print(response.json())

                return(response.json())
        except Exception as err:
                print('Exception in getInventory: ' + str(err))

def main():
        softwareDetails = getInventory('/info')

if __name__ == '__main__':
        main()

