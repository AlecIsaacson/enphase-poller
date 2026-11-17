# Enphase Poller

Polls my Enphase solar controller API and send data to Grafana Cloud for visualization.

Files are as follows:

**enphase-poll.py** - Original release. Polls metrics from Enphase gateway and sends each metric to Grafana when it's polled, which is inefficient.  
**enphase-bulk.py** - Updated release, identical polling logic, but batch sends metrics to Grafana. Much more efficient.  
**enphase-inventory.py** - Gathers inventory information from the gateway (i.e. serial numbers, software versions, etc). 
**\*.json and \*.xml** - Example output from the APIs.  

Run the bulk poller every few minutes to capture solar array KPIs.  The inventory can be run daily or so to capture changes to the gateway which might break the APIs.
