
# %%
from typing import List
import os
import json

import requests
import pandas as pd
from pandas import Series, DataFrame

# %%

DF = DataFrame
ROOT = "https://api.microprediction.org"
WRITE_KEY = None
KEYS_FILE = os.getenv('HOME') + '/stream_keys.json'
# %%


def main():
    # %%
    global WRITE_KEY
    # %%
    volumes_ = volumes()
    # %%
    stream_name = 'cck-btc-cop-10m-ret.json'
    # %%
    stream_15min = '910::' + stream_name
    stream_1min = '70::' + stream_name
    # %%
    # stream_name = "70::z1~cck-btc-cop-10m-ret~70"
    stream_name = 'z1~cck-btc-cop~70'
    # %%
    WRITE_KEY = _get_write_key( stream_name, KEYS_FILE)
    # %%
    l0 = lagged( stream_name)
    # %%
    l1 = lagged( stream_1min )
    # %%
    l15 = lagged( stream_15min )
    # %%
    l15.shape
    # %%
    volumes_[ volumes_.stream.str.contains('electricity') ]
    # %%
    stream_name = '70::electricity-load-nyiso-dunwod.json'
    # %%
    l15 = lagged('70::electricity-load-nyiso-dunwod.json')
    # %%
    cdf( "cck-btc-cop-10m-ret.json" )
    # %%
    sps = sponsors()
    # %%
    streams = sps['Offcast Goose']
    # %%
    vals_dic = {}
    for stream in streams:
        print( stream )
        vals = lagged( stream )
        if len(vals) > 0:
            vals_dic[stream] = vals
    # %%
    from pprint import pprint
    pprint( { stream: len(vals) for stream, vals in vals_dic.items()})
    # %%
    vals
    # %%

    # %%


def _interactive_testing():
    # %%
    # noinspection PyUnresolvedReferences
    runfile("micropred/mp_utils.py")
    # %%


def cdf( stream_name: str, values: List[float] = None, delay: int = 70 ) -> DF:
    if values is None:
        values = [-0.010, -0.001, 0, 0.001, 0.01, 0.05]

    values_str = ",".join( str(val) for val in values )
    resp = requests.get( ROOT + f"/cdf/{stream_name}?delay={delay}&values={values_str}" )
    resp_js = resp.json()
    result = DF( resp_js )
    result.rename( columns={'x': 'value', 'y': 'cdf'}, inplace=True)
    return result
    # %%


def _get_write_key(stream_name: str, keys_file: str) -> str:
    with open(keys_file) as f_in:
        obj = json.load(f_in)
        return obj[stream_name]


def volumes() -> DF:
    """Listing of streams by volumes? Volumes of what?"""
    # %%
    resp = requests.get( ROOT + "/volumes/" ).json()
    result = Series( resp ).reset_index()

    result.columns = ['stream', 'volume']
    # %%
    return result
    # %%


def budgets() -> Series:
    """Return a series with keys being streams and values being budgets"""
    resp = requests.get( ROOT + "/budgets/" ).json()
    return Series( resp )


def sponsors() -> Series:
    """Return a series with key being sponsor and value being a list of streams by that sponsor"""
    # %%
    resp = requests.get( ROOT + "/sponsors/" ).json()
    df = Series( resp ).reset_index()
    df.columns = ['stream', 'sponsor']
    # cols = ['sponsor', 'stream']
    grped = df.groupby('sponsor').apply( lambda grp:  sorted(list( grp['stream'])) )
    # %%
    return grped


def active_submissions( write_key: str ) -> List[str]:
    """Return active submissions for all streams"""
    resp = requests.get( ROOT + f"/active/{write_key}" ).json()
    return resp
    # %%


def lagged( stream_name: str, count: int=1000 ) -> List[str]:
    """Return lagged values """
    # %%
    url = ROOT + f"/lagged/{stream_name}?count={count}"
    resp = requests.get( url )
    if len(resp.json()) == 0:
        print( f'No points retrieved from {url} ({resp})')
    # %%
    result = DF( resp.json(), columns=['epoch_time', 'value'])
    result['tstamp_utc'] = pd.to_datetime( result['epoch_time'], unit='s' )
    # %%
    return result
    # %%


bgets = budgets()
# %%
