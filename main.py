from dataclasses import dataclass
from typing import Dict, List
from utils import logger
from threading import Thread, Event
from web3 import Web3
from models import *

import datetime
import os
import signal
import time
import json
import numpy as np
import requests

# this is to prevent hard shutdowns where the process is interrupted halfway through etc.
quit_event = Event()
signal.signal(signal.SIGINT, lambda *_args: quit_event.set())

# will change to some fancy environment or settings thing later.
DEFAULT_ETH_ADDRESS = "0x0000000000000000000000000000000000000000"
NUM_REQUESTS = int(os.environ["NUM_REQUESTS"])
HITS = int(os.environ["HITS"])
DELAY = int(os.environ["DELAY"])
MEASURED_LATENCIES = json.loads(os.environ["MEASURED_LATENCIES"])
ROUND_DELAY = 21600

headers = {
    # Already added when you pass json= but not when you pass data=
    # 'Content-Type': 'application/json',
}

request_payload = {
    'jsonrpc': '2.0',
    'method': 'eth_getBalance',
    'params': [
        DEFAULT_ETH_ADDRESS,
        'latest',
    ],
    'id': 1,
}

def send_request(url: str):
    try:
        start = time.time()
        response = requests.post(url, headers=headers, timeout=2, json=request_payload)
        end = time.time()
        return end-start
    except:
        return 0

# allows threading functions to give return values.
class Request(Thread):
    def __init__(self, group=None, target=None, name=None,
                 args=(), kwargs={}, Verbose=None):
        Thread.__init__(self, group, target, name, args, kwargs)
        self._return = None
    def run(self):
        if self._target is not None:
            self._return = self._target(*self._args,
                                                **self._kwargs)
    def join(self, *args):
        Thread.join(self, *args)
        return self._return

def main_loop():
    while True:
        with db.atomic():
            timestamp = datetime.datetime.now()

            logger.info(f"Starting new round of requests. Timestamp: {timestamp}, Num_requests: {NUM_REQUESTS}, Delay: {DELAY}, Hits: {HITS}, Measured_latencies: {MEASURED_LATENCIES}")

            # currently we don't need regional support
            # for provider in Provider.select().where(Provider.region==Region.select().where(Region.name==os.environ["REGION"])[0]): 

            for provider in Provider.select():
                logger.info(f"Starting new round of requests for provider {provider.name}")
                w3 = Web3(Web3.HTTPProvider(provider.url))

                # create application session
                w3.eth.block_number
                balance_times = np.array([])
                # how many times to smash the web3 provider ;).

                for i in range(HITS):

                    latencies = np.array([])
                    threads = []
                    for i in range(NUM_REQUESTS):
                        t = Request(target=send_request, args=[provider.url])
                        t.start()
                        threads.append(t)

                    for t in threads:
                        latencies = np.append(latencies, t.join())
                    balance_times = np.concatenate([balance_times, latencies])

                    time.sleep(DELAY)

                pxxDict: Dict[str, float] = dict()
                for pxx in MEASURED_LATENCIES:
                    key = f"p{pxx}"
                    pxxDict[key] = (
                        np.percentile(balance_times, pxx)
                    )
                mean = (
                    np.mean(balance_times)
                )
                benchmark = Benchmark.create(
                    provider=provider,
                    timestamp=timestamp,
                    p25=pxxDict["p25"],
                    p50=pxxDict["p50"],
                    p75=pxxDict["p75"],
                    p90=pxxDict["p90"],
                    p99=pxxDict["p99"],
                    mean=mean,
                    region=Region.select().where(Region.name==os.environ["REGION"])[0]
                )
                logger.info(f"Finished benchmark for provider {provider.name}, results: {pxxDict}, raw results: {balance_times}")
        time.sleep(ROUND_DELAY)
        if quit_event.is_set():
            logger.info("Received SIGINT, quitting.")
            break

if __name__ == '__main__':
    logger.info("Starting main loop")
    main_loop()
