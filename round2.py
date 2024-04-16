from datamodel import OrderDepth, UserId, TradingState, Order
from typing import List
import string
import math


AMETHYSTS = "AMETHYSTS"
STARFRUIT = "STARFRUIT"
SEASHELLS = "SEASHELLS"
ORCHID = "ORCHIDS"

# FIRST_ORCHID_ORDER = 0

ASSETS = [
    STARFRUIT,
    SEASHELLS,
    ORCHID,
]

# Mean price specificed by IMC
DEFAULT_PRICES = {
    AMETHYSTS : 10_000,
    STARFRUIT : 5_000,
    ORCHID : None,
}

# visualiser custom logger (REMOVE FOR SUBMISSION and CONVERT PRINTS)
# from logger import Logger
# logger = Logger()

class Trader:
    def __init__(self) -> None:
        # logger.print("Initialising...")

        self.position_limit = {
            AMETHYSTS : 20, 
            STARFRUIT : 20,
            ORCHID :    100, 
        }

        self.south_pos_limit = {
            ORCHID :    100, 
        }

        # self.round = 0
        self.shells = 0

        # List of price history of assets
        self.price_history = dict()
        for asset in ASSETS:
            self.price_history[asset] = []
            # Set others such as expected regresion price
        
        self.ema_price = None
        self.round = 0

        
    def starfruit_strategy(self, state: TradingState):
        
        # update ema price
        mid_price = self.get_mid_starfruit_price(state)
        
        if not self.ema_price:
            self.ema_price = mid_price
        else:
        
            # Maybe have a variable alpha, where initially alpha is high then goes lower
            alpha = 0.0
            if self.round < 50:
                alpha = 0.5
            else:
                alpha = 0.37
                
            self.ema_price = (alpha * mid_price) + ((1 - alpha) * self.ema_price)
        
        # get position
        starfruit_pos = self.get_pos(STARFRUIT, state)

        bid_volume = self.position_limit[STARFRUIT] - starfruit_pos
        ask_volume = - self.position_limit[STARFRUIT] - starfruit_pos

        orders = []

        if starfruit_pos == 0:
            # Not long nor short
            orders.append(Order(STARFRUIT, math.floor(self.ema_price - 1), bid_volume))
            orders.append(Order(STARFRUIT, math.ceil(self.ema_price + 1), ask_volume))
        
        if starfruit_pos > 0:
            # Long position
            orders.append(Order(STARFRUIT, math.floor(self.ema_price - 1), bid_volume))
            orders.append(Order(STARFRUIT, math.ceil(self.ema_price), ask_volume))

        if starfruit_pos < 0:
            # Short position
            orders.append(Order(STARFRUIT, math.floor(self.ema_price - 1), bid_volume))
            orders.append(Order(STARFRUIT, math.ceil(self.ema_price + 1), ask_volume)) # or take profits @ EMA + 1

        return orders
        
    
    # market make/take around 10k
    def amethyst_strategy(self, state: TradingState):
        
        # get position
        amethyst_pos = self.get_pos(AMETHYSTS, state)

        # find max bid/ask amount
        bid_volume = self.position_limit[AMETHYSTS] - amethyst_pos
        ask_volume = -1 * (self.position_limit[AMETHYSTS] + amethyst_pos)
             
        # price_dev = 2 # Or change back to 1
        
        # append +-1 buy/sell order
        orders = []
        orders.append(Order(AMETHYSTS, DEFAULT_PRICES[AMETHYSTS] - 2, bid_volume))
        orders.append(Order(AMETHYSTS, DEFAULT_PRICES[AMETHYSTS] + 2, ask_volume))
        
        return orders

    # made for starfruit only
    def get_mid_starfruit_price(self, state : TradingState):

        default_price = self.ema_price if self.ema_price else DEFAULT_PRICES[STARFRUIT]

        if STARFRUIT not in state.order_depths:
            return default_price

        market_bids = state.order_depths[STARFRUIT].buy_orders
        market_asks = state.order_depths[STARFRUIT].sell_orders
        if not market_asks or not market_bids:
            return default_price
        
        best_bid = max(market_bids)
        best_ask = min(market_asks)
        
        return (best_bid + best_ask)/2

    def get_pos(self, product, state: TradingState):
        # return state.position.get(product)
        # Investigate later
        return state.position.get(product, 0) 
    
    def orchid_strategy(self, state: TradingState):
        orders = []
        
        # Local Prices
        local_bids = state.order_depths[ORCHID].buy_orders
        local_asks = state.order_depths[ORCHID].sell_orders

        best_local_bid = max(local_bids)
        best_local_ask = min(local_asks)

        # International Prices
        observations = state.observations.conversionObservations[ORCHID]
        #sunlight = observations.sunlight
        #humidity = observations.humidity
        transport_fees = observations.transportFees 
        import_tariff = observations.importTariff
        export_tariff = observations.exportTariff
        south_bid = observations.bidPrice
        south_ask = observations.askPrice

        south_buy = south_bid + import_tariff + transport_fees
        south_sell = south_ask + export_tariff + transport_fees

        curr_pos = self.position_limit[ORCHID]
        conversion = 0
        if best_local_bid > south_sell & curr_pos <= 0:
            bid_volume = self.position_limit[ORCHID] + curr_pos
            orders.append(Order(ORCHID, math.floor(best_local_bid), bid_volume))
            return orders, conversion
        if best_local_bid < south_sell & curr_pos > 0:
            conversion = -curr_pos
            return orders, conversion
        # if best_local_ask - 0.5 > south_buy - 0.5 & curr_pos <= 0:
        #     ask_volume = (self.position_limit[AMETHYSTS] + curr_pos)
        #     orders.append(Order(ORCHID, best_local_bid, bid_volume))
        #     return orders, conversion
        # if best_local_ask - 0.5 > south_buy - 0.5 & curr_pos > 0:
        #     ask_volume = self.position_limit[ORCHID] + curr_pos
        #     conversion = -curr_pos
        #     return orders, conversion

        return orders, conversion
    
    def run(self, state: TradingState):

        # logger.print("traderData: " + state.traderData)
        # logger.print("Observations: " + str(state.observations))
        
        # only running amethyst strategy
        result = {}
        result[AMETHYSTS] = self.amethyst_strategy(state)
        result[STARFRUIT] = self.starfruit_strategy(state)
        result[ORCHID], conversions = self.orchid_strategy(state)

        # orchid_strat = self.get_orchid_strategy(state)
        # result[ORCHID] = self.orchid_strategy(state, orchid_strat)
    
        traderData = "SAMPLE" # String value holding Trader state data required. It will be delivered as TradingState.traderData on next execution.
        
        #conversions = 1
        
        # Need to flush to visualiser (include before return always)
        # logger.flush(state, result, conversions, traderData)
        self.round += 1
        return result, conversions, traderData

