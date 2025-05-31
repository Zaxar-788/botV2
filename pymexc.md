## MEXC Futures API Documentation

This document provides a structured overview of the MEXC Futures API, focusing on clarity, conciseness, and practical examples.

### Methods

The API offers a variety of methods to interact with the MEXC Futures exchange. Each method is categorized by its functionality and accompanied by its respective parameters and examples.

### Market Data Endpoints

These endpoints provide access to public market data, requiring no authentication.

#### 1. `ping`

   - **Description:** Retrieves the server time.
   - **Rate Limit:** 20 times/2 seconds
   - **Parameters:** None
   - **Example:**
     ```python
     futures_client.ping()
     ```

#### 2. `detail`

   - **Description:** Fetches contract information.
   - **Rate Limit:** 1 time/5 seconds
   - **Parameters:**
     - `symbol` (optional): The contract name (e.g., "BTC_USDT").
   - **Example:**
     ```python
     futures_client.detail(symbol="BTC_USDT") 
     futures_client.detail()  # Retrieves details for all contracts
     ```

#### 3. `support_currencies`

   - **Description:** Retrieves the list of transferable currencies.
   - **Rate Limit:** 20 times/2 seconds
   - **Parameters:** None
   - **Example:**
     ```python
     futures_client.support_currencies() 
     ```

#### 4. `get_depth`

   - **Description:**  Fetches the contract's order book (depth) information.
   - **Rate Limit:** 20 times/2 seconds
   - **Parameters:**
     - `symbol`: The contract name.
     - `limit` (optional): The maximum number of price levels to return (default and maximum is usually 100).
   - **Example:**
     ```python
     futures_client.get_depth(symbol="BTC_USDT", limit=50)
     ```

#### 5. `depth_commits`

   - **Description:** Retrieves a snapshot of the latest N depth updates for the contract.
   - **Rate Limit:** 20 times/2 seconds
   - **Parameters:**
     - `symbol`: The contract name.
     - `limit`: The number of recent depth snapshots to retrieve.
   - **Example:**
     ```python
     futures_client.depth_commits(symbol="BTC_USDT", limit=10)
     ```

#### 6. `index_price`

   - **Description:** Retrieves the contract's index price.
   - **Rate Limit:** 20 times/2 seconds
   - **Parameters:**
     - `symbol`: The contract name.
   - **Example:**
     ```python
     futures_client.index_price(symbol="BTC_USDT")
     ```

#### 7. `fair_price`

   - **Description:** Retrieves the contract's fair price.
   - **Rate Limit:** 20 times/2 seconds
   - **Parameters:**
     - `symbol`: The contract name.
   - **Example:**
     ```python
     futures_client.fair_price(symbol="BTC_USDT")
     ```

#### 8. `funding_rate`

   - **Description:** Retrieves the current funding rate for the contract.
   - **Rate Limit:** 20 times/2 seconds
   - **Parameters:**
     - `symbol`: The contract name.
   - **Example:**
     ```python
     futures_client.funding_rate(symbol="BTC_USDT")
     ```

#### 9. `kline`

   - **Description:** Retrieves historical candlestick (K-line) data for the contract.
   - **Rate Limit:** 20 times/2 seconds
   - **Parameters:**
     - `symbol`: The contract name.
     - `interval`: The candlestick time interval. Possible values: "Min1", "Min5", "Min15", "Min30", "Min60", "Hour4", "Hour8", "Day1", "Week1", "Month1".
     - `start` (optional): Start time for the data retrieval in Unix timestamp milliseconds.
     - `end` (optional): End time for the data retrieval in Unix timestamp milliseconds.
   - **Example:**
     ```python
     futures_client.kline(symbol="BTC_USDT", interval="Min15", start=1660822800000, end=1660909200000)
     ```

#### 10. `kline_index_price`

   - **Description:**  Retrieves historical index price kline data.
   - **Rate Limit:** 20 times/2 seconds
   - **Parameters:** Same as `kline`
   - **Example:**
     ```python
     futures_client.kline_index_price(symbol="BTC_USDT", interval="Hour4") 
     ```

