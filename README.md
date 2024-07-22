## 概述

這個程式的主要目的是建立與 Interactive Brokers' Trader Workstation (TWS) 的連接，以便進行自動化的交易操作。程式通過 `EClient` 和 `EWrapper` 類別來建立和處理與 TWS 的連接，實現與 TWS 的雙向通信。

## EClient

`EClient`（Client API）是與 TWS（Trader Workstation）或 IB Gateway 進行通信的客戶端。它負責發送請求給 TWS 並處理與 TWS 的連接相關的功能。

### 主要功能

- **建立連接**：
  - `connect(host, port, clientId)`：用於與 TWS 或 IB Gateway 建立連接，`host` 是 TWS 或 IB Gateway 的 IP 地址，`port` 是連接端口，`clientId` 是唯一的客戶端 ID。

- **發送請求**：
  - 向 TWS 發送各種請求，如訂閱市場數據、請求合約信息、提交訂單等。
  - 例如：`reqMktData(reqId, contract, genericTickList, snapshot, regulatorySnapshot, mktDataOptions)`：用於訂閱市場數據，其中 `reqId` 是請求的唯一標識符，`contract` 是合約對象。

- **處理通信**：
  - 負責低層次的通信處理，如打包和發送數據。確保數據能夠準確地發送到 TWS 並接收回應。

## EWrapper

`EWrapper`（Wrapper API）是用來處理來自 TWS 的回應和事件的。它定義了一組回調方法，這些方法會在收到相應的事件或數據時被自動調用。

### 主要功能

- **處理回應和事件**：
  - 定義各種回調方法來處理 TWS 返回的數據和事件。例如，市場數據更新、訂單狀態更新、錯誤消息等。
  - 例如：`tickPrice(reqId, tickType, price, attrib)`：當市場價格更新時被調用，`reqId` 用於識別請求，`tickType` 表示數據類型，`price` 是更新的價格，`attrib` 是附加屬性。

- **數據解析**：
  - 解析來自 TWS 的數據並將其傳遞給應用程序。處理數據後，可以用於進一步的分析或操作。

## 多重繼承

`App` 類別通過多重繼承同時繼承了 `EWrapper` 和 `EClient` 類別，因此它可以同時擁有這兩個類別的功能。這使得 `App` 類別能夠同時處理請求和回應，實現與 TWS 的雙向通信。

## 連接參數說明

- **port**：
  - 連接端口號。`port` 是 TWS 或 IB Gateway 的通信端口，默認值通常是 7497（TWS 的紙上交易端口）或 7496（實盤交易端口）。正確的端口號確保了客戶端能夠正確連接到 TWS 或 IB Gateway。

- **clientId**：
  - 客戶端 ID。`clientId` 是用於識別不同客戶端連接的唯一標識符。每個連接必須有一個唯一的 `clientId`，以避免與其他連接的衝突。在同一個 TWS 實例中，不能有兩個客戶端使用相同的 `clientId`。
  - **功能**：
    - `clientId` 允許 TWS 確定並管理不同客戶端的連接，這對於多個交易系統或交易員來說尤其重要。
    - 這個功能使得不同涉略和不同交易員可以通過獨特的 `clientId` 識別和管理各自的訂單和操作，確保每個交易的獨立性和準確性。


## 程式碼示例

以下是建立與 TWS 連接並斷開連接的程式碼示例：

```python
import time
from ibapi.client import EClient
from ibapi.wrapper import EWrapper

class App(EWrapper, EClient):
    """
    This class combines the functionalities of EWrapper and EClient
    to create a connection with Interactive Brokers' Trader Workstation (TWS).
    """
    def __init__(self):
        """
        Initializes the EClient part of the instance. The EWrapper part is
        initialized implicitly by inheriting from EWrapper.
        """
        EClient.__init__(self, self)

def main():
    # Define connection parameters
    port = 7497  # Port for TWS paper trading
    clientId = 0  # Unique client ID for this connection

    # Create an instance of the App class
    app = App()
    
    # Connect to TWS
    app.connect('127.0.0.1', port, clientId)
    
    # Wait briefly to ensure connection is established
    time.sleep(0.5)
    
    # Disconnect from TWS
    app.disconnect()
```

### 程式碼解析

1. **導入庫**：
   - 導入 `time`、`EClient` 和 `EWrapper` 類。

2. **定義 `App` 類別**：
   - `App` 類別繼承了 `EWrapper` 和 `EClient`，並在 `__init__` 方法中初始化了 `EClient`。

