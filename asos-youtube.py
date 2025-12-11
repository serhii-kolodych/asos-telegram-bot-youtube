# 📺 watch Python Tutorial for this code on YouTube: https://www.youtube.com/@serhiikolodych

# ✅ 1. Insert your TOKENs in config.py file

# ✅ 2. Don't forget to install libraries, by typing in your terminal:
# pip install datetime==4.4 requests==2.26.0 SQLAlchemy==1.4.23 aiogram==2.9 asyncio==3.4.3 PyMySQL==1.1.0 psycopg2

# pip install datetime==4.4 requests==2.26.0 SQLAlchemy==1.4.23 aiogram==2.25.1 asyncio==3.4.3 PyMySQL==1.1.0 psycopg2

# ✅ 3. You can run the script now! 🚀

import config_a # our config.py file with TOKENs for our bot and database
import datetime # so we can write time and date of when we inserted product in database
import requests # to receive json from website
from sqlalchemy import create_engine, text # engine to work with database
from aiogram import Bot, Dispatcher, executor, types # for telegram bot
from aiogram.types import Message # to read and write messages in telegram bot
import asyncio # to send updates every ? seconds

# Import your bot's TOKEN and engine_token from a configuration file (config.py)
TOKEN = config_a.TOKEN
engine_token = config_a.engine_token

# Initialize the Telegram bot using the provided TOKEN
bot = Bot(token=TOKEN)

# Create a Dispatcher for handling incoming messages and commands
dp = Dispatcher(bot)

# Create an empty dictionary to store user tasks (sending updates to those who /start the bot)
user_tasks = {}

# headers to access url, accept: all, user-agent (browser): copied from my browser
headers = {"accept": "*/*", "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36 OPR/102.0.0.0"}

# Create a database engine using SQLAlchemy, with SSL settings
# engine = create_engine(engine_token, connect_args={"ssl": {"ca": "/etc/ssl/cert.pem"}})
engine = create_engine(engine_token)


# Define global variables more_what, offset, and order_number (for /more function)
global more_what
global offset
global order_number


# Define a message handler for the /start command
@dp.message_handler(commands = ['start'])
async def start(message: Message):
    # Check if the user's ID (message.from_user.id) is not in user_tasks or user_tasks[ our ID ] is not running already
    if message.from_user.id not in user_tasks or not user_tasks[message.from_user.id]:
        # Send a start message and initiate a task for sending updates
        await message.answer("🚀 Bot started! You will from NOW receive Updates with discounts!")
        # Associating a user's ID with an asynchronous task that will start_sending_updates
        user_tasks[message.from_user.id] = asyncio.create_task(start_sending_updates(message.from_user.id))
    else:
        # Send a message indicating that the bot is already running
        await message.answer("✅ Bot is already running. If you want to stop, use /stop")


# Define an asynchronous task for sending updates
async def start_sending_updates(user_id):
    # While we have chat_id (message.from_user.id) in the user_tasks and it's running:
    while user_id in user_tasks and user_tasks[user_id]:
        # Run function send_updates(with out user ID)
        await send_updates(user_id)
        await asyncio.sleep(60) # and sleep for 60 seconds


# Define a message handler for the /stop command
@dp.message_handler(commands = ['stop'])
async def stop(message: Message):
    # if user's ID already in user_tasks and running:
    if message.from_user.id in user_tasks and user_tasks[message.from_user.id]:
        # Cancel the user's task and remove it from the user_tasks dictionary
        user_tasks[message.from_user.id].cancel()
        user_tasks.pop(message.from_user.id)
        await message.answer("🛑 Bot stopped. You will no longer receive updates. Press /start")
    else:
        # Send a message indicating that the bot is not running
        await message.answer("🚫 Bot is not running. Use /start")