#### 11. `kline_fair_price`

   - **Description:** Retrieves historical fair price kline data.
   - **Rate Limit:** 20 times/2 seconds
   - **Parameters:** Same as `kline`
   - **Example:**
     ```python
     futures_client.kline_fair_price(symbol="BTC_USDT", interval="Day1") 
     ```

#### 12. `deals`

   - **Description:** Retrieves recent trades for the contract.
   - **Rate Limit:** 20 times/2 seconds
   - **Parameters:**
     - `symbol`: The contract name.
     - `limit` (optional): The maximum number of trades to return (default and maximum is usually 100).
   - **Example:**
     ```python
     futures_client.deals(symbol="BTC_USDT", limit=50) 
     ```

#### 13. `ticker`

   - **Description:** Retrieves ticker data for one or all contracts.
   - **Rate Limit:** 20 times/2 seconds
   - **Parameters:**
     - `symbol` (optional): The contract name. If not provided, returns data for all contracts.
   - **Example:**
     ```python
     futures_client.ticker(symbol="BTC_USDT") 
     futures_client.ticker()  # Retrieves tickers for all contracts
     ```

#### 14. `risk_reverse`

   - **Description:**  Retrieves the balance of the risk reserve fund for all contracts.
   - **Rate Limit:** 20 times/2 seconds
   - **Parameters:** None
   - **Example:**
     ```python
     futures_client.risk_reverse()
     ```

#### 15. `risk_reverse_history`

   - **Description:** Retrieves the historical data of the risk reserve fund for a specific contract.
   - **Rate Limit:** 20 times/2 seconds
   - **Parameters:**
     - `symbol`: The contract name.
     - `page_num` (optional): The page number for pagination (default is 1).
     - `page_size` (optional): The number of entries per page (default is 20, maximum is 100).
   - **Example:**
     ```python
     futures_client.risk_reverse_history(symbol="BTC_USDT", page_num=2, page_size=50)
     ```

#### 16. `funding_rate_history`

   - **Description:** Retrieves historical funding rates for a specific contract.
   - **Rate Limit:** 20 times/2 seconds
   - **Parameters:** 
      - `symbol`: The contract name.
      - `page_num` (optional): The page number for pagination (default is 1).
      - `page_size` (optional): The number of entries per page (default is 20, maximum is 100).
   - **Example:**
     ```python
     futures_client.funding_rate_history(symbol="BTC_USDT", page_num=2, page_size=50)
     ```

### Account and Trading Endpoints

These endpoints require authentication and allow you to manage your account and execute trades.

#### 1. `assets`
   - **Description:**  Retrieves information about the user's assets.
   - **Permissions Required:** Trade reading permission
   - **Rate Limit:** 20 times/2 seconds
   - **Parameters:** None
   - **Example:**
     ```python
     futures_client.assets()
     ```

#### 2. `asset`
   - **Description:** Retrieves information about a specific asset in the user's account.
   - **Permissions Required:** Account reading permission.
   - **Rate Limit:** 20 times/2 seconds
   - **Parameters:**
     - `currency`: The currency code (e.g., "USDT").
   - **Example:**
     ```python
     futures_client.asset(currency="USDT") 
     ```

#### 3. `transfer_record`
   - **Description:** Retrieves the user's asset transfer history.
   - **Permissions Required:** Account reading permission.
   - **Rate Limit:** 20 times/2 seconds
   - **Parameters:**
     - `currency` (optional): Filters records by currency.
     - `state` (optional): Filters records by transfer state ("WAIT", "SUCCESS", "FAILED").
     - `type` (optional): Filters records by transfer type ("IN", "OUT").
     - `page_num` (optional): The page number for pagination (default is 1).
     - `page_size` (optional): The number of entries per page (default is 20, maximum is 100).
   - **Example:**
     ```python
     futures_client.transfer_record(currency="BTC", state="SUCCESS", type="IN") 
     ```

#### 4. `history_positions`
   - **Description:** Retrieves the user's historical position information.
   - **Permissions Required:** Trade reading permission.
   - **Rate Limit:** 20 times/2 seconds
   - **Parameters:**
     - `symbol` (optional): Filters records by contract.
     - `type` (optional): Filters records by position type (1 for long, 2 for short).
     - `page_num` (optional): The page number for pagination (default is 1).
     - `page_size` (optional): The number of entries per page (default is 20, maximum is 100).
   - **Example:**
     ```python
     futures_client.history_positions(symbol="ETH_USDT", type=1) 
     ```

