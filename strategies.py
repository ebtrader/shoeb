from collections import deque


class WMA:
    def __init__(self, periods: int):
        self.periods = periods
        self.period_sum = periods * (periods+1) // 2
        self.n = 0
        self.dq = deque()
        self.wma = 0
        self.signal = "NONE"

    def calc_wma(self):
        weight = 1
        wma_total = 0
        for price in self.dq:
            wma_total += price * weight
            weight += 1
        self.wma = wma_total / self.period_sum
        self.dq.popleft()

    def update_signal(self, price: float):
        self.dq.append(price)
        self.n += 1
        if self.n < self.periods:
            return
        prev_wma = self.wma
        self.calc_wma()
        if prev_wma != 0:
            if self.wma > prev_wma:
                self.signal = "LONG"
            elif self.wma < prev_wma:
                self.signal = "SHRT"
