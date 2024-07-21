from ibapi.contract import Contract
from ibapi.order import Order
from ibapi.tag_value import TagValue

class InvalidAlgoError(Exception):
    """Custom exception for invalid algorithm input."""
    pass

class AlgoOrderFiller:

    def fill_algo_params(self, order: Order, algo: str) -> Order:
        # Validate algo parameter
        valid_algos = [
            '', 
            'PctVol', 'Adaptive', 'ArrivalPrice', 'ClosePrice', 'Midprice', 
            'DarkIce', 'AccumulateDistribute', 'TWAP', 'PriceVariantPctVol', 
            'SizeVariantPctVol', 'TimeVariantPctVol', 'VWAP', 'BalanceImpactRisk', 
            'MinimiseImpact'
        ]
        if algo not in valid_algos:
            raise InvalidAlgoError(f"Invalid algorithm specified: {algo}. Valid options are {valid_algos}")

        if algo == '':
            pass
        elif algo == 'Adaptive':
            order = self.FillAdaptiveParams(order)
        elif algo == 'PctVol':
            order = self.FillPctVolParams(order)
        elif algo == 'ArrivalPrice':
            order = self.FillArrivalPriceParams(order)
        elif algo == 'ClosePrice':
            order = self.FillClosePriceParams(order)
        elif algo == 'Midprice':
            order = self.FillMidpriceParams(order)
        elif algo == 'DarkIce':
            order = self.FillDarkIceParams(order)
        elif algo == 'AccumulateDistribute':
            order = self.FillAccumulateDistributeParams(order)
        elif algo == 'TWAP':
            order = self.FillTWAPParams(order)
        elif algo == 'PriceVariantPctVol':
            order = self.FillPriceVariantPctVolParams(order)
        elif algo == 'SizeVariantPctVol':
            order = self.FillSizeVariantPctVolParams(order)
        elif algo == 'TimeVariantPctVol':
            order = self.FillTimeVariantPctVolParams(order)
        elif algo == 'VWAP':
            order = self.FillVWAPParams(order)
        elif algo == 'BalanceImpactRisk':
            order = self.FillBalanceImpactRiskParams(order)
        elif algo == 'MinimiseImpact':
            order = self.FillMinimiseImpactParams(order)

        return order

    @staticmethod
    def FillAdaptiveParams(order: Order) -> Order:
        priority = 'Normal'
        order.algoStrategy = "Adaptive"
        order.algoParams = []
        order.algoParams.append(TagValue("adaptivePriority", priority))
        return order

    @staticmethod
    def FillPctVolParams(order: Order) -> Order:
        order.algoStrategy = 'PctVol'
        order.algoParams = []
        order.algoParams.append(TagValue("pctVol", 0.1))
        order.algoParams.append(TagValue("noTakeLiq", int(True)))
        return order

    @staticmethod
    def FillArrivalPriceParams(order: Order) -> Order:
        order.algoStrategy = 'ArrivalPx'
        order.algoParams = []
        order.algoParams.append(TagValue("maxPctVol", 0.1))
        order.algoParams.append(TagValue("riskAversion", "Medium"))
        return order

    @staticmethod
    def FillClosePriceParams(order: Order) -> Order:
        order.algoStrategy = 'ClosePx'
        order.algoParams = []
        order.algoParams.append(TagValue("startTime", "15:00:00 US/Eastern"))
        return order

    @staticmethod
    def FillMidpriceParams(order: Order) -> Order:
        order.algoStrategy = 'Midprice'
        order.algoParams = []
        order.algoParams.append(TagValue("midOffsetPct", 0.5))
        return order

    @staticmethod
    def FillDarkIceParams(order: Order) -> Order:
        order.algoStrategy = 'DarkIce'
        order.algoParams = []
        order.algoParams.append(TagValue("startTime", "09:30:00 US/Eastern"))
        order.algoParams.append(TagValue("endTime", "16:00:00 US/Eastern"))
        order.algoParams.append(TagValue("displaySize", 100))
        return order

    @staticmethod
    def FillAccumulateDistributeParams(order: Order) -> Order:
        order.algoStrategy = 'Accumulate/Distribute'
        order.algoParams = []
        order.algoParams.append(TagValue("maxPctVol", 0.2))
        return order

    @staticmethod
    def FillTWAPParams(order: Order) -> Order:
        order.algoStrategy = 'TWAP'
        order.algoParams = []
        order.algoParams.append(TagValue("startTime", "09:30:00 US/Eastern"))
        order.algoParams.append(TagValue("endTime", "16:00:00 US/Eastern"))
        return order

    @staticmethod
    def FillPriceVariantPctVolParams(order: Order) -> Order:
        order.algoStrategy = 'PctVol'
        order.algoParams = []
        order.algoParams.append(TagValue("priceVariant", "Yes"))
        return order

    @staticmethod
    def FillSizeVariantPctVolParams(order: Order) -> Order:
        order.algoStrategy = 'PctVol'
        order.algoParams = []
        order.algoParams.append(TagValue("sizeVariant", "Yes"))
        return order

    @staticmethod
    def FillTimeVariantPctVolParams(order: Order) -> Order:
        order.algoStrategy = 'PctVol'
        order.algoParams = []
        order.algoParams.append(TagValue("timeVariant", "Yes"))
        return order

    @staticmethod
    def FillVWAPParams(order: Order) -> Order:
        order.algoStrategy = 'VWAP'
        order.algoParams = []
        order.algoParams.append(TagValue("startTime", "09:30:00 US/Eastern"))
        order.algoParams.append(TagValue("endTime", "16:00:00 US/Eastern"))
        return order

    @staticmethod
    def FillBalanceImpactRiskParams(order: Order) -> Order:
        order.algoStrategy = 'BalanceImpactRisk'
        order.algoParams = []
        order.algoParams.append(TagValue("riskTolerance", "Low"))
        return order

    @staticmethod
    def FillMinimiseImpactParams(order: Order) -> Order:
        order.algoStrategy = 'MinimiseImpact'
        order.algoParams = []
        order.algoParams.append(TagValue("urgent", "Yes"))
        return order


if __name__=='__main__':

    ACCOUNT = 'YOUR ACCOUNT'
    ALGO = 'Adaptive'

    algoOrderFiller = AlgoOrderFiller()


    orderInfo_list = [
        {
            'Account': ACCOUNT,
            'Symbol': 'AAPL',
            'Action': 'BUY',
            'TotalQuantity': 10,
        },
        {
            'Account': ACCOUNT,
            'Symbol': 'TSLA',
            'Action': 'BUY',
            'TotalQuantity': 20,
        },
        {
            'Account': ACCOUNT,
            'Symbol': 'GOOG',
            'Action': 'SELL',
            'TotalQuantity': 30,
        },
    ]

    order_contract_pair_list = []
    for orderInfo in orderInfo_list:
        ORDERTYPE = 'Market'
        LMTPRICE = 0.0
        SECTYPE = 'STK'
        EXCHANGE = 'SMART'
        PRIMARYEXCHANGE = 'ARCA'

        contract = Contract()
        contract.symbol = orderInfo['Symbol']
        contract.secType = SECTYPE
        contract.currency = 'USD'
        contract.exchange = EXCHANGE
        contract.primaryExchange = PRIMARYEXCHANGE

        order = Order()
        order.account = orderInfo['Account']
        order.action = orderInfo['Action']
        order.totalQuantity = orderInfo['TotalQuantity']
        order.orderType = ORDERTYPE
        order.lmtPrice = LMTPRICE
        order = algoOrderFiller.fill_algo_params(order, ALGO)

        order_contract_pair_list.append((contract, order))