#### 5. `open_positions`
   - **Description:**  Retrieves the user's currently open positions.
   - **Permissions Required:** Trade reading permission
   - **Rate Limit:** 20 times/2 seconds
   - **Parameters:**
     - `symbol` (optional): Filters positions by contract.
   - **Example:**
     ```python
     futures_client.open_positions(symbol="ETH_USDT") 
     futures_client.open_positions()  # Retrieves all open positions
     ```

#### 6. `funding_records`
   - **Description:** Retrieves the user's funding rate history.
   - **Permissions Required:** Trade reading permission
   - **Rate Limit:** 20 times/2 seconds
   - **Parameters:**
     - `symbol` (optional): Filters records by contract.
     - `position_id` (optional): Filters records by position ID.
     - `page_num` (optional): The page number for pagination (default is 1).
     - `page_size` (optional): The number of entries per page (default is 20, maximum is 100).
   - **Example:**
     ```python
     futures_client.funding_records(symbol="ETH_USDT", position_id=123456789) 
     ```

#### 7. `open_orders`
   - **Description:** Retrieves the user's currently open orders.
   - **Permissions Required:** Trade reading permission
   - **Rate Limit:** 20 times/2 seconds
   - **Parameters:**
     - `symbol` (optional): Filters orders by contract.
     - `page_num` (optional): The page number for pagination (default is 1).
     - `page_size` (optional): The number of entries per page (default is 20, maximum is 100).
   - **Example:**
     ```python
     futures_client.open_orders(symbol="LTC_USDT")
     ```

#### 8. `history_orders`
   - **Description:** Retrieves the user's historical order information.
   - **Permissions Required:** Trade reading permission
   - **Rate Limit:** 20 times/2 seconds
   - **Parameters:**
     - `symbol` (optional): Filters orders by contract.
     - `states` (optional):  Filters orders by a comma-separated list of order states. 
     - `category` (optional): Filters orders by category.
     - `start_time` (optional): Filters orders by start time in Unix timestamp milliseconds.
     - `end_time` (optional): Filters orders by end time in Unix timestamp milliseconds.
     - `side` (optional): Filters orders by order side.
     - `page_num` (optional): The page number for pagination (default is 1).
     - `page_size` (optional): The number of entries per page (default is 20, maximum is 100).
   - **Example:**
     ```python
     futures_client.history_orders(symbol="LTC_USDT", states="FILLED,CANCELED", start_time=1660000000000, end_time=1660909200000) 
     ```

#### 9. `get_order_external`
   - **Description:** Retrieves order details using an external order ID.
   - **Permissions Required:** Trade reading permission
   - **Rate Limit:** 20 times/2 seconds
   - **Parameters:**
     - `symbol`: The contract name.
     - `external_oid`: The external order ID.
   - **Example:**
     ```python
     futures_client.get_order_external(symbol="LTC_USDT", external_oid="your_external_order_id") 
     ```

#### 10. `get_order`
   - **Description:**  Retrieves order details using the MEXC order ID.
   - **Permissions Required:** Trade reading permission
   - **Rate Limit:** 20 times/2 seconds
   - **Parameters:**
     - `order_id`: The MEXC order ID.
   - **Example:**
     ```python
     futures_client.get_order(order_id=1234567890) 
     ```

#### 11. `batch_query`
   - **Description:** Retrieves details for multiple orders using their MEXC order IDs.
   - **Permissions Required:** Trade reading permission
   - **Rate Limit:** 5 times/2 seconds
   - **Parameters:**
     - `order_ids`: A list or comma-separated string of MEXC order IDs (maximum 50 orders).
   - **Example:**
     ```python
     futures_client.batch_query(order_ids=[12345, 67890, 101112])
     futures_client.batch_query(order_ids="12345,67890,101112")
     ```

#### 12. `deal_details`
   - **Description:**  Retrieves detailed information about the fills associated with a specific order.
   - **Permissions Required:** Trade reading permission
   - **Rate Limit:** 20 times/2 seconds
   - **Parameters:**
     - `order_id`: The MEXC order ID.
   - **Example:**
     ```python
     futures_client.deal_details(order_id=9876543210)
     ```

