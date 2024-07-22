import threading
import time
from threading import Thread, Event
from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
from ibapi.execution import Execution
from ibapi.commission_report import CommissionReport
from ibapi.execution import ExecutionFilter

class App(EWrapper, EClient):
    """
    The App class encapsulates functionality for placing orders and managing financial advisor data using Interactive Brokers' TWS API.
    It inherits from EWrapper to handle server responses and from EClient to send requests to the TWS.
    """

    def __init__(self):
        """
        Initializes the App instance, setting up events for synchronization and establishing connection parameters.
        """
        EClient.__init__(self, self)  # Initialize the EClient part of this instance
        self.nextorderId = None  # To store the next valid order ID from TWS
        self.execution_list = []  # List to store execution details
        self.commission_list = []  # List to store commission reports
        self.callbacks = []  # List to store callbacks
        self.connection_status = False  # Connection status flag
        # Events used to synchronize between the main thread and TWS callback responses
        self.first_nextValidId_ready = Event()  # Signals successful connection to TWS
        self.nextValidId_ready = Event()  # Signals next valid ID received
        self.reqExecutions_ready = Event()  # Signals execution data received
        self.lock = threading.Lock()  # Used for thread synchronization, particularly when accessing shared resources
        print('App instance initialized.')

    def start(self):
        """
        Starts the app by launching the main thread for TWS communication.
        """
        print('Run app.')
        thread = Thread(target=self.run)  # Create a new thread for the run method
        thread.start()  # Start the thread
        print('Waiting for the response of the first valid Id.')
        self.first_nextValidId_ready.wait()  # Wait until the first valid ID is received

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
        int: The next valid order ID.
        """
        self.reqIds(-1)
        self.nextValidId_ready.wait()
        return self.nextorderId
    
    def wait_for_reqExecutions(self, orderId) -> list:
        """
        Requests execution details and waits until the data is received.
        
        Parameters:
        - orderId (int): The order ID for which execution details are requested.
        """
        print('Requesting executions data.')
        self.reqExecutions(orderId, ExecutionFilter())
        self.reqExecutions_ready.wait()

    def execDetailsEnd(self, reqId:int):
        """
        Callback indicating the end of execution details.

        Args:
        - reqId (int): The request ID associated with the execution details.
        """
        super().execDetailsEnd(reqId)
        timer = threading.Timer(1, self.reqExecutions_ready.set)
        timer.start()  # Start the timer
        print('Requesting executions have been completed.')

    def execDetails(self, reqId:int, contract:Contract, execution:Execution):
        """
        Callback receiving execution details.

        Parameters:
        - reqId (int): The request ID.
        - contract (Contract): The contract details.
        - execution (Execution): The execution details.
        """
        super().execDetails(reqId, contract, execution)
        self.execution_list.append((contract, execution))
        print(f'execDetails: contract({contract}), execution({execution})')

    def commissionReport(self, commissionReport:CommissionReport):
        """
        Callback when the API returns commission report.

        Args:
        - commissionReport: The commission report.
        """
        super().commissionReport(commissionReport)
        self.commission_list.append(commissionReport)
        print(f'commissionReport: {commissionReport}')
    
    def error(self, reqId, errorCode, errorString, advancedOrderRejectJson=''):
        """
        Callback for errors returned by the API.

        Parameters:
        - reqId: ID of the request that caused the error.
        - errorCode: Numeric error code.
        - errorString: String error message.
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

    def _match_execution_and_commission(self) -> list:
        """
        Match executions with corresponding commission reports.
        
        This function matches executions with their corresponding commission reports based on the execId attribute.
        
        Returns:
        list: A list of tuples containing the execId (int), contract (Contract), execution (Execution), 
            and commissionReport (CommissionReport).
        """
        # Create a dictionary with default value of (None, None)
        execution_dict = {}
        for contract, execution in self.execution_list:
            execution_dict[execution.execId] = (contract, execution)
        
        # Create a dictionary for commission reports
        commission_dict = {}
        for commissionReport in self.commission_list:
            commission_dict[commissionReport.execId] = commissionReport

        # Merge the keys of both dictionaries to get all unique execId
        execId_set = set(execution_dict.keys()) | set(commission_dict.keys())
        
        # Build the result list
        result = []
        for execId in sorted(execId_set):
            contract, execution = execution_dict.get(execId, (Contract(), Execution()))
            commissionReport = commission_dict.get(execId, CommissionReport())
            result.append((execId, contract, execution, commissionReport))
        
        return result
    
    def calculate_callbacks(self) -> list:
        """
        Get the matched executions with corresponding commission reports.

        Returns:
        list: A list of tuples containing the execId (int), contract (Contract), execution (Execution),
            and commissionReport (CommissionReport).
        """
        # Get the matched executions with corresponding commission reports
        callback_tuple_list = self._match_execution_and_commission()
        callbacks = []
        # Check if any element is None in the result list
        for execId, contract, execution, commissionReport in callback_tuple_list:
            if None in (contract, execution, commissionReport):
                missing_data = [name for name, value in zip(('contract', 'execution', 'commissionReport'), (contract, execution, commissionReport)) if value is None]
                raise ValueError(f"One or more elements are None for execId: {execId}. Missing data: {', '.join(missing_data)}")
            callbacks.append(Callback(contract, execution, commissionReport))
        self.callbacks = callbacks

        return callbacks

