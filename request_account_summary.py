import threading
import pandas as pd
import time
from threading import Thread, Event
from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.account_summary_tags import AccountSummaryTags

class App(EWrapper, EClient):
    """
    A class to interact with the Interactive Brokers API, handling connection,
    request for next valid order ID, and account summary.

    Attributes:
    accountSummary_header (list): Header for the account summary DataFrame.
    nextorderId (int): The next valid order ID.
    accountSummary_list (list): List to store account summary data.
    accountSummary_df (pd.DataFrame): DataFrame to store account summary data.
    first_nextValidId_ready (Event): Event to signal the reception of the first valid order ID.
    nextValidId_ready (Event): Event to signal the reception of the next valid order ID.
    reqAccountSummary_ready (Event): Event to signal the reception of the account summary.
    lock (threading.Lock): Lock to synchronize thread access to shared resources.
    """
    
    accountSummary_header = ['Account', 'Tag', 'Value', 'Currency']

    def __init__(self):
        """
        Initializes the App instance, setting up events for synchronization and establishing connection parameters.
        """
        EClient.__init__(self, self)  # Initialize the EClient part of this instance
        # Initialize class attributes
        self.nextorderId = None  # To store the next valid order ID from TWS
        self.accountSummary_list = []
        self.accountSummary_df = pd.DataFrame(columns=self.accountSummary_header)
        # Events used to synchronize between the main thread and TWS callback responses
        self.first_nextValidId_ready = Event()  # Signals successful connection to TWS
        self.nextValidId_ready = Event()
        self.reqAccountSummary_ready = Event()
        self.lock = threading.Lock()  # Used for thread synchronization, particularly when accessing shared resources
        print('App instance initialized.')

    def start(self):
        """
        Starts the application by creating and starting a new thread to run the app.
        Waits for the first valid order ID response.
        """
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
            print(f'App has received the first valid orderId: {orderId}')
        else:
            with self.lock:
                self.nextorderId = orderId  # Update the next valid order ID
                self.nextValidId_ready.set()  # Signal that the next valid order ID has been received
                print(f'Next valid order ID received: {orderId}')
    
    def wait_for_nextValidId(self) -> int:
        """
        Requests the next valid order ID and waits until it's received.

        Returns:
        - nextorderId (int): The next valid order ID.
        """
        self.reqIds(-1)
        self.nextValidId_ready.wait()
        return self.nextorderId
    
    def wait_for_reqAccountSummary(self, orderId) -> pd.DataFrame:
        """
        Requests the account summary for all accounts and waits for the data to be received.

        Parameters:
        - orderId (int): The order ID used for the request.

        Returns:
        - accountSummary_df (pd.DataFrame): DataFrame containing the account summary data.
        """
        print(f'Request account summary for All with orderId: {orderId}')
        self.reqAccountSummary(orderId, "All", AccountSummaryTags.AllTags)
        self.reqAccountSummary_ready.wait()
        self.accountSummary_df = pd.DataFrame(self.accountSummary_list, columns=self.accountSummary_header)
        return self.accountSummary_df

    def accountSummary(self, reqId: int, account: str, tag: str, value: str, currency: str):
        """
        Callback for account summary details received from the API.

        Parameters:
        - reqId (int): Request ID.
        - account (str): Account name.
        - tag (str): Data tag.
        - value (str): Data value.
        - currency (str): Currency of the value.
        """
        super().accountSummary(reqId, account, tag, value, currency)
        content = [account, tag, value, currency]
        self.accountSummary_list.append(content)
        print(f"Account summary data received: {content}")

    def accountSummaryEnd(self, reqId: int):
        """
        Callback for when account summary data finishes transmitting.

        Parameters:
        - reqId (int): Request ID.
        """
        super().accountSummaryEnd(reqId)
        print(f"Account summary transmission ended for ReqId: {reqId}")
        self.reqAccountSummary_ready.set()

    def error(self, reqId, errorCode, errorString, advancedOrderRejectJson=''):
        """
        Callback for error messages received from the API.

        Parameters:
        - reqId (int): Request ID.
        - errorCode (int): Error code.
        - errorString (str): Error description.
        - advancedOrderRejectJson (str, optional): Advanced order reject details in JSON format.
        """
        if reqId != -1:
            print(f"Error received. ReqId: {reqId}, ErrorCode: {errorCode}, ErrorString: {errorString}")

    def stop(self):
        """
        Disconnects the client from TWS and performs cleanup operations like closing the logger.
        """
        print('Disconnecting from TWS.')
        self.disconnect()  # Disconnect from TWS
        time.sleep(0.5)  # Allow some time for disconnection cleanup

if __name__ == '__main__':
    port = 7497
    clientId = 0

    app = App()
    app.connect('127.0.0.1', port, clientId)
    time.sleep(0.5)
    app.start()
    nextorderId = app.wait_for_nextValidId()
    app.wait_for_reqAccountSummary(nextorderId)
    app.stop()

    print(app.accountSummary_df)