#### 13. `order_deals`
   - **Description:**  Retrieves detailed transaction (fill) information for the user's orders within a specified time range.
   - **Permissions Required:** Trade reading permission
   - **Rate Limit:** 20 times/2 seconds
   - **Parameters:**
     - `symbol`: The contract name.
     - `start_time` (optional): The start time of the query range in Unix timestamp milliseconds. (Defaults to 7 days ago, max range 90 days). 
     - `end_time` (optional): The end time of the query range in Unix timestamp milliseconds. (Must be within 90 days of `start_time`).
     - `page_num` (optional): The page number for pagination (default is 1).
     - `page_size` (optional): The number of entries per page (default is 20, maximum is 100).
   - **Example:**
     ```python
     futures_client.order_deals(symbol="XRP_USDT", start_time=1659500000000, end_time=1659586400000) 
     ```

#### 14. `get_trigger_orders`
   - **Description:** Retrieves a list of the user's trigger orders.
   - **Permissions Required:** Trade reading permission
   - **Rate Limit:** 20 times/2 seconds
   - **Parameters:**
     - `symbol` (optional): Filters orders by contract.
     - `states` (optional): Filters orders by a comma-separated list of trigger order states.
     - `start_time` (optional): The start time of the query range in Unix timestamp milliseconds. (Defaults to 7 days ago, max range 90 days).
     - `end_time` (optional): The end time of the query range in Unix timestamp milliseconds. (Must be within 90 days of `start_time`).
     - `page_num`: The page number for pagination (default is 1).
     - `page_size`: The number of entries per page (default is 20, maximum is 100).
   - **Example:**
     ```python
     futures_client.get_trigger_orders(symbol="XRP_USDT", states="2,4") 
     ```

#### 15. `get_stop_limit_orders`
   - **Description:**  Retrieves the user's stop-limit orders.
   - **Rate Limit:** 20 times/2 seconds
   - **Parameters:**
     - `symbol` (optional): Filters orders by contract.
     - `is_finished` (optional): Filters by order status (0 for uncompleted, 1 for completed).
     - `start_time` (optional): The start time of the query range in Unix timestamp milliseconds. (Defaults to 7 days ago, max range 90 days).
     - `end_time` (optional): The end time of the query range in Unix timestamp milliseconds. (Must be within 90 days of `start_time`).
     - `page_num`: The page number for pagination (default is 1).
     - `page_size`: The number of entries per page (default is 20, maximum is 100).
   - **Example:**
     ```python
     futures_client.get_stop_limit_orders(symbol="XRP_USDT", is_finished=0) 
     ```

#### 16. `risk_limit`
   - **Description:** Retrieves the user's risk limits.
   - **Permissions Required:** Trade reading permission
   - **Rate Limit:** 20 times/2 seconds
   - **Parameters:**
      - `symbol` (optional):  If provided, retrieves risk limits for the specified contract; otherwise, retrieves risk limits for all contracts.
   - **Example:**
     ```python
     futures_client.risk_limit(symbol="DOT_USDT")
     futures_client.risk_limit()  # for all symbols 
     ```

#### 17. `tiered_fee_rate`
   - **Description:** Retrieves the user's current fee rates.
   - **Permissions Required:** Trade reading permission
   - **Rate Limit:** 20 times/2 seconds
   - **Parameters:**
     - `symbol` (optional): If provided, retrieves fee rates for the specified contract; otherwise, retrieves fee rates for all contracts.
   - **Example:**
     ```python
     futures_client.tiered_fee_rate(symbol="DOT_USDT")
     futures_client.tiered_fee_rate()  # for all symbols 
     ```

#### 18. `change_margin`
   - **Description:**  Modifies (adds to or reduces) the margin for a position.
   - **Permissions Required:** Trading permission
   - **Rate Limit:** 20 times/2 seconds
   - **Parameters:**
      - `position_id`:  The ID of the position to modify.
      - `amount`: The amount of margin to add or reduce.
      - `type`: The operation type ("ADD" for increasing margin, "SUB" for reducing).
   - **Example:**
     ```python
     futures_client.change_margin(position_id=1234567, amount=0.01, type="ADD") 
     ```

