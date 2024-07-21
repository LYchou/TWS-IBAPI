import time
from threading import Timer

from ibapi.client import EClient
from ibapi.wrapper import EWrapper

class App(EWrapper, EClient):
    """
    A custom application class inheriting from IB's EWrapper and EClient. 
    Used to interact with the IB API for fetching and managing orders.
    """
  
    def __init__(self):
        """Initializes the App class."""
        EClient.__init__(self, self)

    def nextValidId(self, orderId: int):
        """Callback function triggered when a new valid order ID is received."""
        super().nextValidId(orderId)
        self.reqGlobalCancel()
        self.stop()


    def stop(self):
        """Disconnect from the IB server."""
        Timer(1, self.disconnect).start()


if __name__ == '__main__':

    port = 7497
    clientId = 0

    app = App()
    app.connect('127.0.0.1', port, clientId)
    time.sleep(0.5)  # Give time for connection to be established
    app.run()