class Callback:
    """
    Class representing a callback for execution and commission data.
    """

    contract_attributes = {
        'conId': 'ConId',
        'symbol': 'Symbol',
        'secType': 'SecType',
        'lastTradeDateOrContractMonth': 'LastTradeDateOrContractMonth',
        'strike': 'Strike',
        'right': 'Right',
        'multiplier': 'Multiplier',
        'exchange': 'Exchange',
        'primaryExchange': 'PrimaryExchange',
        'currency': 'Currency'
    }
    
    execution_attributes = {
        'execId': 'ExecId',
        'time': 'Time',
        'acctNumber': 'Account',
        'exchange': 'Exchange',
        'side': 'Side',
        'shares': 'Shares',
        'price': 'Price',
        'permId': 'PermId',
        'clientId': 'ClientId',
        'orderId': 'OrderId',
        'liquidation': 'Liquidation',
        'cumQty': 'CumQty',
        'avgPrice': 'AvgPrice',
        'orderRef': 'OrderRef',
        'evRule': 'EvRule',
        'evMultiplier': 'EvMultiplier',
        'modelCode': 'ModelCode',
        'lastLiquidity': 'LastLiquidity'
    }

    commissionReport_attributes = {
        'execId': 'ExecId',
        'commission': 'Commission',
        'currency': 'Currency',
        'realizedPNL': 'RealizedPNL',
        'yield_': 'Yield',
        'yieldRedemptionDate': 'YieldRedemptionDate'
    }

    def __init__(self, contract: Contract = None, execution: Execution = None, commissionReport: CommissionReport = None) -> None:
        self.contract = contract or Contract()
        self.execution = execution or Execution()
        self.commissionReport = commissionReport or CommissionReport()

    def output(self) -> dict:
        """
        Combines execution, contract, and commission report data into a single dictionary.
        
        Returns:
        dict: Combined data from execution, contract, and commission report.
        """
        return {**self.output_execution(), **self.output_contract(), **self.output_commission()}
    
    def output_execution_and_contract(self) -> dict:
        """
        Combines execution and contract data into a single dictionary.
        
        Returns:
        dict: Combined data from execution and contract.
        """
        return {**self.output_execution(), **self.output_contract()}
    
    def output_contract(self) -> dict:
        """
        Outputs contract attributes as a dictionary.
        
        Returns:
        dict: Contract attributes.
        """
        return {attr_key: getattr(self.contract, attr) for attr, attr_key in self.contract_attributes.items()}
    
    def output_execution(self) -> dict:
        """
        Outputs execution attributes as a dictionary.
        
        Returns:
        dict: Execution attributes.
        """
        return {attr_key: getattr(self.execution, attr) for attr, attr_key in self.execution_attributes.items()}
    
    def output_commission(self) -> dict:
        """
        Outputs commission report attributes as a dictionary.
        
        Returns:
        dict: Commission report attributes.
        """
        return {attr_key: getattr(self.commissionReport, attr) for attr, attr_key in self.commissionReport_attributes.items()}

if __name__ == '__main__':
    port = 7497  # TWS paper trading port
    clientId = 0  # Client ID for the connection

    app = App()
    app.connect('127.0.0.1', port, clientId)  # Connect to TWS
    time.sleep(0.5)  # Allow some time for the connection to be established
    app.start()
    nextorderId = app.wait_for_nextValidId()  # Get the next valid order ID
    app.wait_for_reqExecutions(nextorderId)  # Request execution details
    app.stop()  # Disconnect from TWS
    app.calculate_callbacks()  # Calculate callbacks

    for callback in app.callbacks:
        print(callback.output())  # Print the output for each callback
