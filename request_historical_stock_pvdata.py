import threading
import time
import pandas as pd
from threading import Thread, Event
from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
from ibapi.common import TickerId

class App(EWrapper, EClient):
    """
    IB API application class that handles connection, order IDs, and historical data requests.
    Inherits from EWrapper and EClient.
    """

    def __init__(self):
        """
        Initializes the App instance by setting up threading events and synchronization primitives.
        """
        EClient.__init__(self, self)  # Initialize the EClient part of this instance
        self.nextorderId = None  # To store the next valid order ID
        self.first_nextValidId_ready = Event()  # Event to signal the first valid order ID is received
        self.nextValidId_ready = Event()  # Event to signal the next valid order ID is received
        self.lock = threading.Lock()  # Lock for synchronizing access to nextorderId
        self.historical_data_ready = Event()  # Event to signal when historical data is fully received
        print('App instance initialized.')

    def start(self):
        """
        Starts the app by running the EClient in a separate thread.
        Waits for the first valid order ID before proceeding.
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
        - numIds (int): Number of IDs to request.
        """
        super().reqIds(numIds)
        self.nextValidId_ready.clear()  # Clear event before requesting
        print('Requesting next valid order ID.')

    def nextValidId(self, orderId: int):
        """
        Callback for receiving the next valid order ID from TWS.

        Parameters:
        - orderId (int): The next valid order ID.
        """
        super().nextValidId(orderId)
        if not self.first_nextValidId_ready.is_set():
            self.first_nextValidId_ready.set()
            print(f'App has received the first valid orderId: {orderId}')
        else:
            with self.lock:
                self.nextorderId = orderId
                self.nextValidId_ready.set()
                print(f'Next valid order ID received: {orderId}')

    def wait_for_nextValidId(self) -> int:
        """
        Requests the next valid order ID and waits until it's received.

        Returns:
        - int: The next valid order ID.
        """
        self.reqIds(-1)
        self.nextValidId_ready.wait()
        return self.nextorderId

    def request_historical_data(self, symbol: str, end_date: str, duration: str = '1 Y', bar_size: str = '1 day'):
        """
        Requests historical data for a stock.

        Parameters:
        - symbol (str): Stock symbol.
        - end_date (str): End date in 'YYYYMMDD HH:MM:SS' format.
        - duration (str): Duration of data to retrieve. Default is '1 Y' for one year.
        - bar_size (str): Size of each bar. Default is '1 day'.
        """
        print(f'Request Historical Data for {symbol}')
        EXCHANGE = 'SMART'
        PRIMARYEXCHANGE = 'ARCA'

        contract = Contract()
        contract.symbol = symbol
        contract.secType = 'STK'
        contract.currency = 'USD'
        contract.exchange = EXCHANGE
        contract.primaryExchange = PRIMARYEXCHANGE
        
        self.reqHistoricalData(
            1, contract, end_date, duration, bar_size, 'TRADES', 1, 1, False, []
        )  # Request historical data
        self.historical_data_ready.wait()  # Wait until data is received

    def historicalData(self, reqId: int, bar):
        """
        Callback for receiving historical data.

        Parameters:
        - reqId (int): Request ID.
        - bar: Data bar containing historical data.
        """
        super().historicalData(reqId, bar)
        print(f"Historical data received: {bar.date}, Open={bar.open}, High={bar.high}, Low={bar.low}, Close={bar.close}, Volume={bar.volume}")

    def historicalDataEnd(self, reqId: int, startDate: str, endDate: str):
        """
        Callback for when historical data transmission is complete.

        Parameters:
        - reqId (int): Request ID.
        - startDate (str): Start date of the historical data request.
        - endDate (str): End date of the historical data request.
        """
        super().historicalDataEnd(reqId, startDate, endDate)
        print(f"Historical data end for request ID {reqId}. ({startDate}, {endDate})")
        self.historical_data_ready.set()  # Signal that data transmission is complete

    def stop(self):
        """
        Disconnects the client from TWS and performs cleanup operations.
        """
        print('Disconnecting from TWS.')
        self.disconnect()
        time.sleep(0.5)  # Ensure disconnection process completes

if __name__ == '__main__':

    port = 7497
    clientId = 0
    symbol = 'TSM'
    duration = '1 M' #'1 Y'
    bar_size = '1 day'
    end_date = '20240719'

    app = App()
    app.connect('127.0.0.1', port, clientId)
    time.sleep(0.5)  # Give time for connection to be established
    app.start()
    app.request_historical_data(symbol, f'{end_date} 17:00:00 US/Eastern', duration, bar_size)
    app.stop()
