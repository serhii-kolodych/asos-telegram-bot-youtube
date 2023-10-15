# 📺 watch Python Tutorial for this code on YouTube: https://www.youtube.com/@serhiikolodych

# ✅ 1. Insert your TOKENs in config.py file

# ✅ 2. Don't forget to install libraries, by typing in your terminal:
# pip install datetime==4.4 requests==2.26.0 SQLAlchemy==1.4.23 aiogram==2.9 asyncio==3.4.3

# ✅ 3. You can run the script now! 🚀

import config # our config.py file with TOKENs for our bot and database
import datetime # so we can write time and date of when we inserted product in database
import requests # to receive json from website
from sqlalchemy import create_engine, text # engine to work with database
from aiogram import Bot, Dispatcher, executor, types # for telegram bot
from aiogram.types import Message # to read and write messages in telegram bot
import asyncio # to send updates every ? seconds


# Import your bot's TOKEN and engine_token from a configuration file (config.py)
TOKEN = config.TOKEN
engine_token = config.engine_token

# Initialize the Telegram bot using the provided TOKEN
bot = Bot(token=TOKEN)

# Create a Dispatcher for handling incoming messages and commands
dp = Dispatcher(bot)

# Create a database engine using SQLAlchemy, with SSL settings
engine = create_engine(
    engine_token,
    connect_args={
        "ssl": {
            "ca": "/etc/ssl/cert.pem"
        }
    })

# Define global variables more_what, offset, and order_number (for /more function)
global more_what
global offset
global order_number

# Define headers for HTTP requests
headers = {
    "accept": "*/*",
    "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36 OPR/102.0.0.0"
}

# Create an empty dictionary to store user tasks (sending updates to those who /start the bot)
user_tasks = {}

# Define a message handler for the /start command
@dp.message_handler(commands=['start'])
async def start(message: Message):
    # Check if the user's ID (message.from_user.id) is not in user_tasks or user_tasks[ our ID ] is not running already
    if message.from_user.id not in user_tasks or not user_tasks[message.from_user.id]:
        # Send a start message and initiate a task for sending updates
        await message.answer("🚀 Bot started! You will from NOW receive Updates with discounts.")
        await message.answer("I will send you discounts ASAP! Check your /products 📦")
        # Associating a user's ID with an asynchronous task that will start_sending_updates
        user_tasks[message.from_user.id] = asyncio.create_task(start_sending_updates(message.from_user.id))
    else:
        # Send a message indicating that the bot is already running
        await message.answer("✅ Bot is already running. If you want to stop, use /stop 🛑")

# Define a message handler for the /stop command
@dp.message_handler(commands=['stop'])
async def stop_command(message: types.Message):
    # if user's ID already in user_tasks and running:
    if message.from_user.id in user_tasks and user_tasks[message.from_user.id]:
        # Cancel the user's task and remove it from the user_tasks dictionary
        user_tasks[message.from_user.id].cancel()
        user_tasks.pop(message.from_user.id)
        await message.answer("🛑 Bot stopped. You will no longer receive updates. Press /start")
    else:
        # Send a message indicating that the bot is not running
        await message.answer("🚫 Bot is not running. Use /start to start it.")

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

# Define a message handler for the /products command
@dp.message_handler(commands='products')
async def products(message: types.Message):
    # Connect to the database and fetch unique user inputs
    with engine.connect() as conn:
        query = text(f"SELECT DISTINCT user_input FROM `asos` WHERE telegram_id = '{message.from_user.id}'")
        result = conn.execute(query)
        user_inputs = [row[0] for row in result]  # Extract user_input values into user_inputs list
        if user_inputs: # if list exists:
            # Send a message with length of list
            await message.answer(f"📦 Unique User Inputs ({len(user_inputs)}):")
            i = 0
            # in list user_inputs for every item: Send user_input and their last refresh date
            for user_input in user_inputs:
                query = text(
                    f"SELECT refresh_date FROM `asos` WHERE user_input = '{user_input}' AND telegram_id = '{message.from_user.id}' ORDER BY refresh_date DESC")
                formatted_date = conn.execute(query).fetchone()[0].strftime('%d.%m %H:%M')  # Fetch the first column (refresh_date)
                i += 1
                await message.answer(f"{i}: {user_input}, last discount was: {formatted_date}")
        else:
            # Send a message if no user inputs are found
            await message.answer("No user inputs found. Add it by writing: [your product size], [your query]")