# Define an asynchronous function to send updates to a user
async def send_updates(user_id):
    # Define global variables used to know what was the last product we sent to user
    global order_number
    global more_what
    global offset
    # Connect to the database using the engine
    with engine.connect() as conn:
        # Query to retrieve distinct (unique) user inputs for the given user
        query = text('SELECT DISTINCT user_input FROM "asos" WHERE telegram_id = :user_id')
        result = conn.execute(query, {"user_id": str(user_id)})
        user_inputs = [row[0] for row in result] # storing all unique user_input in user_inputs list
        if user_inputs: # Check if user_inputs list exists (there are user inputs):
            for user_input in user_inputs: # for every unique user_input we connect to database and select size_id, so later we could find discounts for this user_input on asos site
                order_number = 0
                with engine.connect() as conn:
                    query = text('SELECT size_id FROM "asos" WHERE telegram_id = :user_id AND user_input = :user_input')
                    size_id = conn.execute(query, {"user_id": str(user_id), "user_input": user_input}).fetchone()[0]
                    query_search = user_input.split(', ', 1)[-1]
                    query_asos = query_search.replace(" ", "+")
                    # Construct the query URL to fetch product data from ASOS


                    query_url = text(f"https://www.asos.com/api/product/search/v2/?offset=0&includeNonPurchasableTypes=restocking&q={query_asos}&store=COM&lang=en-GB&currency=GBP&rowlength=4&channel=desktop-web&country=GB&customerLoyaltyTier=null&keyStoreDataversion=qx71qrg-45&advertisementsPartnerId=100712&advertisementsVisitorId=5ccee116-9a0f-454c-ac68-ab4ce91150f4&advertisementsOptInConsent=true&limit=200&discount_band=1%2C2%2C3%2C4%2C5%2C6&size_eu={size_id}")


                    # query_url = (f"https://www.asos.com/api/product/search/v2/?offset=0&q={query_asos}"
                    #     f"&store=ROE&lang=en-GB&currency=EUR&rowlength=4&channel=desktop-web&country=LV&keyStoreDataversion=h7g0xmn-38&limit=200&discount_band=1%2C2%2C3%2C4%2C5%2C6%2C7"
                    #     f"&size_eu={size_id}")
                    s = requests.Session()
                    response = s.get(url=query_url, headers=headers)
                    # results = all products from asos site for search query
                    results = response.json()
                    item_count = results.get("itemCount")
                    if item_count == 0: # means we can go to next user_input
                        continue # Immediately skips the current iteration of the loop for and continues with the next user_input
                    elif item_count > 200: # Check if there are more than 200 items available
                        await bot.send_message(user_id, "More than 200 items to update. Delete it first:")
                        await bot.send_message(user_id, user_input)
                    elif item_count < 200:  # All results we got for our user_input from asos we take one by one and check if we already have them in our database
                        products = results.get("products")
                        for product in products:
                            # connecting to database to check if we already have this product_id
                            with engine.connect() as conn:
                                product_id = product.get('id')
                                query_db = text('SELECT 1 FROM "asos" WHERE telegram_id = :user_id AND product_id = :product_id')
                                existing_product = conn.execute(query_db, {"user_id": str(user_id), "product_id": str(product_id)}).fetchone()
                                if not existing_product: # If product doesn't exist, insert it into the database
                                    order_number += 1
                                    previous_price = product.get('price').get('previous').get('text')
                                    current_price = product.get('price').get('current').get('text')
                                    link = "https://www.asos.com/" + product.get('url')
                                    await bot.send_message(user_id, f"{order_number} - {product.get('name')}"
                                                         f"\n{link}"
                                                         f"\nPrice: {previous_price} --> {current_price}"
                                                         f"\nQuery: {user_input}")
                                    with engine.connect() as conn:
                                        current_date = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                        query_db = text(
                                            'INSERT INTO "asos" (telegram_id, user_input, product_id, size_id, '
                                            'refresh_date, previous_price, current_price, link) '
                                            'VALUES (:telegram_id, :user_input, :product_id, :size_id, '
                                            ':refresh_date, :previous_price, :current_price, :link) '
                                            'ON CONFLICT (telegram_id, product_id) DO UPDATE SET refresh_date = :refresh_date')
                                        conn.execute(query_db, {
                                            "telegram_id": str(user_id),
                                            "user_input": user_input,
                                            "product_id": str(product_id),
                                            "size_id": str(size_id),
                                            "refresh_date": current_date,
                                            "previous_price": previous_price,
                                            "current_price": current_price,
                                            "link": link
                                        })
                                        conn.commit()
                                    if order_number > 3:
                                        await bot.send_message(user_id, "show /more?")
                                        offset = 4
                                        more_what = user_input
                                        break # exiting loop for product in products (moving to the next product)
                                    else: # If product exists, skip it
                                        pass # we continue with checking results if there is another one new discount for this user_input
        else:
            await bot.send_message(user_id, "No /products to update.")


