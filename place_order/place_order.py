# Import necessary libraries and modules for threading, logging, and interacting with the Interactive Brokers API
import threading
import time
from threading import Thread, Event
from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
from ibapi.order import Order

from algotrade import AlgoOrderFiller

class App(EWrapper, EClient):
    """
    Main application class for interacting with the Interactive Brokers API.
    Inherits from EWrapper and EClient to handle API events and client requests.
    """

    def __init__(self, order_contract_pair_list: list):
        """
        Initialize the App with a list of order-contract pairs and set up threading events and synchronization mechanisms.
        
        Parameters:
        - order_contract_pair_list (list): List of tuples containing (Contract, Order) pairs.
        """
        EClient.__init__(self, self)
        self.order_contract_pair_list = order_contract_pair_list
        self.nextorderId = None  # To store the next valid order ID from TWS
        # Events used to synchronize between the main thread and TWS callback responses
        self.first_nextValidId_ready = Event()
        self.nextValidId_ready = Event()  # Signals receipt of the next valid order ID
        self.lock = threading.Lock()  # Used for thread synchronization, particularly when accessing shared resources

    def start(self):
        """Start the application by running it in a separate thread and waiting for the first valid order ID."""
        thread = Thread(target=self.run)
        thread.start()
        self.first_nextValidId_ready.wait()

    def reqIds(self, numIds: int):
        """
        Requests the next available order ID from TWS. This method overrides EClient.reqIds.
        
        Parameters:
        - numIds (int): The number of IDs requested. Typically, 1 is used to get the next available ID.
        """
        super().reqIds(numIds)
        self.nextValidId_ready.clear()  # Reset the event in case this method is called multiple times

    def nextValidId(self, orderId: int):
        """
        Callback receiving the next valid order ID from TWS.

        Parameters:
        - orderId (int): The next valid order ID provided by TWS.
        """
        super().nextValidId(orderId)  # Call the base class method

        # The first time this method is called signifies a successful connection
        if not self.first_nextValidId_ready.is_set():
            self.first_nextValidId_ready.set()
            print(f'App has received the first valid orderId: {orderId}')
        else:
            with self.lock:
                self.nextorderId = orderId  # Update the next valid order ID
                self.nextValidId_ready.set()  # Signal that the next valid order ID has been received
                print(f'Next valid order ID received: {orderId}')

    def wait_for_nextValidId(self) -> int:
        """Requests the next valid order ID and waits until it's received."""
        self.reqIds(-1)
        self.nextValidId_ready.wait()
        return self.nextorderId
    
    def place_orders(self):
        """Places all orders in the order_contract_pair_list."""
        print(f'There are {len(self.order_contract_pair_list)} orders need to be placed.')
        
        # Process each trade order in the list
        for i, order_contract_pair in enumerate(self.order_contract_pair_list):
            # Place each individual order
            nextorderId = self.wait_for_nextValidId()
            contract, order = order_contract_pair
            order.clientId = self.clientId
            order.orderId = nextorderId
            print(f"({i+1}) ClientId: {order.clientId}, OrderId: {nextorderId}, Account: {order.account}, Symbol: {contract.symbol}, SecType: {contract.secType}, Action: {order.action}, TotalQuantity: {order.totalQuantity}")
            self.placeOrder(nextorderId, contract, order)

    def error(self, reqId, errorCode, errorString, advancedOrderRejectJson=''):
        """
        Callback for handling errors received from TWS.

        Parameters:
        - reqId (int): The request ID that generated the error.
        - errorCode (int): The error code.
        - errorString (str): The error message.
        - advancedOrderRejectJson (str, optional): JSON string with additional order rejection information.
        """
        if reqId != -1:
            print(f"Error received. ReqId: {reqId}, ErrorCode: {errorCode}, ErrorString: {errorString}")

    def stop(self):
        """Disconnect from TWS and allow time for cleanup."""
        self.disconnect()
        time.sleep(0.5)

def get_orders() -> list:
    """
    Generate a list of order-contract pairs based on predefined order information.

    Returns:
    - list: List of tuples containing (Contract, Order) pairs.
    """
    # Example order data
    ACCOUNT = 'YOUR ACCOUNT'
    ALGO = ''

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

    return order_contract_pair_list

if __name__ == '__main__':
    port = 7497
    clientId = 0

    app = App(get_orders())
    app.connect('127.0.0.1', port, clientId)
    time.sleep(0.5)
    app.start()
    app.place_orders()
    app.stop()
