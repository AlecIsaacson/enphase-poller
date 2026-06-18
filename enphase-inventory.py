#!/home/alec/enphase-poller/venv/bin/python3

import requests
import json
import urllib3
import re
from dotenv import dotenv_values
import logging
import time

logging.Formatter.converter = time.gmtime
logging.basicConfig(filename='/home/alec/enphase-poller/enphase-inventory.log', level=logging.INFO, format='%(asctime)s.%(msecs)03dZ %(levelname)s : %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)

logger.info('Starting inventory')

urllib3.disable_warnings()

secrets = dotenv_values('/home/alec/enphase-poller/.env')

# Get inventory from Enphase box.
def getInventory(inventoryEndpoint):
	try:
		headers = {'Authorization' : 'Bearer ' + secrets['solarApiKey'], 'Accept' : 'application/json'}
		# print(headers)

		response = requests.get(secrets['baseURL'] + inventoryEndpoint, verify=False, headers=headers)

		if response.status_code != 200:
			logger.info('getInventory bad response code: ' + response.status_code)
		# print(response.status_code)
		# print(response.json())

		return(response.json())
	except Exception as err:
		logger.info('Exception in getInventory: ' + str(err))

# Send logs to Grafana
def sendLogs(logLabels, logData):
	try:
		logger.info('In sendLogs')
		nowNs = str(int(time.time() * 1000000000))
		logDict = {'streams': [{'stream': logLabels, 'values': [[nowNs, json.dumps(logData)]]}]}
		# print(logDict)
		headers = {'Authorization' : 'Bearer ' + secrets['logKey'], 'Content-Type' : 'application/json'}
		
		response = requests.post(secrets['logURL'], headers=headers, data=json.dumps(logDict))
		# print(response.text)
		# print(response.status_code)
	except Exception as err:
		logger.info('Exception in sendLogs: ' + str(err))


def main():
	logger.info('In Main')
	inverterInventory = getInventory('/inventory.json')
	logger.info('Iterating inverters')
	for item in inverterInventory:
		if item['type'] == 'PCU':
			for device in item['devices']:
				# print(device['part_num'] + ' ' + device['serial_num'])
				logLabels = {'service_name' : 'solar_array', 'part_num' : device['part_num'], 'serial_num' : device['serial_num']}
				del device['part_num']
				del device['serial_num']
				sendLogs(logLabels, device)

	gatewayStatus = getInventory('/home')
	logger.info('Getting gateway inventory')
	logLabels = {'service_name' : 'solar_gateway'}
	sendLogs(logLabels, gatewayStatus)
	# print(gatewayStatus)

if __name__ == '__main__':
	main()
	logger.info('Run complete')