#### 19. `get_leverage`
   - **Description:** Retrieves the current leverage setting for a contract.
   - **Permissions Required:** Trading permission
   - **Rate Limit:** 20 times/2 seconds
   - **Parameters:**
      - `symbol`: The contract name.
   - **Example:**
     ```python
     futures_client.get_leverage(symbol="DOT_USDT")
     ```

#### 20. `change_leverage`
   - **Description:** Modifies the leverage for a position or sets the initial leverage for a new position.
   - **Permissions Required:** Trading permission
   - **Rate Limit:** 20 times/2 seconds
   - **Parameters:**
      - `position_id`:  The ID of the position (required if modifying an existing position).
      - `leverage`:  The desired leverage level.
      - `open_type` (optional):  Required if there is no existing position; specifies the position type (1 for isolated, 2 for cross).
      - `symbol` (optional):  Required if there is no existing position; specifies the contract.
      - `position_type` (optional): Required if there is no existing position; specifies the direction (1 for long, 2 for short).
   - **Example:**
     ```python
     # Modify leverage for an existing position:
     futures_client.change_leverage(position_id=1234567, leverage=25)  
     # Set leverage for a new position:
     futures_client.change_leverage(open_type=1, symbol="DOT_USDT", position_type=1, leverage=50)  
     ```

#### 21. `get_position_mode`
   - **Description:** Retrieves the user's current position mode (hedge mode or one-way mode).
   - **Permissions Required:** Trading permission
   - **Rate Limit:** 20 times/2 seconds
   - **Parameters:** None
   - **Example:**
     ```python
     futures_client.get_position_mode() 
     ```

#### 22. `change_position_mode`
   - **Description:**  Switches the user's position mode between hedge mode and one-way mode. **Important:** This change can only be made when there are no active orders or open positions.
   - **Permissions Required:** Trading permission
   - **Rate Limit:** 20 times/2 seconds
   - **Parameters:**
      - `position_mode`:  The desired position mode (1 for Hedge, 2 for One-way).
   - **Example:**
     ```python
     futures_client.change_position_mode(position_mode=2)  # Switch to One-way mode 
     ```

#### 23. `order`
   - **Description:**  Places a new order. 
   - **Permissions Required:** Trading permission
   - **Rate Limit:** 20 times/2 seconds
   - **Parameters:**
      - `symbol`: The contract name.
      - `price`: The order price.
      - `vol`: The order volume (quantity).
      - `side`:  The order side (1 for open long, 2 for close short, 3 for open short, 4 for close long).
      - `type`:  The order type (1 for limit, 2 for post-only, 3 for IOC, 4 for FOK, 5 for market, 6 for market-to-current).
      - `open_type`: The position type (1 for isolated, 2 for cross).
      - `position_id` (optional):  Recommended when closing a position.
      - `leverage` (optional):  Required for isolated margin.
      - `external_oid` (optional): An external order ID.
      - `stop_loss_price` (optional): Stop-loss price.
      - `take_profit_price` (optional):  Take-profit price.
      - `position_mode` (optional): Position mode (1 for hedge, 2 for one-way). Defaults to the user's current setting.
      - `reduce_only` (optional):  If True, allows only reducing existing positions. Only applies to one-way mode. Defaults to False.
   - **Example:**
     ```python
     futures_client.order(symbol="BTC_USDT", price=40000, vol=0.01, side=1, type=1, open_type=1, leverage=10)
     ```

#### 24. `bulk_order`
   - **Description:** Places multiple orders in a single request.
   - **Permissions Required:** Trading permission
   - **Rate Limit:** 1 time/2 seconds
   - **Parameters:**
      - `symbol`: The contract name.
      - `price`: The order price.
      - `vol`:  The order volume (quantity).
      - `side`: The order side (1 for open long, 2 for close short, 3 for open short, 4 for close long).
      - `type`: The order type (1 for limit, 2 for post-only, 3 for IOC, 4 for FOK, 5 for market, 6 for market-to-current).
      - `open_type`: The position type (1 for isolated, 2 for cross).
      - `position_id` (optional): Recommended when closing a position.
      - `external_oid` (optional): An external order ID. Returns the existing order ID if the external ID is already in use. 
      - `stop_loss_price` (optional): Stop-loss price.
      - `take_profit_price` (optional): Take-profit price.
   - **Example:**
     ```python
     order_data = [
         {"symbol": "BTC_USDT", "price": 40000, "vol": 0.01, "side": 1, "type": 1, "open_type": 1},
         {"symbol": "ETH_USDT", "price": 3000, "vol": 0.1, "side": 3, "type": 1, "open_type": 1}
     ]
     futures_client.bulk_order(**order_data) 
     ```