# Define a message handler for the /sizes command
@dp.message_handler(commands=['sizes'])
async def sizes(message: types.Message):
    # Send a message with available sizes and example what to type
    await message.answer(f"Search works for these sizes: "
        f"\n{size_replace('sizes_db')}"
        "\n\nFor example, type: 42.7, Puma Suede")



# Define a message handler for the /more command
@dp.message_handler(commands=['more'])
async def more(message: Message):
    # Global variables to keep what was the last item sent
    global more_what
    global offset
    global order_number

    # Check if the required global variables exist
    if "more_what" not in globals() or "offset" not in globals() or "order_number" not in globals():
        await message.answer("Please write what you're looking for.")
    else:
        # Find the index of the first comma (,) in 'more_what'
        comma_index = more_what.find(",")

        # if there is comma (,) // if comma_index not equal to -1:
        if comma_index != -1:
            # input_size = take from 'more_what' symbols from 0 till comma_index symbol + strip (remove leading/trailing spaces)
            input_size = more_what[:comma_index].strip()
            # size id = using function size_replace to return us size_id for our asos site
            size_id = size_replace(input_size)
        else: # if there is no comma in user input --> size_id = ''
            size_id = ""
        size_search = "&size_eu=" + str(size_id) # we will add it to query URL later

        # we will send query to asos without size in the beginning, only search query. So splitting 'more_what' by ',', 1 - means splititng 1 time, [-1] - means taking last part after split
        query_search = more_what.split(', ', 1)[-1]
        # Replace spaces in 'query_search' with '%20' for the query URL
        query_asos = query_search.replace(" ", "%20")

        # Construct the query URL for fetching more results
        query = f"https://www.asos.com/api/product/search/v2/?offset={offset}&q={query_asos}&store=ROE&lang=en-GB&currency=EUR&rowlength=2&channel=mobile-web&country=LV&keyStoreDataversion=h7g0xmn-38&limit=200&discount_band=1%2C2%2C3%2C4%2C5%2C6" + size_search

        # Create an HTTP session and send a GET request
        s = requests.Session()
        # Send a GET request to the 'query' URL with headers 'headers'
        response = s.get(url=query, headers=headers)
        results = response.json() # Python dictionary results = parsed JSON from response
        sent = 0 # amount of products we already sent to user
        skipped = 0 # amount of products we ignored from asos because they didn't have discount
        products = results.get("products") # from dictionary results (our json response) take 'products' and store it in products dictionary
        item_count = results.get("itemCount") # from results get 'itemCount', showing how many products with discounts exists on asos site

        # send amount of found items - (minus) already shown
        await message.answer(f"I found {item_count - offset} discounts more for {more_what}")

        # if item_count more than 200 we delete this search entry and ask user to be more specific
        if item_count > 200:
            await bot.send_message(message.from_user.id, "Sorry, more than 200 items available. So I Deleted one of your /products: 📦")
            await bot.send_message(message.from_user.id, "Write something more specific, than:")
            await bot.send_message(message.from_user.id, more_what)
            with engine.connect() as conn:
                query = text(f"DELETE FROM `asos` WHERE telegram_id = '{message.from_user.id}' AND user_input = '{more_what}'")
                conn.execute(query)
        else: # if less than 200 products --> for every product in products
            for product in products:
                # compare if previous_price = '' - then we skip this product, and count it +1
                if product.get("price").get("previous").get("text") == "":
                    skipped += 1
                    pass
                else: # means there is previous_price, so we need to take current_price and link and send this data to user
                    sent += 1
                    previous_price = product.get("price").get("previous").get("text")
                    current_price = product.get("price").get("current").get("text")
                    link = "https://www.asos.com/" + product.get("url")

                    # Send a message with product details and discount
                    await message.answer(str(order_number + sent) + ". " + product.get("name") +
                        "\n" + link + "\nPrice: " + previous_price + " ---> " +
                        current_price + "\nQuery: " + more_what)

                    product_id = product.get("id")
                    current_date = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                    # Check if the product already exists in the database
                    with engine.connect() as conn:
                        query = text(f"SELECT 1 FROM `asos` WHERE telegram_id = '{message.from_user.id}' AND product_id = '{product_id}'")
                        existing_product = conn.execute(query).fetchone()

                        if not existing_product: # Product doesn't exist, insert it into the database
                            query_db = text(f"INSERT INTO `asos` (telegram_id, user_input, product_id, size_id, refresh_date, previous_price, current_price, link) "
                                f"VALUES ('{message.from_user.id}', '{more_what}', '{product_id}', '{size_id}', '{current_date}', '{previous_price}', '{current_price}', '{link}')")
                            conn.execute(query_db)
                        else: # Product exists, update it in the database, since we previously sent it to user in message
                            query_db_update = text(f"UPDATE `asos` "
                                f"SET user_input = '{more_what}', "
                                f"size_id = '{size_id}', "
                                f"refresh_date = '{current_date}', "
                                f"previous_price = '{previous_price}', "
                                f"current_price = '{current_price}', "
                                f"link = '{link}' "
                                f"WHERE telegram_id = '{message.from_user.id}' AND product_id = '{product_id}'")
                            conn.execute(query_db_update)
                    # Checking if bot already sent > 3 messages:
                    if sent > 3:
                        await message.answer(f"show /more") #sending /more message
                        order_number = order_number + 4 # order_number is now +4 since there were 4 messages sent, so next time you should start with +4
                        break # exiting loop for product in products (moving to the next product)
                    else: # means were sent less than 4 messages / products
                        pass # pass means go to next line
            # Updating global offset to fetch the next set of results (global more_what stays the same, global order_number was updated before break)
            offset = offset + sent + skipped
            await message.answer(f"Analyzed prices for {skipped + sent} items from Asos")

