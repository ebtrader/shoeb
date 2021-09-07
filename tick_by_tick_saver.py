#!/usr/local/bin/python3

import logging
import time
import os.path
import datetime
import argparse

from ibapi.utils import iswrapper
from ibapi.common import *

from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract

CONTRACT_ES = Contract()
CONTRACT_ES.symbol = "ES"
CONTRACT_ES.secType = "FUT"
CONTRACT_ES.exchange = "GLOBEX"
CONTRACT_ES.currency = "USD"
CONTRACT_ES.lastTradeDateOrContractMonth = "202009"

CONTRACT_NQ = Contract()
CONTRACT_NQ.symbol = "NQ"
CONTRACT_NQ.secType = "FUT"
CONTRACT_NQ.exchange = "GLOBEX"
CONTRACT_NQ.currency = "USD"
CONTRACT_NQ.lastTradeDateOrContractMonth = "202009"

CONTRACT_SPY = Contract()
CONTRACT_SPY.symbol = "SPY"
CONTRACT_SPY.secType = "STK"
CONTRACT_SPY.primaryExchange = "ARCA"
CONTRACT_SPY.exchange = "SMART"
CONTRACT_SPY.currency = "USD"

CONTRACT_QQQ = Contract()
CONTRACT_QQQ.symbol = "QQQ"
CONTRACT_QQQ.secType = "STK"
CONTRACT_QQQ.primaryExchange = "ARCA"
CONTRACT_QQQ.exchange = "SMART"
CONTRACT_QQQ.currency = "USD"

KNOWN_CONTRACTS = {
	"ES": CONTRACT_ES,
	"NQ": CONTRACT_NQ,
	"SPY": CONTRACT_SPY,
	"QQQ": CONTRACT_QQQ,
}

REQ_ID_TICK_BY_TICK_DATE = 1


def SetupLogger():
	if not os.path.exists("log"):
		os.makedirs("log")

	time.strftime("pyibapi.%Y%m%d_%H%M%S.log")

	recfmt = '(%(threadName)s) %(asctime)s.%(msecs)03d %(levelname)s %(filename)s:%(lineno)d %(message)s'

	timefmt = '%y%m%d_%H:%M:%S'

	# logging.basicConfig( level=logging.DEBUG,
	#                    format=recfmt, datefmt=timefmt)
	logging.basicConfig(filename=time.strftime("log/pyibapi.%y%m%d_%H%M%S.log"),
						filemode="w",
						level=logging.INFO,
						format=recfmt, datefmt=timefmt)
	logger = logging.getLogger()
	console = logging.StreamHandler()
	console.setLevel(logging.ERROR)
	logger.addHandler(console)


class TestApp(EWrapper, EClient):
	def __init__(self, contract):
		EClient.__init__(self, self)
		self.contract = contract
		self.nextValidOrderId = None
		self.started = False
		self.done = False
		today = datetime.date.today().strftime("%Y%m%d")
		file_path = f"data/ticks_{contract.symbol}_{today}.csv"
		if not os.path.exists("data"):
			os.makedirs("data")
		self.fd = open(file_path, "w")

	@iswrapper
	def nextValidId(self, orderId: int):
		super().nextValidId(orderId)

		logging.debug("setting nextValidOrderId: %d", orderId)
		self.nextValidOrderId = orderId
		print("NextValidId:", orderId)

		# we can start now
		self.start()

	def start(self):
		if self.started:
			return
		self.started = True
		print("Executing requests")
		self.tickByTickDataOperations()
		print("Executing requests ... finished")

	def keyboardInterrupt(self):
		self.stop()
		self.done = True

	def stop(self):
		print("Executing cancels")
		self.tickByTickDataOperationsCancel()
		print("Executing cancels ... finished")
		self.fd.close()

	@iswrapper
	def error(self, reqId: TickerId, errorCode: int, errorString: str):
		super().error(reqId, errorCode, errorString)
		print("Error. Id:", reqId, "Code:", errorCode, "Msg:", errorString)

	def tickByTickDataOperations(self):
		self.reqTickByTickData(REQ_ID_TICK_BY_TICK_DATE, self.contract, "AllLast", 1, True)

	def tickByTickDataOperationsCancel(self):
		self.cancelTickByTickData(REQ_ID_TICK_BY_TICK_DATE)

	@iswrapper
	def tickByTickAllLast(
		self, reqId: int, tickType: int, time: int, price: float,
		size: int, tickAttribLast: TickAttribLast, exchange: str,
		specialConditions: str):
		self.fd.write(f"{time},{tickType},{price},{size}\n")


def main():
	SetupLogger()
	logging.debug("now is %s", datetime.datetime.now())
	logging.getLogger().setLevel(logging.ERROR)

	cmd_line_parser = argparse.ArgumentParser("auto_trader.py")
	cmd_line_parser.add_argument(
		"-s", "--symbol", action="store", type=str, required=True,
		dest="symbol", help="The symbol to use", choices=KNOWN_CONTRACTS.keys())

	args = cmd_line_parser.parse_args()
	print("Using args", args)
	app = TestApp(KNOWN_CONTRACTS[args.symbol])
	app.connect("127.0.0.1", 7497, 0)
	print("serverVersion:%s connectionTime:%s" % (app.serverVersion(), app.twsConnectionTime()))
	app.run()


if __name__ == "__main__":
	main()
