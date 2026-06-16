#!/home/alec/enphase-poller/venv/bin/python3

import requests
import json
import urllib3
import re
from dotenv import dotenv_values
import logging
import time

# Initialize logging
logging.Formatter.converter = time.gmtime
logging.basicConfig(filename='/home/alec/enphase-poller/enphase-bulk.log', level=logging.INFO, format='%(asctime)s.%(msecs)03dZ %(levelname)s : %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)

# Log something
logger.info('Starting poller')

# Load secrets
secrets = dotenv_values('/home/alec/enphase-poller/.env')

# Disable SSL warnings because the Enphase box has a self-signed cert
urllib3.disable_warnings()

# Initalize lists of the metrics we want to collect from the Enphase box. Metrics listed here will be sent to Grafana, this is a subset of metrics Enphase publishes.
prodMetrics = ['activeCount','wNow','whLifetime','varhLeadLifetime','varhLagLifetime','vahLifetime','rmsCurrent','rmsVoltage','reactPwr','apprntPwr','pwrFactor','whToday','whLastSevenDays', 'vahToday', 'varhLeadToday', 'varhLagToday']
consumeMetrics = ['activeCount','wNow','whLifetime','varhLeadLifetime','varhLagLifetime','vahLifetime','rmsCurrent','rmsVoltage','reactPwr','apprntPwr','pwrFactor','whToday','whLastSevenDays','vahToday','varhLeadToday','varhLagToday']

# Get metrics from Enphase box.
def getMetrics(metricEndpoint):
    logger.info('In GetMetrics')
    try:
        headers = {'Authorization' : 'Bearer ' + secrets['solarApiKey'], 'Accept' : 'application/json'}
        # print(headers)

        response = requests.get(secrets['baseURL'] + metricEndpoint, verify=False, headers=headers)

        if response.status_code != 200:
            logger.info('setMetrics bad response code: ' + response.status_code)
        # print(response.status_code)
        # print(response.json())
        logger.info('Leaving getMetrics')
        return(response.json())
    except Exception as err:
        logger.info('Exception in getMetrics: ' + str(err))

# Send metrics to Grafana
def sendMetrics(metricBatch):
    logger.info('In sendMetrics')
    try:
        logger.debug('Sending: ' + metricBatch)

        headers = {"Authorization": "Bearer " + secrets['grafanaMetricKey'], "Content-Type": "text/plain"}
        response = requests.post(secrets['grafanaMetricURL'], headers=headers, data=metricBatch)

        logger.debug('sendMetrics response code: ' + str(response.status_code))
        if response.status_code != 204:
            logger.info('sendMetrics bad response code: ' + str(response.status_code))
            logger.info('sendMetrics bad response: ' + str(response))
            logger.info('Unable to send: ' + metricBatch)
        return
    except Exception as err:
        print('Exception: ' + str(err))
        logger.info('Exception in sendMetrics: ' + str(err))

def main():
    logger.info('In Main')

    # Initialize the variable that holds the metrics we're sending
    metricBatch = ''

    # Query the Enphase box for production and consumption metrics
    solarData = getMetrics('/production.json')

    # Get the production metrics we're intereested in and append to metricBatch
    logger.info('Iterating production')
    for item in solarData['production']:
        if item['type'] == 'inverters':
            metricData = 'solar_prod' + ',location=' + secrets['siteID'] + ' ' + 'activeinvertercount=' + str(item['activeCount']) + ' ' + str(item['readingTime']) + '\n'
            metricBatch = metricBatch + metricData
        if item['type'] == 'eim' and item['measurementType'] == 'production':
            for prodMetric in prodMetrics:
                metricData = 'solar_prod' + ',location=' + secrets['siteID'] + ' ' + prodMetric.lower() + '='  + str(item[prodMetric]) + ' ' + str(item['readingTime']) + '\n'
                metricBatch = metricBatch + metricData

    # Get the consumption metrics we're interested in and append to metricBatch
    logger.info('Iterating consumption')
    for item in solarData['consumption']:
        if item['type'] == 'eim' and item['measurementType'] == 'total-consumption':
            for consumeMetric in consumeMetrics:
                # print(consumeMetric + ' = ' + str(item[consumeMetric]))
                metricData = 'solar_consume' + ',location=' + secrets['siteID'] + ' ' + consumeMetric.lower() + '=' + str(item[consumeMetric]) + ' ' + str(item['readingTime']) + '\n'
                metricBatch = metricBatch + metricData
    
    # Query the Enphase box for individual inverter production metrics
    inverterData = getMetrics('/api/v1/production/inverters')

    # Get the inverter metrics and append to metricBatch
    logger.info('Iterating inverters')
    for inverter in inverterData:
        # print(str(inverter['serialNumber']) + ' ' + str(inverter['lastReportWatts']) + ' ' + str(inverter['lastReportDate']))
        metricData = 'solar_prod_inverter' + ',location=' + secrets['siteID'] + ',serial_number=' + str(inverter['serialNumber']) + ' watts=' + str(inverter['lastReportWatts']) + ' ' + str(inverter['lastReportDate']) + '\n'
        metricBatch = metricBatch + metricData

    # print(metricBatch)
    # Send the metric batch to Grafana
    sendMetrics(metricBatch)

if __name__ == '__main__':
    main()
    logger.info('Run complete')