# Define an asynchronous task for sending updates
async def start_sending_updates(chat_id):
    # While we have chat_id (message.from_user.id) in the user_tasks and it's running:
    while chat_id in user_tasks and user_tasks[chat_id]:
        # Run function send_updates(with out user ID) and sleep for 60 seconds
        await send_updates(chat_id)
        await asyncio.sleep(10)  # Wait for 60 seconds


# Define an asynchronous function to send updates to a user
async def send_updates(user_id):
    # Define global variables used to know what was the last product we sent to user
    global more_what
    global offset
    global order_number

    # Connect to the database using the engine
    with engine.connect() as conn:
        # Query to retrieve distinct (unique) user inputs for the given user
        query = text(f"SELECT DISTINCT user_input FROM `asos` WHERE telegram_id = '{user_id}'")
        result = conn.execute(query)
        user_inputs = [row[0] for row in result] # storing all unique user_input in user_inputs list
        if user_inputs: # Check if user_inputs list exists (there are user inputs):
            for user_input in user_inputs: # for every unique user_input we connect to database and select size_id, so later we could find discounts for this user_input on asos site
                with engine.connect() as conn:
                    query = text(f"SELECT size_id FROM `asos` WHERE telegram_id = '{user_id}' AND user_input = '{user_input}'")
                    result = conn.execute(query).fetchone()
                    size_id = result[0]
                    size_search = "&size_eu=" + str(size_id)
                    query_search = user_input.split(', ', 1)[-1]
                    query_asos = query_search.replace(" ", "%20")

                    # Construct the query URL to fetch product data from ASOS
                    query_url = "https://www.asos.com/api/product/search/v2/?offset=0&q=" + query_asos + "&store=ROE&lang=en-GB&currency=EUR&rowlength=2&channel=mobile-web&country=LV&keyStoreDataversion=h7g0xmn-38&limit=200" + size_search + "&discount_band=1%2C2%2C3%2C4%2C5%2C6"

                    s = requests.Session()
                    response = s.get(url=query_url, headers=headers)
                    data = response.json()
                    item_count = data.get("itemCount")
                    # results = all products from asos site for search query
                    results = data.get("products")
                    skipped = 0
                    order_number = 0

                    # Check if there are more than 200 items available
                    if item_count > 200:
                        await bot.send_message(user_id, "Sorry, more than 200 items available. So I Deleted one of your /products: 📦")
                        await bot.send_message(user_id, user_input)
                        with engine.connect() as conn:
                            query = text(f"DELETE FROM `asos` WHERE telegram_id = '{user_id}' AND user_input = '{user_input}'")
                            conn.execute(query)
                    elif item_count == 0: # means we can go to next user_input
                        continue # Immediately skips the current iteration of the loop for and continues with the next user_input
                    elif item_count < 200:
                        # All results we got for our user_input from asos we take one by one and check if we already have them in our database
                        for product in results:
                            more_what = user_input
                            offset = 0

                            # Check if there is no discount for the product
                            if product.get("price").get("previous").get("text") == "":
                                skipped += 1
                            else: # if there is discount (previous_price is not ''):
                                with engine.connect() as conn: # connecting to database to check if we already have this product_id
                                    product_id = product.get("id")
                                    query = text(f"SELECT 1 FROM `asos` WHERE telegram_id = '{user_id}' AND product_id = '{product_id}'")
                                    existing_product = conn.execute(query).fetchone()
                                    if not existing_product: # If product doesn't exist, insert it into the database
                                        order_number += 1
                                        current_date = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                        previous_price = product.get("price").get("previous").get("text")
                                        current_price = product.get("price").get("current").get("text")
                                        link = "https://www.asos.com/" + product.get("url")
                                        query_db = text(f"INSERT INTO `asos` (telegram_id, user_input, product_id, size_id, refresh_date, previous_price, current_price, link) "
                                            f"VALUES ('{user_id}', '{user_input}', '{product_id}', '{size_id}', '{current_date}', '{previous_price}', '{current_price}', '{link}')")
                                        conn.execute(query_db)
                                        await bot.send_message(user_id, f"{product.get('name')} \n{link} \nPrice: {previous_price} ---> {current_price}\nQuery: {user_input}")
                                    else: # If product exists, skip it
                                        skipped += 1
                                if order_number > 3: # let's count all messages we sent about 1 unique user input and if oder_number > 3:
                                    await bot.send_message(user_id, f"show /more")
                                    offset = order_number
                                    break # we exit loop for this product and move to next in our results list
                                else:
                                    pass # we continue with checking results if there is another one new discount for this user_input
                # await bot.send_message(user_id, f"skipped: {skipped}, order_number: {order_number}")


# Define a message handler for handling text messages
@dp.message_handler(content_types=types.ContentType.TEXT)
async def handle_text_message(message: types.Message):
    # Check if the message starts with "delete "
    if message.text.lower().startswith("delete "):
        # Find the position of ":" and "last discount was" in the message text
        position_start = message.text.find(":") + 2
        position_end = message.text.find("last discount was") - 2

        # Extract the user product from the message text
        user_product = message.text[position_start:position_end].strip()
        await message.answer(f"{user_product}")

        # Connect to the database and delete all rows for this user_input for this user's ID
        with engine.connect() as conn:
            query = text(f"DELETE FROM `asos` WHERE telegram_id = '{message.from_user.id}' "
                f"AND user_input = '{user_product}' ")
            conn.execute(query)
        # Send a confirmation message
        await message.answer(f"Deleted successfully! Check other /products? 📦")
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


