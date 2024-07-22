# Import necessary libraries and modules for threading, logging, and interacting with the Interactive Brokers API
import threading
import pandas as pd
import time
from threading import Thread, Event
from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract


class App(EWrapper, EClient):
    # Define headers for the data
    updateAccountValue_header = ['Account', 'Key', 'Val', 'Currency']
    updatePortfolio_header = [
        'ConId', 'Symbol', 'SecType', 'LastTradeDateOrContractMonth', 'Strike', 'Right', 'Multiplier', 'Exchange', 'PrimaryExchange', 'Currency', 
        'Account', 'Position', 'MarketPrice', 'MarketValue', 'AverageCost', 'UnrealizedPNL', 'RealizedPNL']

    def __init__(self):
        EClient.__init__(self, self)  # Initialize the EClient part of this instance
        # Initialize class attributes
        self.nextorderId = None  # To store the next valid order ID from TWS
        self.updateAccountValue_list = []
        self.updatePortfolio_list = []
        #
        self.connection_status = False
        # Events used to synchronize between the main thread and TWS callback responses
        self.first_nextValidId_ready = Event()
        self.nextValidId_ready = Event()
        self.managedAccounts_ready = Event()
        self.reqAccountUpdates_ready = Event()
        self.lock = threading.Lock()  # Used for thread synchronization, particularly when accessing shared resources
        print('App instance initialized.')

    def start(self):
        print('Run app.')
        thread = Thread(target=self.run)
        thread.start()
        print('Waiting for the response of the first valid Id.')
        self.first_nextValidId_ready.wait()

    def reqIds(self, numIds: int):
        """
        Requests the next available order ID from TWS. This method overrides EClient.reqIds.
        
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
        # The first time this method is called signifies a successful connection
        if not self.first_nextValidId_ready.is_set():
            self.first_nextValidId_ready.set()
            print(f'App has recieved the first valid orderId is: {orderId}')
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

    def wait_for_reqAccountUpdates(self, accountName:str):
        self.reqAccountUpdates_ready.clear()
        print(f"Requesting account updates for {accountName}.")
        self.reqAccountUpdates(True, accountName)
        self.reqAccountUpdates_ready.wait()

    def updateAccountValue(self, key: str, val: str, currency: str, accountName: str):
        """
        Updates account value list upon receiving update.

        Parameters:
        - key, val, currency, accountName: Account update details.
        """
        super().updateAccountValue(key, val, currency, accountName)
        content = [accountName, key, val, currency]
        self.updateAccountValue_list.append(content)
        print(f"Account data received: {content}")

    def updatePortfolio(self, contract: Contract, position: float, marketPrice: float, marketValue: float,
                        averageCost: float, unrealizedPNL: float, realizedPNL: float, accountName: str):
        """
        Updates portfolio list upon receiving update.

        Parameters:
        - contract, position, marketPrice, marketValue, averageCost, unrealizedPNL, realizedPNL, accountName: Portfolio update details.
        """
        super().updatePortfolio(contract, position, marketPrice, marketValue, averageCost, unrealizedPNL, realizedPNL, accountName)
        content = [
            contract.conId, 
            contract.symbol, 
            contract.secType, 
            contract.lastTradeDateOrContractMonth, 
            contract.strike, 
            contract.right, 
            contract.multiplier,
            contract.exchange,
            contract.primaryExchange,
            contract.currency, 
            accountName, position, marketPrice, marketValue, 
            averageCost, unrealizedPNL, realizedPNL
        ]
        self.updatePortfolio_list.append(content)
        print(f"Portfolio data received: {content}")

    def accountDownloadEnd(self, accountName: str):
        """
        Stops account data update and checks if it's the last account, then disconnects.

        Parameters:
        - accountName: Account name where download ended.
        """
        super().accountDownloadEnd(accountName)
        self.reqAccountUpdates(False, accountName)
        print(f'Account download ended for {accountName}')
        self.reqAccountUpdates_ready.set()

    def wait_for_managedAccounts(self) -> list:
        self.managedAccounts_ready.wait()
        return self.accountsList
        
    def managedAccounts(self, accountsList: str):
        """
        Callback for managed accounts. Initializes account list and requests IDs.

        Parameters:
        - accountsList: Comma separated list of account names.
        """
        super().managedAccounts(accountsList)
        self.accountsList = [accountName.strip() for accountName in accountsList.split(',') if accountName.strip()]
        print(f'Managed accounts received: {self.accountsList}.')
        self.managedAccounts_ready.set() 

    def error(self, reqId, errorCode, errorString, advancedOrderRejectJson=''):
        """
        Callback for errors returned by the API.

        Parameters:
        - reqId: ID of the request that caused the error.
        - errorCode: Numeric error code.
        - errorString: String error message.
        """
        # super().error(reqId, errorCode, errorString, advancedOrderRejectJson)
        # if errorCode == 502:
        #     print('error', f"Error received. ReqId: {reqId}, ErrorCode: {errorCode}, ErrorString: {errorString}")
        if reqId != -1:
            print('error', f"Error received. ReqId: {reqId}, ErrorCode: {errorCode}, ErrorString: {errorString}")

    def stop(self):
        """
        Disconnects the client from TWS and performs cleanup operations like closing the logger.
        """
        print('Disconnecting from TWS.')
        self.disconnect()  # Disconnect from TWS
        time.sleep(0.5)  # Allow some time for disconnection cleanup

    def get_updateAccountValue(self):
        return pd.DataFrame(self.updateAccountValue_list, columns=self.updateAccountValue_header)

    def get_updatePortfolio(self):
        updatePortfolio = pd.DataFrame(self.updatePortfolio_list, columns=self.updatePortfolio_header)
        return updatePortfolio



if __name__=='__main__':

    port = 7497
    clientId = 0

    app = App()
    app.connect('127.0.0.1', port, clientId)
    time.sleep(0.5)
    app.start()
    accounts = app.wait_for_managedAccounts()
    for account in accounts:
        app.wait_for_reqAccountUpdates(account)
    app.stop()

    updateAccountValue = app.get_updateAccountValue().drop_duplicates(ignore_index=True)
    updatePortfolio = app.get_updatePortfolio().drop_duplicates(ignore_index=True)

    print(updateAccountValue)
    print(updatePortfolio)