3. **主函數 `main`**：
   - 定義了連接參數，包括端口和客戶端 ID。
   - 創建 `App` 類別的實例，並與 TWS 進行連接。
   - 等待一段時間以確保連接建立成功。
   - 斷開與 TWS 的連接。

### 異步處理

在這個程式中，`EClient` 和 `EWrapper` 類別的設計是基於異步處理的。異步處理允許在連接建立後，程式可以繼續執行其他操作而不需要等待所有回應。當 TWS 回應或發生事件時，`EWrapper` 定義的回調方法會被自動調用，這樣可以在不阻塞主線程的情況下處理回應和事件。這種方式使得程式能夠同時處理多個請求和回應，提高了程式的效率和響應速度。

這個程式碼示例展示了如何建立和斷開與 TWS 的連接。透過 `EClient` 和 `EWrapper` 的結合，`App` 類別能夠有效地處理與 TWS 的通信和回應。













### 簡易說明 - place_order

#### 1. 在做什麼？

這段程式碼用於與 Interactive Brokers (IB) 的交易系統進行互動，自動下單交易。具體來說，程式會：

- 初始化一個客戶端應用程序以連接到 IB 的交易系統 (TWS)。
- 從預定義的訂單信息生成交易訂單和對應的合約。
- 請求並獲取有效的訂單 ID。
- 將生成的訂單提交到 IB 的交易系統。

#### 2. 怎麼使用？

使用這個程式的步驟如下：

1. **修改訂單信息**：
   - 確保 TWS 或 IB Gateway 正確配置，允許 API 連接並設置了正確的端口號（預設為 7497）

2. **修改訂單信息**：
   - 在 `get_orders` 函數中修改訂單信息（如帳戶號、股票代碼、動作和數量）以匹配您的交易需求。

3. **運行程式**：
   - 在終端或命令行中運行程式：`python <filename>.py`。




### 程式碼簡介 - request_callback

這段程式碼解決了如何與 Interactive Brokers TWS API 交互以管理交易執行細節和手續費報告的問題。以下是程式碼的功能、使用方法及可圈可點的部分。

---

### 功能

1. **連接TWS**：建立與 TWS 的連接。
2. **獲取有效訂單ID**：獲取下一個有效的訂單ID。
3. **請求交易執行細節**：請求並接收執行細節。
4. **收集手續費報告**：接收並儲存手續費報告。
5. **配對執行與手續費報告**：將交易執行與手續費報告配對。

---

### 使用方法

1. **初始化並連接**

    ```python
    app = App()
    app.connect('127.0.0.1', 7497, 0)  # 連接到TWS的paper trading port
    time.sleep(0.5)  # 等待連接建立
    app.start()
    ```

2. **獲取有效訂單ID並請求交易執行細節**

    ```python
    nextorderId = app.wait_for_nextValidId()  # 獲取下一個有效訂單ID
    app.wait_for_reqExecutions(nextorderId)  # 請求交易執行細節
    ```

3. **斷開連接並計算回調**

    ```python
    app.stop()  # 斷開與TWS的連接
    app.calculate_callbacks()  # 計算回調，配對執行與手續費報告
    ```

4. **輸出配對結果**

    ```python
    for callback in app.callbacks:
        print(callback.output())  # 輸出每個回調的詳細資訊
    ```

---

### 可圈可點的部分

1. **同步機制**：使用 `Event` 來同步主執行緒與TWS API回調。
   
    ```python
    self.first_nextValidId_ready = Event()
    ```

2. **多執行緒處理**：通過 `Thread` 類來非阻塞地執行API請求。
   
    ```python
    thread = Thread(target=self.run)
    thread.start()
    ```

3. **數據結構**：使用 `dict` 和 `set` 高效地配對執行和手續費報告。
   
    ```python
    execution_dict = {execution.execId: (contract, execution) for contract, execution in self.execution_list}
    ```

4. **錯誤處理**：提供 `error` 回調來處理TWS錯誤訊息。
   
    ```python
    def error(self, reqId, errorCode, errorString):
        if reqId != -1:
            print(f"Error received. ReqId: {reqId}, ErrorCode: {errorCode}, ErrorString: {errorString}")
    ```

5. **回調類別設計**： `Callback` 類別封裝了交易執行、合約和手續費報告的數據，並提供 `output` 方法來輸出這些數據。

6. **解耦合設計**： `App` 類別和 `Callback` 類別的單一職責原則，提高了程式碼的可維護性。

---

這段程式碼提供了一個穩定且高效的方式來處理TWS API的交易數據。