#!/usr/bin/python

import ccxt
import time
import MySQLdb as sql
import logging
import datetime
import smtplib
import sys
import config


class Connection:
    def __init__(self):
        # connect to database using MySQLdb and SQLalchemy
        self.db = sql.connect(host=config.DATABASE_CONFIG['host'],
                              user=config.DATABASE_CONFIG['user'],
                              passwd=config.DATABASE_CONFIG['password'],
                              db=config.DATABASE_CONFIG['dbname'],
                              port=config.DATABASE_CONFIG['port'],
                              charset='utf8')
        self.c = self.db.cursor()


class Exchange:
    def __init__(self, name):
        self.name = name
        self.is_live = False
        self.data = {}
        try:
            func = getattr(ccxt, config.EXCHANGES[config.EXCHANGES.index(name)])
            self.exch = func()
            self.exch.options['fetchOHLCVWarning'] = False
            self.exch.loadMarkets()
        except AttributeError:
            logging.error("Error instantiating exchange " + name + " on ccxt")

    def minute_transfer(self, coin):
        try:
            # symbols = exchange.symbols
            if self.exch.has['fetchOHLCV']:  # this checks for open, high, low, close, volume data
                time.sleep(self.exch.rateLimit / 1000)  # sleep to prevent over requesting the exchange
                if self.exch.markets and (coin + '/USD') in self.exch.markets:
                    data_t = (self.exch.fetch_ohlcv(coin + '/USD', '1m', 1)[-1])  # get minute data for the coin
                    # format time
                    timew = datetime.datetime.fromtimestamp((data_t[0] / 1000)).strftime('%Y-%m-%d %H:%M:%S.%f')

                    self.data[coin] = {'open_price': data_t[1], 'high_price': data_t[2], 'low_price': data_t[3],
                                       'close_price': data_t[4], 'volume': data_t[5], 'times': timew}

                    self.is_live = True  # the exchange is online

        except ConnectionError:  # except in case of error to keep script running
            logging.critical('Error fetching data for ' + coin + ' : ' + str(sys.exc_info()))  # reason for failure
            time.sleep(5)  # sleep
            try:
                Email.send_mail(Email(), 'Data fetch fail', str(sys.exc_info()))  # try to send mail saying it failed
            except smtplib.SMTPException:
                logging.error('Error sending email with info: ', str(sys.exc_info()))  # catch if can't email


class Token:
    def __init__(self, name):
        self.name = name


class Email:
    def __init__(self):
        # set password and email address to have emails sent to throw away email address
        self.address = config.EMAIL_CONFIG['address']
        self.password = config.EMAIL_CONFIG['password']

    def send_mail(self, subject, msg):
        try:
            server = smtplib.SMTP('smtp.gmail.com:587')
            server.ehlo()
            server.starttls()
            server.login(self.address, self.password)
            message = 'Subject: {}{}'.format(subject, msg)
            server.sendmail(self.address, self.address, message)
            server.quit()
            logging.info("Success sending email: " + subject)
        except smtplib.SMTPException:
            logging.error("Failure sending email")


def main():
    # set logging level
    logging.basicConfig(filename='log.txt', level=logging.INFO)
    conn = Connection()
    exchanges = {}
    # number of live exchanges
    live_num = {}
    open_price = {}
    high_price = {}
    low_price = {}
    close_price = {}
    volume = {}

    for x in range(len(config.EXCHANGES)):
        try:
            exch = Exchange(config.EXCHANGES[x])
            exchanges[config.EXCHANGES[x]] = exch
            exchange_table = ("CREATE TABLE IF NOT EXISTS exchange_" + exch.name +
                              """ (token varchar(15),
                              open decimal(12,6),
                              high decimal(12,6),
                              low decimal(12,6),
                              close decimal(12,6),
                              volume decimal(20,6),
                              time datetime )""")
            conn.c.execute(exchange_table)
            for t in config.TOKENS:
                try:
                    if not open_price.get(t, 0):
                        open_price[t] = 0
                    if not high_price.get(t, 0):
                        high_price[t] = 0
                    if not low_price.get(t, 0):
                        low_price[t] = 0
                    if not close_price.get(t, 0):
                        close_price[t] = 0
                    if not volume.get(t, 0):
                        volume[t] = 0
                    if not live_num.get(t, 0):
                        live_num[t] = 0
                    exch.minute_transfer(t)
                    timestamp = datetime.datetime.now()
                    if exch.is_live and exch.data.get(t, {}):

                        """ first insert price for the token into the particular exchange table"""
                        conn.c.execute("INSERT IGNORE INTO exchange_" + exch.name +
                                       """ (token, open, high, low, close, volume, time)
                                       VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                                       (t,
                                        exch.data[t]['open_price'],
                                        exch.data[t]['high_price'],
                                        exch.data[t]['low_price'],
                                        exch.data[t]['close_price'],
                                        exch.data[t]['volume'],
                                        timestamp))
                        conn.db.commit()

                        """ add price values to get average on all exchanges later for particular token"""
                        open_price[t] += exch.data[t]['open_price']
                        high_price[t] += exch.data[t]['high_price']
                        low_price[t] += exch.data[t]['low_price']
                        close_price[t] += exch.data[t]['close_price']
                        volume[t] += exch.data[t]['volume']
                        live_num[t] += 1
                except ConnectionError:
                    logging.error("Error fetching transfer for  " + t + " for " + config.EXCHANGES[x])
        except ConnectionError:
            logging.error("Error instantiating exchange " + config.EXCHANGES[x] + " on ccxt")
    for t in config.TOKENS:
        if live_num[t] == 0:
            logging.info("No live exchanges for the token " + t + " found")
            continue
        try:
            op = round(open_price[t]/live_num[t], 6)
            hp = round(high_price[t]/live_num[t], 6)
            lp = round(low_price[t]/live_num[t], 6)
            cp = round(close_price[t]/live_num[t], 6)
            vol = round(volume[t]/live_num[t], 6)
            timestamp = datetime.datetime.now()

            create = ("CREATE TABLE IF NOT EXISTS " + str(t) +
                      """ (open decimal(12,6),
                      high decimal(12,6),
                      low decimal(12,6),
                      close decimal(12,6),
                      volume decimal(20,6),
                      time datetime )""")

            conn.c.execute(create)
            conn.c.execute("INSERT IGNORE INTO " + str(t) +
                           """ (open, high, low, close, volume, time) VALUES (%s, %s, %s, %s, %s, %s)""",
                           (op, hp, lp, cp, vol, timestamp))
            conn.db.commit()
        except ConnectionError:
            logging.error("Error inserting prices row for " + t)
    conn.c.close()
    conn.db.close()

main()