#### 25. `cancel_order`
   - **Description:**  Cancels one or more orders.
   - **Permissions Required:** Trading permission
   - **Rate Limit:** 20 times/2 seconds
   - **Parameters:**
      - `order_id`:  A single order ID or a list of order IDs to cancel (maximum 50 orders).
   - **Example:**
     ```python
     futures_client.cancel_order(order_id=1234567890)  # Cancel a single order
     futures_client.cancel_order(order_id=[12345, 67890, 101112])  # Cancel multiple orders
     ```

#### 26. `cancel_order_with_external`
   - **Description:** Cancels an order using its external order ID.
   - **Rate Limit:** 20 times/2 seconds
   - **Parameters:**
      - `symbol`: The contract name.
      - `external_oid`:  The external order ID to cancel.
   - **Example:**
     ```python
     futures_client.cancel_order_with_external(symbol="BTC_USDT", external_oid="your_external_order_id_123")
     ```

#### 27. `cancel_all`
   - **Description:**  Cancels all open orders for a specific contract or for all contracts.
   - **Permissions Required:** Trading permission
   - **Rate Limit:** 20 times/2 seconds
   - **Parameters:**
      - `symbol` (optional):  The contract name. If not provided, cancels all open orders for all contracts.
   - **Example:**
     ```python
     futures_client.cancel_all(symbol="ETH_USDT")  # Cancel all ETH/USDT orders
     futures_client.cancel_all()  # Cancel all open orders for all contracts 
     ```

#### 28. `change_risk_level`
   - **Description:** (Details not provided in the original code snippet; refer to MEXC API documentation for usage).
   - **Example:**
      ```python
      futures_client.change_risk_level() 
      ```

#### 29. `trigger_order`
   - **Description:**  Places a trigger order (a type of advanced order that executes when certain conditions are met).
   - **Parameters:**
      - `symbol`: The contract name.
      - `vol`: The order volume (quantity).
      - `side`: The order side (1 for open long, 2 for close short, 3 for open short, 4 for close long).
      - `open_type`: The position type (1 for isolated, 2 for cross).
      - `trigger_price`: The price that triggers the order.
      - `trigger_type`:  The trigger condition (1 for greater than or equal to, 2 for less than or equal to).
      - `execute_cycle`:  The order duration (1 for 24 hours, 2 for 7 days).
      - `order_type`:  The order type (1 for limit, 2 for post-only, 3 for IOC, 4 for FOK, 5 for market).
      - `trend`:  The price used for the trigger (1 for last price, 2 for fair price, 3 for index price).
      - `price` (optional): The limit price for the order (if applicable).
      - `leverage` (optional): The leverage for the order (if applicable).
   - **Example:**
     ```python
     futures_client.trigger_order(symbol="BTC_USDT", vol=0.005, side=1, open_type=1, 
     trigger_price=41000, trigger_type=1, execute_cycle=1, order_type=1, trend=1)
     ```

#### 30. `cancel_trigger_order`
   - **Description:** Cancels a specific trigger order.
   - **Parameters:**
      - `order_id`: The ID of the trigger order to cancel.
   - **Example:**
     ```python
     futures_client.cancel_trigger_order(order_id=987654321) 
     ```

#### 31. `cancel_all_trigger_orders`
   - **Description:** Cancels all trigger orders for a specific contract or for all contracts.
   - **Parameters:**
      - `symbol` (optional): The contract name. If not provided, cancels all trigger orders for all contracts.
   - **Example:**
     ```python
     futures_client.cancel_all_trigger_orders(symbol="LINK_USDT")  # Cancel LINK/USDT trigger orders
     futures_client.cancel_all_trigger_orders()  # Cancel all trigger orders
     ```

