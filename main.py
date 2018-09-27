import gdax
import time
import decimal
import tweepy

# Twitter part

# enter the corresponding information from your Twitter application:
CONSUMER_KEY = ''  # keep the quotes, replace this with your consumer key
CONSUMER_SECRET = ''  # keep the quotes, replace this with your consumer secret key
ACCESS_KEY = ''  # keep the quotes, replace this with your access token
ACCESS_SECRET = ''  # keep the quotes, replace this with your access token secret
auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
auth.set_access_token(ACCESS_KEY, ACCESS_SECRET)
api = tweepy.API(auth)

key = '' #GDAX
b64sec = '' #GDAX
passphrase = ''

auth_client = gdax.AuthenticatedClient(key, b64sec, passphrase)
public_client = gdax.PublicClient()

# If state of bot is =1, then it has a buy order out, if =0, it has a sell order
state_bot = 1

# Enter the amount of ETH you want to give the bot access to trade with
starting_ETH = '0.01'

# Enter the price you want the first sell order to be
# starting_price = '142.1'

# On/Off switch for bot
run = True

initial_sale = True
last_order_id = None

current_price = None
wallet_EUR = 0
wallet_ETH = 0
total_transactions = 0

# In a declining market, one should use a higher buy margin than sell, and vice versa on a rising market
profit_perc_sell = 0.01
profit_perc_buy = 0.01

profit_session_eur = 0
order_book = []


def sell_ETH(price, amount, state, order_book):
    auth_client.sell(price=price, size=amount, product_id='ETH-EUR')
    order_price = float(price) * float(amount)
    order_book.append(order_price)
    print("Put out sell order for ", amount, "ETH at ", price, "EUR.")
    state = 0
    wallet = eur_wallet_calc(price, amount)
    return state, wallet, order_book


def buy_ETH(price, amount, state, order_book):
    auth_client.buy(price=price, size=amount, product_id='ETH-EUR')
    order_price = float(price) * float(amount)
    order_book.append(order_price)
    print("Put out buy order for ", amount, "ETH at ", price, "EUR.")
    state = 1
    wallet = eth_wallet_calc(amount)
    return state, wallet, order_book


def eur_wallet_calc(price, amount):
    content = float(price) * float(amount)
    content = content - (content * 0.003)
    return content


def eth_wallet_calc(amount):
    content = float(amount) - (float(amount) * 0.003)
    return content


def round_number(number, decimals):
    amount_decimal = decimal.Decimal(number)
    round_amouth = round(amount_decimal, decimals)
    return round_amouth


def find_order_info(info):
    orders_in = auth_client.get_orders()
    last_order_in = orders_in[0]
    last_order_dict_in = last_order_in[0]
    string_order_id = str(last_order_dict_in[info])

    return string_order_id


def get_price_sell():
    order_book = public_client.get_product_order_book(product_id='ETH-EUR', level=1)
    asks = order_book['asks']
    asks = asks[0]
    asks = float(asks[0])
    return asks


def get_price_buy():
    order_book = public_client.get_product_order_book(product_id='ETH-EUR', level=1)
    bids = order_book['bids']
    bids = bids[0]
    bids = float(bids[0])
    return bids


def calc_profit(order_book):
    tot_profit = 0
    for i in range(1, len(order_book)):
        profit = abs(order_book[i - 1] - order_book[i])
        tot_profit = tot_profit + profit
    return tot_profit


# Calculculating start price
asking_price = get_price_sell()
starting_price = str(asking_price)

while run:

    if initial_sale:
        print("Placing the initial sell order..")
        state_bot, wallet_EUR, order_book = sell_ETH(starting_price, starting_ETH, state_bot, order_book)
        time.sleep(2)

        try:
            last_order_id = find_order_info('id')
        except:
            run = False

        print("Initial order made")
        total_transactions = total_transactions + 1
        # print("Placed order to sell ", starting_ETH, "ETH at ", starting_price, "EUR.")
        message = "Initially placed order for " + starting_ETH + "ETH at " + starting_price + "EUR"
        api.update_status(message)
        initial_sale = False
        current_price = float(starting_price) - (float(starting_price) * profit_perc_buy)

    else:
        orders = auth_client.get_orders()
        try:
            last_order = orders[0]
            last_order_dict = last_order[0]
            num_orders = len(last_order)
            profit_session_eur = calc_profit(order_book)
            profit_session_eur = round(profit_session_eur, 2)

            # print(orders)
            print("Last order id: ", last_order_dict['id'])
            print("Order price: ", last_order_dict['price'])
            print("Order size: ", last_order_dict['size'])
            print("Order action: ", last_order_dict['side'])
            print("From-To: ", last_order_dict['product_id'])
            print("Total active orders: ", num_orders)
            print("Starting ETH: ", starting_ETH, "starting price: ", starting_price)
            print("ETH wallet: ", wallet_ETH)
            print("EUR wallet: ", wallet_EUR)
            print("Transactions made this session: ", total_transactions)
            print("Profit this session: ", profit_session_eur, "EUR")
            print(" ")
            try:
                print(order_book)

            except:
                continue

            if num_orders >= 2:
                auth_client.cancel_all(product='ETH-EUR')
                auth_client.cancel_all(product='EUR-ETH')
                print("Canceled all orders!")
                print("The bot will now stop..")
                run = False


        except:
            print("There does not seem to be any current orders.")
            print("Placing new order based on last order")

            if state_bot == 1:
                sold_message = "Completed order: " + last_order_id
                api.update_status(sold_message)
                print("Trying to make a sell order..")
                amount_eth = wallet_ETH
                current_price = get_price_sell()
                current_price = current_price + (current_price * profit_perc_sell)
                round_amount_eth = round_number(amount_eth, 5)
                round_price = round_number(current_price, 2)
                state_bot, wallet_EUR, order_book = sell_ETH(str(round_price), str(round_amount_eth), state_bot,
                                                             order_book)
                time.sleep(1)

                try:
                    last_order_id = find_order_info('id')
                except:
                    run = False

                message = "Placed sell order for " + str(round_amount_eth) + "ETH at " + str(round_price) + "EUR"
                api.update_status(message)
                wallet_ETH = 0
                total_transactions = total_transactions + 1
                print("Current bot state: ", state_bot)

            else:
                sold_message = "Completed order: " + last_order_id
                api.update_status(sold_message)
                current_price = current_price - (current_price * profit_perc_buy)
                amount_eth = wallet_EUR / current_price
                round_amount_eth = round_number(amount_eth, 5)
                round_price = round_number(current_price, 2)
                state_bot, wallet_ETH, order_book = buy_ETH(str(round_price), str(round_amount_eth), state_bot,
                                                            order_book)
                time.sleep(1)

                try:
                    last_order_id = find_order_info('id')
                except:
                    run = False

                message = "Placed buy order for " + str(round_amount_eth) + "ETH at " + str(round_price) + "EUR"
                api.update_status(message)
                wallet_EUR = 0
                total_transactions = total_transactions + 1
                print("Current bot state: ", state_bot)

    time.sleep(5)