# Define a message handler for the /products command
@dp.message_handler(commands = ['products'])
async def products(message: Message):
    # Connect to the database and fetch unique user inputs
    with engine.connect() as conn:
        query = text('SELECT DISTINCT user_input FROM "asos" WHERE telegram_id = :telegram_id')
        result = conn.execute(query, {"telegram_id": str(message.from_user.id)})
        user_inputs = [row[0] for row in result] # Extract user_input values into user_inputs list
        if user_inputs:
            # Send a message with length of list
            await message.answer(f"Unique User Inputs {len(user_inputs)}:")
            i = 0
            # in list user_inputs for every item: Send user_input and their last refresh date
            for user_input in user_inputs:
                query = text('SELECT refresh_date FROM "asos" WHERE user_input = :user_input ORDER BY refresh_date DESC')
                last_date = conn.execute(query, {"user_input": user_input}).fetchone()[0].strftime('%d.%m %H:%M')
                i += 1
                await message.answer(f"{i}: {user_input}, last discount was on: {last_date}")
        else:
            # Send a message if no user inputs are found
            await message.answer("No user inputs found. Add it by writing [size], [product name]")


# Define a message handler for the /sizes command
@dp.message_handler(commands = ['sizes'])
async def sizes(message: Message):
    # Send a message with available sizes and example what to type
    await message.answer(f"Search works for these sizes:"
                         f"\n{size_replace('sizes_db')}")


# Define a message handler for the /help command
@dp.message_handler(commands=['help'])
async def help(message: types.Message):
    # Send a help message with explanations of available commands
    help_text = ("👉 <b>/start</b> - Subscribe for updates\n\n"
        "📦 <b>/products</b> - List of your items\n\n"
        "📏 <b>/sizes</b> - Available sizes\n\n"
        "🪒 <b>Gillette</b> - Search discounts for Gillette\n\n"
        "👟 <b>[size], Gillette</b> - Add your query to /products list\n\n"
        "❌ delete 1: 43, Puma suede... - Delete this product from your Search list"
        "\n\n🛑 /stop - Stop receiving updates")
    await message.reply(help_text, parse_mode='HTML')


# Define a message handler for the /more command
@dp.message_handler(commands = ['more'])
async def more(message: Message):
    # Global variables to keep what was the last item sent
    global more_what
    global offset
    global order_number
    # Find the index of the first comma (,) in 'more_what'
    comma_index = more_what.find(",")
    input_size = more_what[:comma_index].strip()
    size_id = size_replace(input_size) # we will add it to query URL later
    # we will send query to asos without size in the beginning, only search query. So splitting 'more_what' by ',', 1 - means splititng 1 time, [-1] - means taking last part after split
    query_search = more_what.split(', ', 1)[-1]
    # Replace spaces in 'query_search' with '+' OR '%20' for the query URL
    query_asos = query_search.replace(" ", "+")
    # Construct the query URL for fetching more results
    
    query_url = text(f"https://www.asos.com/api/product/search/v2/?offset=0&includeNonPurchasableTypes=restocking&q={query_asos}&store=COM&lang=en-GB&currency=GBP&rowlength=4&channel=desktop-web&country=GB&customerLoyaltyTier=null&keyStoreDataversion=qx71qrg-45&advertisementsPartnerId=100712&advertisementsVisitorId=5ccee116-9a0f-454c-ac68-ab4ce91150f4&advertisementsOptInConsent=true&limit=200&discount_band=1%2C2%2C3%2C4%2C5%2C6&size_eu={size_id}")


    # query_url = (f"https://www.asos.com/api/product/search/v2/?offset={offset}&q={query_asos}&store=ROE&lang=en-GB&currency=EUR"
    #     f"&rowlength=4&channel=desktop-web&country=LV&keyStoreDataversion=h7g0xmn-38&limit=200&discount_band=1%2C2%2C3%2C4%2C5%2C6%2C7"
    #     f"&size_eu={size_id}")
    
    # Create an HTTP session and send a GET request
    s = requests.Session()
    # Send a GET request to the 'query' URL with headers 'headers'
    response = s.get(url=query_url, headers=headers)
    results = response.json() # Python dictionary results = parsed JSON from response
    item_count = results.get("itemCount") # from results get 'itemCount', showing how many products with discounts exists on asos site
    if offset == 0:
        # send amount of found items
        await message.answer(f"I found {item_count} discounts for {message.text}")
    else:
        pass
    products = results.get("products") # from dictionary results (our json response) take 'products' and store it in products dictionary
    for product in products:
        order_number += 1
        previous_price = product.get('price').get('previous').get('text')
        current_price = product.get('price').get('current').get('text')
        link = "https://www.asos.com/"+ product.get('url')
        await message.answer(f"{order_number} - {product.get('name')}"
            f"\n{link}"
            f"\nPrice: {previous_price} --> {current_price}"
            f"\nQuery: {message.text}")
        with engine.connect() as conn:
            current_date = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            # insert product into the database (on duplicate) update date
            query_db = text(
                'INSERT INTO "asos" (telegram_id, user_input, product_id, size_id, '
                'refresh_date, previous_price, current_price, link) '
                'VALUES (:telegram_id, :user_input, :product_id, :size_id, '
                ':refresh_date, :previous_price, :current_price, :link) '
                'ON CONFLICT (telegram_id, product_id) DO UPDATE SET refresh_date = :refresh_date')
            conn.execute(query_db, {
                "telegram_id": str(message.from_user.id),
                "user_input": more_what,
                "product_id": str(product.get('id')),
                "size_id": str(size_id),
                "refresh_date": current_date,
                "previous_price": previous_price,
                "current_price": current_price,
                "link": link
            })
            conn.commit()
        # Checking if bot already sent > 3 messages:
        if order_number - offset > 3:
            await message.answer("show /more?")
            offset = offset + 4 # offset now is increased by 4 because we sent 4 products
            break # exiting loop for product in products (moving to the next product)
        else:
            pass