#### 32. `cancel_stop_order`
   - **Description:**  Cancels a specific stop-limit order.
   - **Parameters:**
      - `order_id`:  The ID of the stop-limit order to cancel.
   - **Example:**
     ```python
     futures_client.cancel_stop_order(order_id=5678901234) 
     ```

#### 33. `cancel_all_stop_order`
   - **Description:**  Cancels all stop-limit orders, optionally filtered by position ID or contract.
   - **Parameters:**
      - `position_id` (optional): If provided, cancels stop-limit orders associated with this position ID.
      - `symbol` (optional):  If provided, cancels stop-limit orders for this contract. If neither `position_id` nor `symbol` is provided, cancels all stop-limit orders.
   - **Example:**
     ```python
     futures_client.cancel_all_stop_order(position_id=876543210)  # Cancel orders for the position
     futures_client.cancel_all_stop_order(symbol="LINK_USDT")  # Cancel LINK/USDT stop-limit orders
     futures_client.cancel_all_stop_order()  # Cancel all stop-limit orders
     ```

#### 34. `stop_limit_change_price`
   - **Description:**  Modifies the stop-loss and/or take-profit prices of an existing stop-limit order.
   - **Parameters:**
      - `order_id`:  The ID of the stop-limit order to modify.
      - `stop_loss_price` (optional):  The new stop-loss price.
      - `take_profit_price` (optional): The new take-profit price.
   - **Example:**
     ```python
     futures_client.stop_limit_change_price(order_id=3456789012, stop_loss_price=29500, take_profit_price=30500)
     ```

#### 35. `stop_limit_change_plan_price`
   - **Description:**  Modifies the stop-loss and/or take-profit prices of a trigger order that has a stop-limit order attached.
   - **Parameters:**
      - `stop_plan_order_id`: The ID of the trigger order that has the stop-limit order.
      - `stop_loss_price` (optional):  The new stop-loss price. At least one of stop_loss_price or take_profit_price must be provided and greater than 0.
      - `take_profit_price` (optional): The new take-profit price. At least one of stop_loss_price or take_profit_price must be provided and greater than 0.
   - **Example:**
     ```python
     futures_client.stop_limit_change_plan_price(stop_plan_order_id=4321098765, stop_loss_price=1450, take_profit_price=1550)  
     ```


---



## MEXC Futures API WebSocket Methods

This document outlines the available WebSocket methods for the MEXC Futures API. Each method is accompanied by a list of parameters and example values.

**Note:** This documentation reflects the API's state as of September 2021. 

### Public Channels

#### 1. `tickers_stream`

**Description:** Retrieves the latest transaction price, buy-price, sell-price, and 24-hour transaction volume for all perpetual contracts. Updates are sent every second.

**Parameters:**

- `callback` (Callable[..., None]): Function to handle incoming messages.

**Example Usage:**

```python
ws_futures_client.tickers_stream(handle_message)
```

---

#### 2. `ticker_stream`

**Description:**  Retrieves the latest transaction price, buy price, sell price, and 24-hour transaction volume for a specific contract. Updates are sent every second.

**Parameters:**

- `callback` (Callable[..., None]): Function to handle incoming messages.
- `symbol` (str): The contract symbol (e.g., "BTC_USDT").

**Example Usage:**

```python
ws_futures_client.ticker_stream(handle_message, symbol="BTC_USDT")
```

---

#### 3. `deal_stream`

**Description:** Provides real-time transaction data for a specific contract.

**Parameters:**

- `callback` (Callable[..., None]): Function to handle incoming messages.
- `symbol` (str): The contract symbol (e.g., "ETH_USDT").

**Example Usage:**

```python
ws_futures_client.deal_stream(handle_message, symbol="ETH_USDT")
```

---

#### 4. `depth_stream`

**Description:** Streams real-time order book data for a specific contract.

**Parameters:**

- `callback` (Callable[..., None]): Function to handle incoming messages.
- `symbol` (str): The contract symbol (e.g., "XRP_USDT").

**Example Usage:**

```python
ws_futures_client.depth_stream(handle_message, symbol="XRP_USDT")
```

---

#### 5. `depth_full_stream`

**Description:**  Streams the full order book for a specific contract, up to the specified limit.

**Parameters:**

