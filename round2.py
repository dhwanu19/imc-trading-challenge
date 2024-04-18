import pandas as pd
from datamodel import OrderDepth, UserId, TradingState, Order
from typing import Dict, List, Union
import string
import math
import numpy as np


AMETHYSTS = "AMETHYSTS"
STARFRUIT = "STARFRUIT"
SEASHELLS = "SEASHELLS"
ORCHID = "ORCHIDS"

CHOCOLATE = "CHOCOLATE"
STRAWBERRIES = "STRAWBERRIES"
ROSES = "ROSES"
GIFT_BASKET = "GIFT_BASKET" # 4C, 6S, 1R

WINDOW = 200

# FIRST_ORCHID_ORDER = 0

ASSETS = [
    STARFRUIT,
    SEASHELLS,
    ORCHID,
    CHOCOLATE,
    STRAWBERRIES,
    ROSES,
    GIFT_BASKET,
]

# Mean price specificed by IMC
DEFAULT_PRICES = {
    AMETHYSTS : 10_000,
    STARFRUIT : 5_000,
    ORCHID : None,
    CHOCOLATE: 8000,
    STRAWBERRIES: 4000,
    ROSES: 14750,
    GIFT_BASKET: 71000,
}

# visualiser custom logger (REMOVE FOR SUBMISSION and CONVERT PRINTS)
from logger import Logger
logger = Logger()

