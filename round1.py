from datamodel import OrderDepth, UserId, TradingState, Order
from typing import List
import string

AMETHYSTS = "AMETHYSTS"
STARFRUIT = "STARFRUIT"
SEASHELLS = "SEASHELLS"

ASSETS = [
    STARFRUIT,
    SEASHELLS,
]

# Mean price specificed by IMC
DEFAULT_PRICES = {
    AMETHYSTS : 10_000,
    STARFRUIT : 5_000,
}

class Trader:
    def __init__(self) -> None:
        print("Initialising...")

        self.position_limit = (
            AMETHYSTS : 20, 
            STARFRUIT : 20, 
        )

        # self.round = 0
        self.shells = 0

        # List of price history of assets
        self.price_history = dict()
        for asset in ASSETS:
            asset.price_history[asset] = []
            # Set others such as expected regresion price
        
    def starfruit_strategy():
        pass
    
    # market make/take around 10k
    def amethyst_strategy(self, state: TradingState):
        
        # get position
        amethyst_pos = self.get_pos(AMETHYSTS, state)

        # find max bid/ask amount
        bid_volume = self.position_limit[AMETHYSTS] - amethyst_pos
        ask_volume = -1 * (self.position_limit[AMETHYSTS] + amethyst_pos)
             
        price_dev = 1
        
        # append +-1 buy/sell order
        orders = []
        orders.append(Order(AMETHYSTS, DEFAULT_PRICES[AMETHYSTS] - price_dev, bid_volume))
        orders.append(Order(AMETHYSTS, DEFAULT_PRICES[AMETHYSTS] + price_dev, ask_volume))
        
        return orders
    
    def get_pos(self, product, state: TradingState):
        # return state.position.get(product)
        # Investigate later
        return state.position.get(product, 0) 
    
    
    def run(self, state: TradingState):
        # Only method required. It takes all buy and sell orders for all symbols as an input, and outputs a list of orders to be sent
        print("traderData: " + state.traderData)
        print("Observations: " + str(state.observations))
        result = {}
        for product in state.order_depths:
            order_depth: OrderDepth = state.order_depths[product]
            orders: List[Order] = []
            acceptable_price = 10;  # Participant should calculate this value
            print("Acceptable price : " + str(acceptable_price))
            print("Buy Order depth : " + str(len(order_depth.buy_orders)) + ", Sell order depth : " + str(len(order_depth.sell_orders)))
    
            if len(order_depth.sell_orders) != 0:
                best_ask, best_ask_amount = list(order_depth.sell_orders.items())[0]
                if int(best_ask) < acceptable_price:
                    print("BUY", str(-best_ask_amount) + "x", best_ask)
                    orders.append(Order(product, best_ask, -best_ask_amount))
    
            if len(order_depth.buy_orders) != 0:
                best_bid, best_bid_amount = list(order_depth.buy_orders.items())[0]
                if int(best_bid) > acceptable_price:
                    print("SELL", str(best_bid_amount) + "x", best_bid)
                    orders.append(Order(product, best_bid, -best_bid_amount))
            
            result[product] = orders
    
    
        traderData = "SAMPLE" # String value holding Trader state data required. It will be delivered as TradingState.traderData on next execution.
        
        conversions = 1
        return result, conversions, traderData

