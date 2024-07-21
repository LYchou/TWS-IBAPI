import threading
import pandas as pd
import time
from threading import Thread, Event
from ibapi.client import EClient
from ibapi.wrapper import EWrapper

class App(EWrapper, EClient):
    """
    The App class is a wrapper around the IB API EClient and EWrapper classes.
    It handles connection to TWS, order management, and data retrieval.
    """

    # Headers for the DataFrame containing open orders and order statuses
    header_openOrder = [
        'PermId', 'ClientId', 'OrderId', 'Status', 'Account', 'Symbol', 
        'SecType', 'LastTradeDateOrContractMonth', 'Strike', 'Right', 
        'Multiplier', 'Exchange', 'PrimaryExchange', 'Currency', 'Action', 
        'TotalQuantity', 'OrderType', 'LmtPrice', 'Tif'
    ]
    header_openOrderStatus = [
        'PermId', 'ClientId', 'OrderId', 'Status', 'Filled', 'Remaining', 
        'AvgFillPrice', 'LastFillPrice'
    ]

    def __init__(self):
        """
        Initializes the App instance, setting up events for synchronization and establishing connection parameters.
        """
        EClient.__init__(self, self)  # Initialize the EClient part of this instance
        
        # Initialize class attributes
        self.nextorderId = None  # Stores the next valid order ID from TWS
        self.openOrder_record = []  # List to hold open orders data
        self.orderStatus_record = []  # List to hold order status data
        
        # Events used to synchronize between the main thread and TWS callback responses
        self.first_nextValidId_ready = Event()
        self.nextValidId_ready = Event()  # Signals receipt of the next valid order ID
        self.reqAllOpenOrders_ready = Event()  # Signals receipt of all open orders
        self.lock = threading.Lock()  # Used for thread synchronization
        print('App instance initialized.')

    def start(self):
        """
        Starts the app by running the event loop in a separate thread and waits for the first valid order ID.
        """
        print('Run app.')
        thread = Thread(target=self.run)
        thread.start()
        print('Waiting for the response of the first valid Id.')
        self.first_nextValidId_ready.wait()

    def reqIds(self, numIds: int):
        """
        Requests the next available order ID from TWS.
        
        Parameters:
        - numIds (int): The number of IDs requested. Typically, 1 is used to get the next available ID.
        """
        super().reqIds(numIds)
        self.nextValidId_ready.clear()  # Reset the event in case this method is called multiple times
        print('Requesting next valid order ID.')

    def nextValidId(self, orderId: int):
        """
        Callback receiving the next valid order ID from TWS.
        
        Parameters:
        - orderId (int): The next valid order ID provided by TWS.
        """
        super().nextValidId(orderId)  # Call the base class method
        if not self.first_nextValidId_ready.is_set():
            self.first_nextValidId_ready.set()
            print(f'App has received the first valid order ID: {orderId}')
        else:
            with self.lock:
                self.nextorderId = orderId  # Update the next valid order ID
                self.nextValidId_ready.set()  # Signal that the next valid order ID has been received
                print(f'Next valid order ID received: {orderId}')

    def wait_for_nextValidId(self) -> int:
        """
        Requests the next valid order ID and waits until it's received.
        
        Returns:
            int: The next valid order ID.
        """
        self.reqIds(-1)
        self.nextValidId_ready.wait()
        return self.nextorderId
    
    def wait_for_reqAllOpenOrders(self):
        """
        Requests all open orders and waits until the response is received.
        """
        print('Requesting all open orders.')
        self.reqAllOpenOrders()
        self.reqAllOpenOrders_ready.wait()

    def openOrder(self, orderId, contract, order, orderState):
        """
        Callback for every order as it's returned by Interactive Brokers.
        
        Parameters:
        - orderId: The ID of the order.
        - contract: The contract details of the order.
        - order: The order details.
        - orderState: The state of the order.
        """
        super().openOrder(orderId, contract, order, orderState)
        content = [
            order.permId, order.clientId, orderId, orderState.status, order.account,
            contract.symbol, contract.secType, contract.lastTradeDateOrContractMonth,
            contract.strike, contract.right, contract.multiplier, contract.exchange,
            contract.primaryExchange, contract.currency, order.action, order.totalQuantity,
            order.orderType, order.lmtPrice, order.tif
        ]
        self.openOrder_record.append(content)
        print(f'openOrder: {content}')
    
    def orderStatus(self, orderId, status, filled, remaining, avgFillPrice, permId, parentId, lastFillPrice, clientId, whyHeld, mktCapPrice):
        """
        Callback providing the current status of an order.
        
        Parameters:
        - orderId: The ID of the order.
        - status: The current status of the order.
        - filled: The quantity filled.
        - remaining: The quantity remaining.
        - avgFillPrice: The average fill price.
        - permId: The permanent ID of the order.
        - parentId: The parent ID if applicable.
        - lastFillPrice: The price of the last fill.
        - clientId: The client ID.
        - whyHeld: Reason the order is being held.
        - mktCapPrice: Market cap price if applicable.
        """
        super().orderStatus(orderId, status, filled, remaining, avgFillPrice, permId, parentId, lastFillPrice, clientId, whyHeld, mktCapPrice)
        content = [
            permId, clientId, orderId, status, filled, remaining, avgFillPrice, lastFillPrice
        ]
        self.orderStatus_record.append(content)
        print(f'orderStatus: {content}')

    def openOrderEnd(self):
        """
        Indicates the end of the initial orders download.
        """
        super().openOrderEnd()
        timer = threading.Timer(0.5, self.reqAllOpenOrders_ready.set)
        timer.start()  # Starting the timer
        print('Requesting all open orders has been completed.')

    def error(self, reqId, errorCode, errorString, advancedOrderRejectJson=''):
        """
        Callback for errors returned by the API.
        
        Parameters:
        - reqId: ID of the request that caused the error.
        - errorCode: Numeric error code.
        - errorString: String error message.
        - advancedOrderRejectJson: JSON string with order rejection details if applicable.
        """
        if reqId != -1:
            print(f"Error received. ReqId: {reqId}, ErrorCode: {errorCode}, ErrorString: {errorString}")

    def stop(self):
        """
        Disconnects the client from TWS and performs cleanup operations.
        """
        print('Disconnecting from TWS.')
        self.disconnect()  # Disconnect from TWS
        time.sleep(0.5)  # Allow some time for disconnection cleanup

    def get_openOrder(self) -> pd.DataFrame:
        """
        Retrieves all open orders as a pandas DataFrame.
        
        Returns:
            pd.DataFrame: DataFrame containing details of all open orders.
        """
        df = pd.DataFrame(self.openOrder_record, columns=self.header_openOrder)
        return df

    def get_openOrderStatus(self) -> pd.DataFrame:
        """
        Retrieves the status of all open orders as a pandas DataFrame.
        
        Returns:
            pd.DataFrame: DataFrame containing status details of all open orders.
        """
        df = pd.DataFrame(self.orderStatus_record, columns=self.header_openOrderStatus)
        return df


if __name__ == '__main__':
    port = 7497  # TWS paper trading port
    clientId = 0  # Client ID for the connection

    app = App()
    app.connect('127.0.0.1', port, clientId)
    time.sleep(0.5)  # Allow some time for the connection to establish
    app.start()
    app.wait_for_reqAllOpenOrders()
    app.stop()

    # Retrieve and print open orders and order statuses
    openOrder = app.get_openOrder().drop_duplicates(ignore_index=True)
    openOrderStatus = app.get_openOrderStatus().drop_duplicates(ignore_index=True)

    print(openOrder)
    print(openOrderStatus)
