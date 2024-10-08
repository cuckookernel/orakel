
import logging as log
import os
import sys

import dotenv
import numpy as np
from microprediction import MicroCrawler
from numpy import random
from sklearn.linear_model import LinearRegression
from statsmodels.tsa.arima.model import ARIMA

dotenv.load(os.getenv('HOME') + '/micropred.env')
# %%


class _Config:
    write_key = os.getenv('TACTABLE_TOAD_KEY')
    min_lags = 12 * 24 * 3


assert _Config.write_key is not None

# log.basicConfig(filename='publish_btc_cop.log', level=log.INFO)
log.basicConfig(stream=sys.stderr, level=log.INFO)


class FTCrawlerV0(MicroCrawler):

    def __init__(self, **kwargs):
        self.names = []
        self.horizon_i = 0
        # self.horizons = ["310", "910", "3555"]
        self.horizons = ["310"]

        super().__init__(**kwargs)

        self.nf = 20  # num
        N = self.min_lags

        i = np.linspace(0, N - 1, N + 12)
        self.feats = np.array(  [ np.cos( 2 * np.pi * k * i / N ) for k in range(self.nf+1) ]
                              + [ np.sin( 2 * np.pi * k * i / N )
                                  for k in range(-self.nf, self.nf + 1) if k != 0 ]
                              + [ i ] ).transpose()

        self.lr = LinearRegression()
        # print( self.names )

    def include_stream(self, name=None, **ignore):
        """Whether to include a stream in predictions"""
        include = name.startswith('electricity-load-')
        if include:
            # print(f"INCLUDED: {name}")
            if name not in self.names:
                self.names.append(name)
                print(f'names has {len(self.names)}')

        # if not include and 'electricity-load-' in name:
        #    print( "not included:", name )

        return include

    def next_horizon(self, exclude=None):
        """Produce a next horizon by cycling jointly through self.horizons self.names"""
        self.horizon_i += 1
        name_i = self.horizon_i // 3
        next_name = self.names[name_i % len(self.names)]
        horizon = self.horizons[self.horizon_i % len(self.horizons)]
        return f"{horizon}::{next_name}"

    # def exclude_delay(self, delay, name=None, **ignore):
    #     return delay > 50000  # Lower this to have any effect

    def sample(self, lagged_values, lagged_times=None, name=None, delay=None, **ignored):
        """Must return a list of 225 numbers
        In this example we use the empirical distribution of changes
        We add in some singletons to capture (to some extent) the under-sampled possibilities
        """
        lagged_values, lagged_times = self.get_lagged_values_and_times( name )

        n_values = len(lagged_values)
        print( f"name={name} n_values: {n_values}\ntype(lagged_values)={type(lagged_values)}\n "
               f"delay={delay} "
               f"lagged_times[0]={lagged_times[0]:.2f} lagged_times[-1]={lagged_times[-1]:.2f}\n"
               f"time_span = {lagged_times[-1] - lagged_times[0]:.2f} "
               f"lagged_values[0]={lagged_values[0]:.2f}" )

        N = self.min_lags
        past_truth = lagged_values[:N][-1::-1]
        self.lr.fit(self.feats[:N, :], past_truth)

        past_preds = self.lr.predict(self.feats[:N])
        stdev = _l2_error(past_preds, past_truth)

        if delay == 310:
            pred, stdev = self._predict_310( name, delay, past_truth, past_preds,
                                             last_time=lagged_times[-1] )
        elif delay == 910:
            pred = self.lr.predict(self.feats[[N + 2], :])
        elif delay == 3555:
            pred = self.lr.predict(self.feats[[N + 11], :])
        else:
            raise ValueError( 'Invalid value for delay={delay}')

        result = random.normal( pred, stdev, size=225 )

        return sorted(result)

    def _predict_310(self, name, delay, past_truth, past_preds, last_time):

        print(f"past error: l1: {_l1_error(past_preds, past_truth)} "
              f"l2: {_l2_error(past_preds, past_truth)}")

        pred0 = self.lr.predict(self.feats[[self.min_lags], :])
        err = past_truth - past_preds
        arima = ARIMA(err, order=(2, 0, 1))
        model_fit = arima.fit()
        past_err_preds = model_fit.predict()
        err_preds = model_fit.predict(start=len(err), end=len(err) + 3)
        stdev = _l2_error(past_preds + past_err_preds, past_truth)
        pred = pred0 + err_preds[0]

        print(f'{name} prediction for: t={ last_time + delay}: {pred},\n'
              f'err_preds has {len(err_preds)}: past_err_preds[-1]={past_err_preds[-1]:.2f} '
              # f'err_preds={err_preds}\n'
              f'stdev={stdev:.2f}')

        return pred, stdev


def _l1_error( preds: np.array, truth: np.array ) -> float:
    return float(np.mean( np.abs(preds - truth) ))


def _l2_error( preds: np.array, truth: np.array ) -> float:
    diff = preds - truth
    return np.sqrt( np.mean( diff * diff ) )
    # %%


def _interactive_testing():
    # %%
    # noinspection PyUnresolvedReferences
    runfile("prediction/electricity/v0.py")
    # %%
    # %%
    from microprediction.reader import MicroReader
    reader = MicroReader()
    # %%
    lagged = reader.get_lagged('electricity-load-nyiso-overall.json')
    # %%

log.info('Publishing starts')

if __name__ == '__main__':
    crawler = FTCrawlerV0(write_key=_Config.write_key,
                          min_lags=_Config.min_lags)
    crawler.run()