# Define a message handler for handling text messages
@dp.message_handler(content_types=types.ContentType.TEXT)
async def handle_text(message: Message):
    # Check if the message starts with "delete "
    if message.text.lower().startswith("delete "):
        # Find the position of ":" and "last discount was" in the message text
        position_start = message.text.find(":") + 2
        position_end = message.text.find("last discount was") - 2
        # Extract the user product from the message text
        user_input = message.text[position_start:position_end].strip()
        await message.answer(f"{user_input}")
        # Connect to the database and delete all rows for this user_input for this user's ID
        with engine.connect() as conn:
            query = text('DELETE FROM "asos" WHERE telegram_id = :telegram_id AND user_input = :user_input')
            conn.execute(query, {"telegram_id": str(message.from_user.id), "user_input": user_input})
            conn.commit()
        # Send a confirmation message
        await message.answer("Deleted Successfully. Check your /products")
    else:
        # Set global variables for more_what, offset, and order_number
        global more_what
        global offset
        global order_number
        # Set more_what to the message text, and reset offset and order_number
        more_what = message.text
        offset = 0
        order_number = 0
        # Call the 'more' function to handle the user's input
        await more(message)


# Define a function that maps European shoe sizes to their corresponding IDs
def size_replace(size):
    # Define a dictionary that maps sizes to IDs
    sizes_db = {
        "35.5": 6382,
        "36": 23,
        "36.7": 13193,
        "36.5": 6393,
        "37": 3219,
        "37.3": 13203,
        "37.5": 5942,
        "38": 35,
        "38.5": 5953,
        "38.7": 13213,
        "39": 3233,
        "39.3": 13223,
        "40": 47,
        "40.5": 5309,
        "40.7": 13233,
        "41": 5321,
        "41.3": 13243,
        "42": 59,
        "42.5": 5333,
        "42.7": 14100,
        "43": 3251,
        "43.3": 13263,
        "44": 71,
        "44.7": 13080,
        "45.3": 13090,
        "44.5": 5282,
        "45": 3195,
        "45.5": 7518,
        "46": 141,
        "46.7": 13100,
        "47": 5296,
        "47.3": 13110,
        "47.5": 7528,
        "48": 153,
        "48.5": 11921,
        "48.7": 13120,
        "49.3": 13130,
        "50": 183,
        "XS": 5188,
        "S": 4430,
        "M": 4418,
        "L": 5164,
        "XL": 5176,
        "2XL": 5128,
    }
    # Check if the input size is "sizes_db" and return a comma-separated list of available sizes
    if size == "sizes_db":
        sizes_text = ', '.join(map(str, sizes_db.keys()))
        return sizes_text # after function reaches 'return' - all other code is ignored
    # Check if the input size exists in the dictionary and return its corresponding ID
    if size in sizes_db:
        final_id = sizes_db[size]
        return final_id
    else:
        return ""


# Check if the script is being run directly and start the polling executor (to continuously check for new messages from Telegram servers)
if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)