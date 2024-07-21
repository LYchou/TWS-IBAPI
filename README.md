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