- `callback` (Callable[..., None]): Function to handle incoming messages.
- `symbol` (str): The contract symbol (e.g., "LINK_USDT").
- `limit` (int, optional):  Number of price levels to include (5, 10, or 20). Defaults to 20.

**Example Usage:**

```python
ws_futures_client.depth_full_stream(handle_message, symbol="LINK_USDT", limit=10)
```

---

#### 6. `kline_stream`

**Description:**  Streams candlestick data for a specific contract and interval.

**Parameters:**

- `callback` (Callable[..., None]): Function to handle incoming messages.
- `symbol` (str): The contract symbol (e.g., "DOT_USDT").
- `interval` (str, optional): Candlestick interval. Options: "Min1", "Min5", "Min15", "Min60", "Hour1", "Hour4", "Day1", "Week1". Defaults to "Min1".

**Example Usage:**

```python
ws_futures_client.kline_stream(handle_message, symbol="DOT_USDT", interval="Hour4")
```

---

#### 7. `funding_rate_stream`

**Description:** Streams real-time funding rate updates for a specific contract.

**Parameters:**

- `callback` (Callable[..., None]): Function to handle incoming messages.
- `symbol` (str): The contract symbol (e.g., "ADA_USDT").

**Example Usage:**

```python
ws_futures_client.funding_rate_stream(handle_message, symbol="ADA_USDT")
```

---

#### 8. `index_price_stream`

**Description:** Streams real-time updates to the index price for a specific contract.

**Parameters:**

- `callback` (Callable[..., None]): Function to handle incoming messages.
- `symbol` (str): The contract symbol (e.g., "LTC_USDT").

**Example Usage:**

```python
ws_futures_client.index_price_stream(handle_message, symbol="LTC_USDT")
```

---


#### 9. `fair_price_stream`

**Description:**  Streams real-time updates to the fair price for a specific contract.

**Parameters:**

- `callback` (Callable[..., None]): Function to handle incoming messages.
- `symbol` (str): The contract symbol (e.g., "BCH_USDT").

**Example Usage:**

```python
ws_futures_client.fair_price_stream(handle_message, symbol="BCH_USDT")
```

---

### Private Channels 

**Note:** Private channels require authentication using your API key and secret.

#### 10. `order_stream`

**Description:** Streams updates on your orders.

**Parameters:**

- `callback` (Callable[..., None]): Function to handle incoming messages.
- `params` (dict, optional): Additional parameters. Refer to MEXC API documentation.

**Example Usage:**

```python
ws_futures_client.order_stream(handle_message)
```

---

#### 11. `asset_stream`

**Description:**  Streams updates on your account assets.

**Parameters:**

- `callback` (Callable[..., None]): Function to handle incoming messages.
- `params` (dict, optional): Additional parameters. Refer to MEXC API documentation.

**Example Usage:**

```python
ws_futures_client.asset_stream(handle_message)
```

---

#### 12. `position_stream`

**Description:** Streams updates on your open positions.

**Parameters:**

- `callback` (Callable[..., None]): Function to handle incoming messages.
- `params` (dict, optional): Additional parameters. Refer to MEXC API documentation.

**Example Usage:**

```python
ws_futures_client.position_stream(handle_message)
```

---

#### 13. `risk_limit_stream`

**Description:** Streams updates on your risk limit levels. 

**Parameters:**

- `callback` (Callable[..., None]): Function to handle incoming messages.
- `params` (dict, optional): Additional parameters. Refer to MEXC API documentation.

**Example Usage:**

```python
ws_futures_client.risk_limit_stream(handle_message)
```

---

#### 14. `adl_level_stream`

**Description:** Streams updates on your Auto-Deleveraging (ADL) levels.

**Parameters:**

- `callback` (Callable[..., None]): Function to handle incoming messages.
- `params` (dict, optional): Additional parameters. Refer to MEXC API documentation.

**Example Usage:**

```python
ws_futures_client.adl_level_stream(handle_message) 
```

---

#### 15. `position_mode_stream`

**Description:**  Streams updates on your position mode (e.g., One-way mode, Hedge mode).

**Parameters:**

- `callback` (Callable[..., None]): Function to handle incoming messages.
- `params` (dict, optional): Additional parameters. Refer to MEXC API documentation.

**Example Usage:**

```python
ws_futures_client.position_mode_stream(handle_message)
```