class Trader:
    def __init__(self) -> None:
        # logger.print("Initialising...")

        self.position_limit = {
            AMETHYSTS : 20, 
            STARFRUIT : 20,
            ORCHID :    100, 
            CHOCOLATE : 250,
            STRAWBERRIES : 350,
            ROSES : 60, 
            GIFT_BASKET : 60,
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
        self.arbitrage_strat = False

        self.prices : Dict[ASSETS, pd.Series] = { # type: ignore
            "SPREAD":pd.Series(),
        }
        
        
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

    def get_mid_price(self, product, state : TradingState):


        default_price = DEFAULT_PRICES[product]

        if product not in state.order_depths:
            return default_price

        market_bids = state.order_depths[product].buy_orders
        if len(market_bids) == 0:
            # There are no bid orders in the market (midprice undefined)
            return default_price
        
        market_asks = state.order_depths[product].sell_orders
        if len(market_asks) == 0:
            # There are no bid orders in the market (mid_price undefined)
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
        conversion = 0
        
        # International Prices
        observations = state.observations.conversionObservations[ORCHID]

        transport_fees = observations.transportFees 
        import_tariff = observations.importTariff
        export_tariff = observations.exportTariff
        south_bid = observations.bidPrice
        south_ask = observations.askPrice
        
        import_amount = south_ask + import_tariff + transport_fees       # cost of importing from south (buy at ask, add tariff cost, add transport cost)
        export_amount = south_bid - export_tariff - transport_fees       # amount received by selling to south (sell at bid, remove tariff cost, remove transport cost)

        # Domestic Prices
        max_local_bid = max(state.order_depths[ORCHID].buy_orders)      # max price bot is willing to buy at locally
        min_local_ask = min(state.order_depths[ORCHID].sell_orders)     # max price bot is selling to sell at locally
        
        orchid_pos = self.get_pos(ORCHID, state) # pos > 0 = own (buy), pos < 0 = owe (sell)

        our_bid_volume = self.position_limit[ORCHID] - orchid_pos
        our_ask_volume = - self.position_limit[ORCHID] - orchid_pos
        
        local_ask_export_south = export_amount - min_local_ask
        local_bid_import_south = max_local_bid - import_amount

        if orchid_pos != 0:
            conversion = -orchid_pos
        # BUY LOCAL SELL SOUTH
        elif local_ask_export_south < local_bid_import_south: # IF PROFITABLE (SELL SOUTH > BUY LOCAL)
            orders.append(Order(ORCHID, math.ceil(import_amount), our_ask_volume))   
        # BUY SOUTH SELL LOCAL
        else:
            orders.append(Order(ORCHID, math.floor(export_amount), our_bid_volume))
           
        return orders, conversion

    def save_prices_product(
        self, 
        product, 
        state: TradingState,
        price: Union[float, int, None] = None, 
    ):
        if not price:
            price = self.get_mid_price(product, state)

        self.prices[product] = pd.concat([
            self.prices[product],
            pd.Series({state.timestamp: price})
        ])


    def round3_strategy(self, state: TradingState):
        chocolate_orders = []
        strawberry_orders = []
        rose_orders = []
        basket_orders = []

        def create_round3_orders(doBuyBasket: bool) -> List[List[Order]]:
            # Basket = 4C, 6S, 1R
            trade_volume = 2
            
            if doBuyBasket:
                volume_sign = 1
                basket_price = 1e7
                individual_price = 1
            else:
                volume_sign = -1
                basket_price = 1
                individual_price = 1e7

            basket_orders.append(Order(GIFT_BASKET, basket_price, volume_sign * trade_volume))
            chocolate_orders.append(Order(CHOCOLATE, individual_price, 4 * volume_sign * trade_volume))
            strawberry_orders.append(Order(STRAWBERRIES, individual_price, 6 * volume_sign * trade_volume))
            rose_orders.append(Order(ROSES, individual_price, 1 * volume_sign * trade_volume))


        # Basket = 4C, 6S, 1R
        basket_mp = self.get_mid_price(GIFT_BASKET, state)
        chocolate_mp = self.get_mid_price(CHOCOLATE, state)
        strawberry_mp = self.get_mid_price(STRAWBERRIES, state)
        rose_mp = self.get_mid_price(ROSES, state)

        basket_pos = self.get_pos(GIFT_BASKET, state)

        spread = basket_mp - (4 * chocolate_mp + 6 * strawberry_mp + rose_mp)

        self.save_prices_product(
            "SPREAD",
            state,
            spread
        )

        avg_spread = self.prices["SPREAD"].rolling(WINDOW).mean()
        std_spread = self.prices["SPREAD"].rolling(WINDOW).std()
        spread_5 = self.prices["SPREAD"].rolling(5).mean()

        if not np.isnan(avg_spread.iloc[-1]):
            avg_spread = avg_spread.iloc[-1]
            std_spread = std_spread.iloc[-1]
            spread_5 = spread_5.iloc[-1]
            print(f"Average spread: {avg_spread}, Spread5: {spread_5}, Std: {std_spread}")


            if abs(basket_pos) <= self.position_limit[GIFT_BASKET] - 2:
                if spread_5 < avg_spread - 2*std_spread:  # buy basket
                    buy_basket = True
                    create_round3_orders(buy_basket)

                elif spread_5 > avg_spread + 2*std_spread: # sell basket
                    buy_basket = False 
                    create_round3_orders(buy_basket)

            else: # abs(position_basket) >= POSITION_LIMITS[PICNIC_BASKET]-10
                if basket_pos > 0 : # sell basket
                    if spread_5 > avg_spread + 2*std_spread:
                        buy_basket = False
                        create_round3_orders(buy_basket)

                else: # buy basket
                    if spread_5 < avg_spread - 2*std_spread:
                        buy_basket = True
                        create_round3_orders(buy_basket)

        return basket_orders, chocolate_orders, strawberry_orders, rose_orders

    def run(self, state: TradingState):

        # logger.print("traderData: " + state.traderData)
        # logger.print("Observations: " + str(state.observations))
        
        # only running amethyst strategy
        result = {}
        conversions = 0
        # result[AMETHYSTS] = self.amethyst_strategy(state)
        # result[STARFRUIT] = self.starfruit_strategy(state)
        # result[ORCHID], conversions = self.orchid_strategy(state)

        
        result[GIFT_BASKET], result[CHOCOLATE], result[STRAWBERRIES], result[ROSES] = self.round3_strategy(state)
        # orchid_strat = self.get_orchid_strategy(state)
        # result[ORCHID] = self.orchid_strategy(state, orchid_strat)
    
        traderData = "SAMPLE" # String value holding Trader state data required. It will be delivered as TradingState.traderData on next execution.
        
        #conversions = 1
        
        # Need to flush to visualiser (include before return always)
        logger.flush(state, result, conversions, traderData)
        self.round += 1
        return result, conversions, traderData

