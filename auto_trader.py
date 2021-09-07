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
from ibapi.order import Order
from ibapi.order_state import OrderState
from ibapi.execution import Execution

import strategies

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

NUM_PERIODS = 9
ORDER_QUANTITY = 1


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
    def __init__(self, contract, ticks_per_candle):
        EClient.__init__(self, self)
        self.contract = contract
        self.ticks_per_candle = ticks_per_candle
        self.nextValidOrderId = None
        self.started = False
        self.done = False
        self.position = 0
        self.strategy = strategies.WMA(NUM_PERIODS)
        self.last_signal = "NONE"
        self.pending_order = False
        self.tick_count = 0

    @iswrapper
    def nextValidId(self, orderId: int):
        super().nextValidId(orderId)

        logging.debug("setting nextValidOrderId: %d", orderId)
        self.nextValidOrderId = orderId
        print("NextValidId:", orderId)

        # we can start now
        self.start()

    def nextOrderId(self):
        oid = self.nextValidOrderId
        self.nextValidOrderId += 1
        return oid

    def start(self):
        if self.started:
            return
        self.started = True
        print("Executing requests")
        self.accountUpdateOperations()
        self.tickByTickDataOperations()
        print("Executing requests ... finished")

    def keyboardInterrupt(self):
        self.stop()
        self.done = True

    def stop(self):
        print("Executing cancels")
        self.tickByTickDataOperationsCancel()
        self.accountUpdateOperationsCancel()
        print("Executing cancels ... finished")

    def nextOrderId(self):
        oid = self.nextValidOrderId
        self.nextValidOrderId += 1
        return oid

    @iswrapper
    def error(self, reqId: TickerId, errorCode: int, errorString: str):
        super().error(reqId, errorCode, errorString)
        print("Error. Id:", reqId, "Code:", errorCode, "Msg:", errorString)

    def accountUpdateOperations(self):
        self.reqAccountUpdates(True, "")

    def accountUpdateOperationsCancel(self):
        self.reqAccountUpdates(False, "")

    def tickByTickDataOperations(self):
        self.reqTickByTickData(REQ_ID_TICK_BY_TICK_DATE, self.contract, "AllLast", 1, True)

    def tickByTickDataOperationsCancel(self):
        self.cancelTickByTickData(REQ_ID_TICK_BY_TICK_DATE)

    @iswrapper
    def updatePortfolio(self, contract: Contract, position: float,
                        marketPrice: float, marketValue: float,
                        averageCost: float, unrealizedPNL: float,
                        realizedPNL: float, accountName: str):
        print("UpdatePortfolio. ",
              "Contract:", contract,
              "Position:", position,
              "MarketPrice:", marketPrice,
              "MarketValue:", marketValue,
              "AverageCost:", averageCost,
              "UnrealizedPNL:", unrealizedPNL,
              "RealizedPNL:", realizedPNL,
              "AccountName:", accountName)
        if contract.symbol != self.contract.symbol:  # Only interested in position updates for our contract
            return
        self.position = position
        print(f"UpdatePortfolio. updated position for {contract.symbol} to {self.position}")

    @iswrapper
    def tickByTickAllLast(self, reqId: int, tickType: int, time: int, price: float,
                          size: int, tickAttribLast: TickAttribLast, exchange: str,
                          specialConditions: str):
        print("TickByTickAllLast. ",
              "Candle:", str(self.tick_count // self.ticks_per_candle + 1).zfill(3),
              "Period:", str(self.tick_count % self.ticks_per_candle + 1).zfill(3),
              "Time:", datetime.datetime.fromtimestamp(time).strftime("%Y%m%d %H:%M:%S"),
              "Price:", "{:.2f}".format(price),
              "Size:", size)
        if self.tick_count % self.ticks_per_candle == self.ticks_per_candle-1:
            self.strategy.update_signal(price)
            self.checkAndSendOrder()
        self.tick_count += 1

    @iswrapper
    def orderStatus(self, orderId: OrderId, status: str, filled: float,
                    remaining: float, avgFillPrice: float, permId: int,
                    parentId: int, lastFillPrice: float, clientId: int,
                    whyHeld: str, mktCapPrice: float):
        print("OrderStatus. ",
              "OrderId:", orderId,
              "Status:", status,
              "Filled:", filled,
              "Remaining:", remaining,
              "AvgFillPrice:", avgFillPrice,
              "PermId:", permId,
              "ParentId:", parentId,
              "LastFillPrice:", lastFillPrice,
              "ClientId:", clientId,
              "WhyHeld:", whyHeld,
              "MktCapPrice:", mktCapPrice)

    @iswrapper
    def openOrder(self, orderId: OrderId, contract: Contract, order: Order,
                  orderState: OrderState):
        print("OpenOrder. ",
              "OrderId:", orderId,
              "Contract:", contract,
              "Order:", order,
              "OrderState:", orderState)

    @iswrapper
    def execDetails(self, reqId: int, contract: Contract, execution: Execution):
        print("ExecDetails. ",
              "Contract:", contract,
              "Execution:", execution)
        if execution.cumQty == ORDER_QUANTITY:
            self.pending_order = False
            if execution.side == "BUY":
                self.position += execution.cumQty
            else:
                self.position -= execution.cumQty

    def checkAndSendOrder(self):
        print(f"Received {self.strategy.signal}")
        print(f"Last signal {self.last_signal}")

        if self.strategy.signal == "NONE" or self.strategy.signal == self.last_signal:
            print("Doing nothing")
            self.last_signal = self.strategy.signal
            return

        self.last_signal = self.strategy.signal

        if self.strategy.signal == "LONG":
            if self.position >= ORDER_QUANTITY:
                print(f"Already own {self.position} shares, doing nothing")
                return
            self.sendOrder("BUY")
        elif self.strategy.signal == "SHRT":
            if self.position < ORDER_QUANTITY:
                print(f"Current position is {self.position}. Don't want to go naked short, doing nothing")
                return
            self.sendOrder("SELL")
        else:
            print(f"Error. Received invalid signal {self.strategy.signal}")

    def sendOrder(self, action):
        if self.pending_order:
            print(f"Want to send a {action} order. But, there is a pending order out there already, doing nothing")
            return
        order = Order()
        order.action = action
        order.totalQuantity = ORDER_QUANTITY
        order.orderType = "MKT"
        self.pending_order = True
        self.placeOrder(self.nextOrderId(), self.contract, order)
        print(f"Sent a {order.action} order for {order.totalQuantity} shares")


def main():
    SetupLogger()
    logging.debug("now is %s", datetime.datetime.now())
    logging.getLogger().setLevel(logging.ERROR)

    cmd_line_parser = argparse.ArgumentParser("auto_trader.py")
    cmd_line_parser.add_argument("-s", "--symbol", action="store", type=str, required=True,
                                 dest="symbol", help="The symbol to use", choices=KNOWN_CONTRACTS.keys())
    cmd_line_parser.add_argument("-t", "--ticks_per_candle", action="store", type=int, required=True,
                                 dest="ticks_per_candle", help="Ticks per candle, typical values: 377, 1600")

    args = cmd_line_parser.parse_args()
    print("Using args", args)
    app = TestApp(KNOWN_CONTRACTS[args.symbol], args.ticks_per_candle)
    app.connect("127.0.0.1", 7497, 0)
    print("serverVersion:%s connectionTime:%s" % (app.serverVersion(),
                                                  app.twsConnectionTime()))
    app.run()


if __name__ == "__main__":
    main()
