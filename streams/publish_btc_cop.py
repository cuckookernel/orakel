"""Publish btc cop every 10 minutes as given by
https://www.buda.com/api/v2/markets/btc-cop/ticker
"""

import json
import logging as log
import os
from typing import Optional

import requests
from microprediction.polling import MicroPoll

log.basicConfig(filename='publish_btc_cop.log', level=log.INFO)
# log.basicConfig(stream=sys.stderr, level=log.INFO)
log.info('Publishing starts')


class _Config:
    keys_file = os.getenv('HOME') + '/stream_keys.json'
    stream_name = 'cck-btc-cop-10m-ret.json'
    ticker_url = 'https://www.buda.com/api/v2/markets/btc-cop/ticker'
    interval = 10  # minutes
    key_server_url = 'http://localhost:8000/key?client_name=cck-btc-cop&difficulty=9'


CFG = _Config

# %%


class MicroPollV2( MicroPoll ):
    """Version of Micropoll that fetches keys from a key server"""

    def maybe_bolster_balance_by_mining(self):
        balance = self.get_balance()
        log.info(f'at the start, balance: {balance}')

        if balance < 0:
            response_js = requests.get(CFG.key_server_url).json()
            key = response_js['key']
            difficulty = response_js['difficulty']
            log.info(f"Got key of difficulty {difficulty} from server")
            self.put_balance(source_write_key=key)
            balance = self.get_balance()
            log.info(f'at the end, balance: {balance}')


def main():
    """Get key, instantiate feed, run it"""
    write_key = _get_write_key( CFG.stream_name, CFG.keys_file )
    assert write_key, f"Failed getting key for `{CFG.stream_name}` from file: {CFG.keys_file}"

    price_getter = PriceGetter()

    feed = MicroPollV2( name=CFG.stream_name,
                        write_key=write_key,
                        func=price_getter.get_return,
                        interval=CFG.interval)

    feed.run()


class PriceGetter:
    def __init__(self):
        self.prev_price = None

    def get_return(self) -> Optional[float]:
        """Query ticker url return last price"""
        last_price = None
        try:
            response = requests.get(CFG.ticker_url)
            last_price = float( response.json()['ticker']['last_price'][0] )
            if self.prev_price is not None:
                return_ = (last_price - self.prev_price) / self.prev_price
            else:
                return_ = None

            self.prev_price = last_price
            return return_

        except Exception as exc:
            log.warning( f"Exception getting ticker:\n{exc}\n{response.json()}\n"
                         f"last_price={last_price}" )
            self.prev_price = None

        return None


def _get_write_key( stream_name: str, keys_file: str) -> str:
    with open( keys_file ) as f_in:
        obj = json.load(f_in)
        return obj[stream_name]


if __name__ == "__main__":
    main()
