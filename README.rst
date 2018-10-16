PredictionVC Exchanges Data Information
==========================================

The scraper.py currently pulls data from exchanges globally, averages it,
then sends it to MySQL database.

Exchanges currently covered:
bitstamp
kraken
bitfinex
binance
bitmex
coinbase
coincheck
kucoin
poloniex

Tokens currently covered:
BTC
ETH
BCH
XRP
EOS
XLM
LTC
USDT
ADA
XMR
MIOTA
DASH
BNB
NEO
ETC
XEM
XTZ
VET
DOGE
ZEC
MKR
BTG
OMG
ZRX
ONT
DCR
QTUM
LSK
BCN

Ways to improve and expand:
    1) Including more top volume cryptocurrencies (right now the number is 29)
    2) Make this a multi-threaded script, to improve performance as it is meant to run every minute
    3) Error handling and logging should be done more thoroughly, for the cases where the exchange is down
        or it stopped supporting certain trading pairs etc.


-------------------------------------------

If you want to learn more about ``setup.py`` files, check out `this repository <https://github.com/kennethreitz/setup.py>`_.

✨🍰✨
