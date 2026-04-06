#!/usr/bin/python3

import requests
import json
import urllib3
import re
from dotenv import dotenv_values
import logging
import time

logging.Formatter.converter = time.gmtime
logging.basicConfig(filename='/home/alec/enphase-poller/enphase-poller.log', level=logging.INFO, format='%(asctime)s.%(msecs)03dZ %(levelname)s : %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)

logger.info('Starting poller')

urllib3.disable_warnings()

secrets = dotenv_values('/home/alec/enphase-poller/.env')


prodMetrics = ['activeCount','wNow','whLifetime','varhLeadLifetime','varhLagLifetime','vahLifetime','rmsCurrent','rmsVoltage','reactPwr','apprntPwr','pwrFactor','whToday','whLastSevenDays', 'vahToday', 'varhLeadToday', 'varhLagToday']
consumeMetrics = ['activeCount','wNow','whLifetime','varhLeadLifetime','varhLagLifetime','vahLifetime','rmsCurrent','rmsVoltage','reactPwr','apprntPwr','pwrFactor','whToday','whLastSevenDays','vahToday','varhLeadToday','varhLagToday']

def getMetrics():
	try:
		headers = {'Authorization' : 'Bearer ' + secrets['solarApiKey'], 'Accept' : 'application/json'}
		# print(headers)

		response = requests.get(secrets['baseURL'] + "/production.json?details=1", verify=False, headers=headers)

		if response.status_code != 200:
			logger.info('setMetrics bad response code: ' + response.status_code)
		# print(response.status_code)
		# print(response.json())

		return(response.json())
	except Exception as err:
		logger.info('Exception in getMetrics: ' + str(err))

def sendMetrics(metricName, metricValue, readingTime):
	try:
		metricName = re.sub(r'([a-z])([A-Z])', r'\1_\2', metricName).lower()
		
		if readingTime == 0:
			readingTime = ''
		
		metricData = metricName + ',location=' + secrets['siteID'] + ' metric=' + str(metricValue) + ' ' + str(readingTime)
		# print(metricData)

		headers = {"Authorization": "Bearer " + secrets['grafanaMetricKey'], "Content-Type": "text/plain"}
		response = requests.post(secrets['grafanaMetricURL'], headers=headers, data=metricData)
		
		if response.status_code != 204:
			logger.info('sendMetrics bad response code: ' + str(response.status_code))
			logger.info('Unable to send: ' + metricData)
		#print(response)
		
		return
	except Exception as err:
		logger.info('Exception in sendMetrics: ' + str(err))

def main():
	logger.info('In Main')
	solarData = getMetrics()
	logger.info('Iterating production')
	for item in solarData['production']:
		if item['type'] == 'inverters':
			# print('Active Inverters = ' + str(item['activeCount']))
			sendMetrics('solar_prod_activeInverterCount', item['activeCount'], item['readingTime'])
		if item['type'] ==  'eim' and item['measurementType'] == 'production':
			for prodMetric in prodMetrics:
				# print(prodMetric + ' = ' + str(item[prodMetric]))
				sendMetrics('solar_prod_'+ prodMetric, item[prodMetric], item['readingTime'])

	# print('**********')

	logger.info('Iterating consumption')
	for item in solarData['consumption']:
		if item['type'] == 'eim' and item['measurementType'] == 'total-consumption':
			for consumeMetric in consumeMetrics:
				# print(consumeMetric + ' = ' + str(item[consumeMetric]))
				sendMetrics('solar_consume_' + consumeMetric, item[consumeMetric], item['readingTime'])

if __name__ == '__main__':
	main()
	logger.info('Run complete')