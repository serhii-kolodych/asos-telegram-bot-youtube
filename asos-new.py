# pip install aiogram asyncio requests sqlalchemy
import config_a
from datetime import datetime
import requests
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message
import asyncio
import random # for anyway - to generate product_id
from aiogram.filters import Command # you can import only one of them (if needed)
import psycopg2
import sqlalchemy
from sqlalchemy import create_engine, text
import signal
import sys
import aiohttp

TOKEN = config_a.TOKEN
connection_string = config_a.engine_token

# Initialize SQLAlchemy engine
engine = create_engine(connection_string)

def get_formatted_time():
    return datetime.now().strftime('%H:%M %B %d')

current_time = datetime.now()
formatted_time = get_formatted_time()
print(f"-->cv-online.py Started on {formatted_time}")

bot = Bot(TOKEN)
dp = Dispatcher()

global more_what
global offset
global user_id
global user_tasks

headers = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "accept-encoding": "gzip, deflate, br, zstd",
    "accept-language": "en-GB,en;q=0.9,ru-RU;q=0.8,ru;q=0.7,en-US;q=0.6,bg;q=0.5,lv;q=0.4",
    "cache-control": "max-age=0",
    "cookie": "_abck=E25695CA8159E3DC35E8679F9E6151EA~-1~YAAQjYnvUL5OIAyXAQAA0iHxJw3vrdZg2rLp0DsZhEt1cby/aZz3oNbUQghjDO3zF4uGmdvLV//C8kBO2lO3aEEMDcYARWibFpGLapF94sy7rMCpwXJrAWvztej95A33lDgM3mTkz42H8zFnBn51bt/WnRq9iJnglFb4f1+vyYwEh6jEeOw2+54IrZA7h6geWzpM9ARsMd7OOibv75115C8wZJI+qT2BZ3fxYHgP76BI0Hdiofb1HgDZkuAXHza+EiEDlRTXya1MQ8yDCoRzixmUoA/I3j7FxDJCrMvOMReg2dcjmIbFORE6KFHEbILPbAxp7c921L84r7gJSjFzEokkJ88/M3NcefdqnB14S3m4VKfyLUNcrknzUZtoLoVIUFUiUpUNiAsxehi5iePIZpfdbO+x7CxwhzaAwjc0Y+YBne1R5ExdsTsm4MtD1H0eYjs=~-1~-1~-1; ak_bmsc=D24A18338E392B421259E7610C42C612~000000000000000000000000000000~YAAQjYnvUL9OIAyXAQAA0iHxJxvkyr0xvGsM/0KHRbB1KvxwfIOeMdPBYIZHY3IiLe/fPRgTgYnnO+m9si+3A0+kWvHgzJhh/y7WqOZyveAGKr0mm6CvdnT38fSbpHxPg1sQL2ez0QqIJWeQrzDqUq6+Zp6pi9jFLj+2GoBGoRPLt+UAWnaFWejC7SfLb3stZz6XXcWbmD49Zujb07T3l92tLSH4Fo6ms/Ay1z233WmqhiOh6ff853/BzdKQthmF71s9lhWd8uiU1RY6+z1p3le0tthYkBC55m+s1e7ZGwrrF6gkIeMqGChfeQ3MNjsf/byz4zG0GQXCOSxkG9GKjolBNZZJTCVFKN3nAGlJHJGFiipDgHtiAB9gbqycPu8lPLO24+I=; bm_sz=B934F188B2649327563782AC502297AF~YAAQjYnvUMBOIAyXAQAA0iHxJxvA7UVTu1zSimHP5riOHW0uFIXa1y+mw27NIcJNCuJ3vwNyjOBDxeUxjMhiZaV7g3hb6+KciKK+sa4kI24vXp0yzKisxt3tXAVKdcaeWvdMihwY5PA5yrPLONpe/ecd4H3VRqHpr5dGZtqzV5A2rjhFBJdwC1QjMSdidjONDqzkaqEAsu5q9DOHdkb3hSv2G7TWZ7VbbbEbAWGA19b2GyQrqkk1f8Rmiuecuxb6hfae10c2pLXjki16HrBx19FPm7bGuuEb9ev4SOxBPpvd4+71R13JswzNkd+/fPGiSPShVPo6PGzxHFQ3ds+ae31EXw2TeqVUEspjGB1T5IjLFcULA7wAy2s2Tj9EkazgKnBmFpqH3UVy~4403781~4600376; geocountry=LV; asos_drmlp=ff00fd5a1a9ede5c5d04ff92f8cab8cc",
    "priority": "u=0, i",
    "sec-ch-ua": "\"Chromium\";v=\"136\", \"Google Chrome\";v=\"136\", \"Not.A/Brand\";v=\"99\"",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "\"macOS\"",
    "sec-fetch-dest": "document",
    "sec-fetch-mode": "navigate",
    "sec-fetch-site": "none",
    "sec-fetch-user": "?1",
    "upgrade-insecure-requests": "1",
    "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36"
}

user_tasks = {}

async def cleanup():
    print(f"[{get_formatted_time()}] Cleaning up resources...")
    # Cancel all running tasks
    for task in user_tasks.values():
        if task and not task.done():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
    user_tasks.clear()
    
    # Close database connections
    if engine:
        await engine.dispose()
    
    print(f"[{get_formatted_time()}] Cleanup completed")

@dp.message(Command("start"))
async def handle_start(message: types.Message):
    """
    Handle the /start command to initialize the bot for a user.
    Creates a new task for sending updates if one doesn't exist.
    """
    print(f"[{get_formatted_time()}] ⬇️ ⬇️ ⬇️ Start command initiated ⬇️ ⬇️ ⬇️")
    print(f"[{get_formatted_time()}] Starting bot initialization for user {message.from_user.id}")
    
    try:
        # Notify admin about new user
        try:
            await bot.send_message(266585723, f"new-user: {message.from_user.full_name}\nID: {message.from_user.id}\n@{message.from_user.username}")
            print(f"[{get_formatted_time()}] Admin notification sent successfully")
        except Exception as e:
            print(f"[{get_formatted_time()}] Error sending admin notification: {str(e)}")

        # Check if user already has a running task
        if message.from_user.id not in user_tasks or not user_tasks[message.from_user.id]:
            print(f"[{get_formatted_time()}] Creating new update task for user {message.from_user.id}")
            await message.answer("Bot started! You will from NOW receive Updates with discounts.")
            await message.answer("I will send you discounts ASAP! Check your /products")
            
            try:
                user_tasks[message.from_user.id] = asyncio.create_task(start_sending_updates(message.from_user.id))
                print(f"[{get_formatted_time()}] Update task created successfully")
            except Exception as e:
                print(f"[{get_formatted_time()}] Error creating update task: {str(e)}")
                await message.answer("Error starting updates. Please try /stop and then /start again.")
        else:
            print(f"[{get_formatted_time()}] User {message.from_user.id} already has a running task")
            await message.answer("Bot is already running. If you want to stop, use /stop")
        
        print(f"[{get_formatted_time()}] ⬆️ ⬆️ ⬆️ Start command completed successfully ⬆️ ⬆️ ⬆️")
    except Exception as e:
        print(f"[{get_formatted_time()}] Unexpected error in start command: {str(e)}")
        await message.answer("An unexpected error occurred. Please try again.")


@dp.message(Command("stop"))
async def stop_command(message: types.Message):
    """
    Handle the /stop command to stop sending updates to a user.
    Cancels the user's update task and removes it from the tasks dictionary.
    """
    print(f"[{get_formatted_time()}] ⬇️ ⬇️ ⬇️ Stop command initiated ⬇️ ⬇️ ⬇️")
    print(f"[{get_formatted_time()}] Attempting to stop updates for user {message.from_user.id}")
    
    try:
        if message.from_user.id in user_tasks and user_tasks[message.from_user.id]:
            print(f"[{get_formatted_time()}] Found running task for user {message.from_user.id}")
            try:
                user_tasks[message.from_user.id].cancel()
                try:
                    await user_tasks[message.from_user.id]
                except asyncio.CancelledError:
                    pass
                user_tasks.pop(message.from_user.id)
                print(f"[{get_formatted_time()}] Task cancelled and removed successfully")
                await message.answer("Bot stopped. You will no longer receive updates. Press /start")
            except Exception as e:
                print(f"[{get_formatted_time()}] Error cancelling task: {str(e)}")
                await message.answer("Error stopping updates. Please try again.")
        else:
            print(f"[{get_formatted_time()}] No running task found for user {message.from_user.id}")
            await message.answer("Bot is not running. Use /start to start it.")
        
        print(f"[{get_formatted_time()}] ⬆️ ⬆️ ⬆️ Stop command completed successfully ⬆️ ⬆️ ⬆️")
    except Exception as e:
        print(f"[{get_formatted_time()}] Unexpected error in stop command: {str(e)}")
        await message.answer("An unexpected error occurred. Please try again.")


@dp.message(Command("help"))
async def help(message: types.Message):
    """
    Handle the /help command to display available commands and their usage.
    """
    print(f"[{get_formatted_time()}] ⬇️ ⬇️ ⬇️ Help command initiated ⬇️ ⬇️ ⬇️")
    print(f"[{get_formatted_time()}] Sending help message to user {message.from_user.id}")
    
    try:
        help_text = (
            "👉 <b>/start</b> - Subscribe for updates\n\n"
            "📦 <b>/products</b> - List of your items\n\n"
            "📏 <b>/sizes</b> - Available sizes\n\n"
            "🪒 <b>Gillette</b> - Search discounts for Gillette\n\n"
            "👟 <b>[size], Gillette</b> - Add your query to /products list\n\n"
            "❌ delete 1: 43, Puma suede... - Delete this product from your Search list"
            "\n\n🛑 /stop - Stop receiving updates"
        )
        await message.reply(help_text, parse_mode='HTML')
        print(f"[{get_formatted_time()}] ⬆️ ⬆️ ⬆️ Help command completed successfully ⬆️ ⬆️ ⬆️")
    except Exception as e:
        print(f"[{get_formatted_time()}] Error sending help message: {str(e)}")
        await message.answer("❌ Error sending help message. Please try again.")


@dp.message(Command("products"))
async def products(message: types.Message):
    """
    Handle the /products command to show user's saved products and their last update times.
    """
    print(f"[{get_formatted_time()}] ⬇️ ⬇️ ⬇️ Products command initiated ⬇️ ⬇️ ⬇️")
    print(f"[{get_formatted_time()}] Fetching products for user {message.from_user.id}")
    
    connection = None
    cursor = None
    try:
        # Connect to database
        print(f"[{get_formatted_time()}] Connecting to database...")
        connection = psycopg2.connect(connection_string)
        cursor = connection.cursor()

        # Get user's products
        print(f"[{get_formatted_time()}] Querying user's products...")
        telegram_id = message.from_user.id
        query = f"SELECT DISTINCT user_input FROM asos WHERE telegram_id = {message.from_user.id}"
        cursor.execute(query)
        user_inputs = [row[0] for row in cursor.fetchall()]

        if user_inputs:
            print(f"[{get_formatted_time()}] Found {len(user_inputs)} products")
            await message.answer(f"📦 Unique User Inputs ({len(user_inputs)}):")
            
            # Get last update time for each product
            query = """
                SELECT refresh_date FROM asos
                WHERE user_input = %s AND telegram_id = %s
                ORDER BY refresh_date DESC LIMIT 1
            """
            for i, user_input in enumerate(user_inputs, 1):
                try:
                    cursor.execute(query, (user_input, message.from_user.id))
                    result = cursor.fetchone()
                    text = (f"{i}: {user_input}, last discount was: {result[0].strftime('%d.%m %H:%M')}"
                            if result else f"{i}: {user_input}, no discounts found.")
                    await message.answer(text)
                except Exception as e:
                    print(f"[{get_formatted_time()}] Error processing product {i}: {str(e)}")
                    await message.answer(f"❌ Error showing product {i}. Skipping...")
        else:
            print(f"[{get_formatted_time()}] No products found for user")
            await message.answer("No user inputs found.")
            await help(message)
            
        print(f"[{get_formatted_time()}] ⬆️ ⬆️ ⬆️ Products command completed successfully ⬆️ ⬆️ ⬆️")
        
    except (Exception, psycopg2.Error) as error:
        print(f"[{get_formatted_time()}] Error while interacting with PostgreSQL: {str(error)}")
        await message.answer("❌ An error occurred while fetching data. Please try again.")
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()
        print(f"[{get_formatted_time()}] Database connection closed")


@dp.message(Command("db"))
async def db(message: types.Message):
    await message.answer("`asos`")

@dp.message(Command("anyway"))
async def anyway(message: types.Message):
    global more_what
    current_date = datetime(1111, 11, 11, 11, 11, 11)
    product_id = random.randint(0, 9999) #creating product_id, because we should have it for our database
    input_size = more_what.split(', ', 1)[0] # split string by ',' (comma symbol), taking [0] first element of splitted string
    size_id = size_replace(input_size)
    try:
        connection = psycopg2.connect(connection_string)
        cursor = connection.cursor()

        query_db = str(f"INSERT INTO asos (telegram_id, user_input, product_id, size_id, refresh_date, previous_price, current_price, link)"
            f"VALUES ('{message.from_user.id}', '{more_what}', '{product_id}', '{size_id}',"
            f"'{current_date}', '', '', '')"
            f"ON CONFLICT (telegram_id, user_input) DO UPDATE SET refresh_date = '{current_date}'")
        cursor.execute(query_db)
        await message.answer(f"{more_what} - Aded to /products 🙌")
        
        cursor.close()
        
    except psycopg2.Error as e:
        await message.answer(f"An error occurred: {e}")
    finally:
        connection.close()



@dp.message(Command("sizes"))
async def sizes(message: types.Message):
    """
    Handle the /sizes command to display available shoe sizes.
    """
    print(f"[{get_formatted_time()}] ⬇️ ⬇️ ⬇️ Sizes command initiated ⬇️ ⬇️ ⬇️")
    print(f"[{get_formatted_time()}] Fetching available sizes for user {message.from_user.id}")
    
    try:
        a = "sizes_db"
        sizes_text = size_replace(a)
        if not sizes_text:
            print(f"[{get_formatted_time()}] Error: No sizes found in database")
            await message.answer("❌ Error fetching sizes. Please try again.")
            return
            
        print(f"[{get_formatted_time()}] Successfully retrieved sizes")
        await message.answer(
            f"Search works for this sizes: "
            f"\n{sizes_text}"
            "\n\nFor example, type: 42.7, Puma Suede")
        print(f"[{get_formatted_time()}] ⬆️ ⬆️ ⬆️ Sizes command completed successfully ⬆️ ⬆️ ⬆️")
    except Exception as e:
        print(f"[{get_formatted_time()}] Error in sizes command: {str(e)}")
        await message.answer("❌ Error fetching sizes. Please try again.")




@dp.message(Command("more"))
async def more(message: Message):
    """
    Handle the /more command to show additional products from ASOS search results.
    This command is used to paginate through search results when there are more than 3 items.
    """
    print(f"[{get_formatted_time()}] ⬇️ ⬇️ ⬇️ More command initiated ⬇️ ⬇️ ⬇️")
    try:
        global more_what
        global offset
        global order_number

        # Check if required global variables are initialized
        if "more_what" not in globals() or "offset" not in globals() or "order_number" not in globals():
            print(f"[{get_formatted_time()}] Error: Missing global variables")
            await message.answer("Please write what you're looking for.")
            return

        # Parse size and search query from the input
        try:
            comma_index = more_what.find(",")
            input_size = more_what[:comma_index].strip()
            size_id = size_replace(input_size)
            if not size_id:
                print(f"[{get_formatted_time()}] Error: Invalid size {input_size}")
                await message.answer(f"❌ Invalid size: {input_size}. Check /sizes for available sizes.")
                return

            query_search = more_what.split(', ', 1)[-1]
            query_asos = query_search.replace(" ", "+")
        except Exception as e:
            print(f"[{get_formatted_time()}] Error parsing input: {str(e)}")
            await message.answer("❌ Error parsing your input. Please use format: size, product_name")
            return

        # Construct and make ASOS API request
        try:
            query = text(f"https://www.asos.com/api/product/search/v2/?offset=0&q={query_asos}&store=ROE&lang=en-GB&currency=EUR&rowlength=4&channel=desktop-web&country=LV&keyStoreDataversion=h7g0xmn-38&limit=200&discount_band=1%2C2%2C3%2C4%2C5%2C6%2C7&size_eu={size_id}")
            s = requests.Session()
            response = s.get(url=query, headers=headers)
            response.raise_for_status()  # Raise exception for bad status codes
            results = response.json()
        except requests.RequestException as e:
            print(f"[{get_formatted_time()}] Error making ASOS API request: {str(e)}")
            await message.answer("❌ Error connecting to ASOS. Please try again later.")
            return
        except ValueError as e:
            print(f"[{get_formatted_time()}] Error parsing ASOS response: {str(e)}")
            await message.answer("❌ Error processing ASOS response. Please try again.")
            return

        # Process search results
        item_count = results.get("itemCount", 0)
        if offset == 0 and item_count > 0:
            await message.answer(f"I found {item_count} discounts for {message.text}")

        # Handle different result scenarios
        if item_count > 200:
            print(f"[{get_formatted_time()}] Too many results ({item_count}) for query: {more_what}")
            await message.answer("You have to be more specific 😝 More than 200 found for:")
            await message.answer(more_what)
            try:
                with engine.connect() as conn:
                    query = text(f"DELETE FROM asos WHERE telegram_id = '{message.from_user.id}' AND user_input = '{more_what}'")
                    conn.execute(query)
                    conn.commit()
            except Exception as e:
                print(f"[{get_formatted_time()}] Error deleting from database: {str(e)}")
                await message.answer("❌ Error updating your search list. Please try again.")
            return

        elif item_count == 0:
            print(f"[{get_formatted_time()}] No results found for query: {query_search}")
            await message.answer(f"🙁 Nothing found for:")
            await message.answer(query_search)
            await message.answer("Do you want to add it /anyway?")
            return

        # Process products when count is within limits
        try:
            output = results.get("products", [])
            order_number = 0
            product_counter = 0

            for product in output:
                product_counter += 1
                try:
                    with engine.connect() as conn:
                        product_id = product.get('id')
                        query_db = text(
                            f"SELECT 1 FROM asos WHERE telegram_id = '{message.from_user.id}' AND product_id = '{product_id}'")
                        existing_product = conn.execute(query_db).fetchone()

                        if not existing_product:
                            order_number += 1
                            previous_price = product.get('price', {}).get('previous', {}).get('text', 'N/A')
                            current_price = product.get('price', {}).get('current', {}).get('text', 'N/A')
                            link = "https://www.asos.com/" + product.get('url', '')

                            # Send product information to user
                            await message.answer(
                                f"{product_counter} - {product.get('name', 'Unknown Product')}\n"
                                f"{link}\n"
                                f"Price: {previous_price} --> {current_price}\n"
                                f"Query: {more_what}"
                            )

                            # Save product to database
                            current_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            query_db = text(
                                f"INSERT INTO asos (telegram_id, user_input, product_id, size_id, "
                                f"refresh_date, previous_price, current_price, link)"
                                f"VALUES ('{message.from_user.id}', '{more_what}', '{product_id}', '{size_id}',"
                                f"'{current_date}', '{previous_price}', '{current_price}', '{link}')"
                                f"ON CONFLICT (telegram_id, user_input) DO UPDATE SET refresh_date = '{current_date}'")
                            conn.execute(query_db)
                            conn.commit()

                            # Check if we've shown enough products
                            if order_number > 3:
                                await message.answer(
                                    f"I analyzed {product_counter} products out of {item_count} for {more_what}\n"
                                    "show /more?"
                                )
                                offset = 4
                                order_number = product_counter
                                break

                except Exception as e:
                    print(f"[{get_formatted_time()}] Error processing product {product_counter}: {str(e)}")
                    continue

        except Exception as e:
            print(f"[{get_formatted_time()}] Error processing products: {str(e)}")
            await message.answer("❌ Error processing products. Please try again.")

        print(f"[{get_formatted_time()}] ⬆️ ⬆️ ⬆️ More command completed successfully ⬆️ ⬆️ ⬆️")

    except Exception as e:
        print(f"[{get_formatted_time()}] Unexpected error in more command: {str(e)}")
        await message.answer("❌ An unexpected error occurred. Please try again.")


async def start_sending_updates(chat_id):
    while chat_id in user_tasks and user_tasks[chat_id]:
        await send_updates(chat_id, 'no')
        await asyncio.sleep(60)  # Wait for 60 seconds



@dp.message(Command("refresh"))
async def refresh(message: Message):
    """
    Handle the /refresh command to manually trigger an update check for all products.
    """
    print(f"[{get_formatted_time()}] ⬇️ ⬇️ ⬇️ refresh pressed ⬇️ ⬇️ ⬇️")
    print(f"[{get_formatted_time()}] Starting manual refresh for user {message.from_user.id}")
    
    try:
        print(f"[{get_formatted_time()}] Checking for updates...")
        await send_updates(message.from_user.id, "yes")
        print(f"[{get_formatted_time()}] Updates check completed")
        await message.answer("just refreshed")
        print(f"[{get_formatted_time()}] ⬆️ ⬆️ ⬆️ Refresh command completed successfully ⬆️ ⬆️ ⬆️")
    except Exception as e:
        print(f"[{get_formatted_time()}] Error during refresh: {str(e)}")
        await message.answer("Error during refresh. Please try again.")


async def fetch_asos(url, headers):
    async with aiohttp.ClientSession(headers=headers) as session:
        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                print("Status code:", resp.status)
                text = await resp.text()
                print("First 500 chars of response:", text[:500])
                resp.raise_for_status()
                data = await resp.json()
                print("Item count:", data.get("itemCount"))
                return data
        except Exception as e:
            print("Exception:", e)
            return None

async def make_request(query):
    max_retries = 3
    retry_delay = 2  # seconds
    for attempt in range(max_retries):
        try:
            request_start = datetime.now()
            print(f"[{get_formatted_time()}] Starting API request attempt {attempt + 1}/{max_retries}")
            results = await fetch_asos(str(query), headers)
            request_time = (datetime.now() - request_start).total_seconds()
            print(f"[{get_formatted_time()}] API request successful (attempt {attempt + 1}) - Time taken: {request_time:.2f}s")
            if results is not None:
                return results
            else:
                raise Exception("No data returned from fetch_asos")
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"[{get_formatted_time()}] Request failed (attempt {attempt + 1}/{max_retries}): {str(e)}")
                print(f"[{get_formatted_time()}] Retrying in {retry_delay} seconds...")
                await asyncio.sleep(retry_delay)
                retry_delay *= 2
            else:
                print(f"[{get_formatted_time()}] All retry attempts failed for {query_search}")
                raise

async def send_updates(user_id, statistics):
    """
    Send updates about product discounts to a user.
    Args:
        user_id: The Telegram user ID to send updates to
        statistics: Whether to include statistics in the update ("yes" or "no")
    """
    start_time = datetime.now()
    print(f"[{get_formatted_time()}] ⬇️ ⬇️ ⬇️ Starting send_updates for user {user_id} ⬇️ ⬇️ ⬇️")
    print(f"[{get_formatted_time()}] Statistics mode: {statistics}")
    global more_what
    global offset
    global order_number
    
    try:
        # Get user's saved products
        print(f"[{get_formatted_time()}] Fetching user's saved products from database...")
        with engine.connect() as conn:
            query = text(f"SELECT DISTINCT user_input FROM asos WHERE telegram_id = '{user_id}'")
            result = conn.execute(query)
            user_inputs = [row[0] for row in result]
            
        if not user_inputs:
            print(f"[{get_formatted_time()}] No saved products found for user {user_id}")
            return
            
        print(f"[{get_formatted_time()}] Found {len(user_inputs)} products to check")
        
        # Process each product
        for user_input in user_inputs:
            try:
                product_start_time = datetime.now()
                print(f"[{get_formatted_time()}] ⬇️ ⬇️ ⬇️ Processing product: {user_input} ⬇️ ⬇️ ⬇️")
                
                # Get size ID for the product
                with engine.connect() as conn:
                    query = text(f"SELECT size_id FROM asos WHERE telegram_id = '{user_id}' AND user_input = '{user_input}'")
                    size_id = conn.execute(query).fetchone()[0]
                    print(f"[{get_formatted_time()}] Retrieved size_id: {size_id} for product")
                
                # Prepare search query
                query_search = user_input.split(', ', 1)[-1]
                query_asos = query_search.replace(" ", "+")
                print(f"[{get_formatted_time()}] Prepared search query: {query_asos}")
                
                # Make ASOS API request with timeout and retries
                print(f"[{get_formatted_time()}] Making ASOS API request for: {query_asos} + SIZE_ID: {size_id}")
                query = text(f"https://www.asos.com/api/product/search/v2/?offset=0&q={query_asos}&store=ROE&lang=en-GB&currency=EUR&rowlength=4&channel=desktop-web&country=LV&keyStoreDataversion=h7g0xmn-38&limit=200&discount_band=1%2C2%2C3%2C4%2C5%2C6%2C7&size_eu={size_id}")
                print(query)
                
                try:
                    results = await asyncio.wait_for(make_request(query), timeout=30)  # Increased overall timeout to 30 seconds
                except asyncio.TimeoutError:
                    print(f"[{get_formatted_time()}] Operation timed out after 30 seconds for {query_search}")
                    print(f"[{get_formatted_time()}] Last known state: API request in progress")
                    await bot.send_message(user_id, f"Request timed out for {user_input}. Please try again later.")
                    continue
                except Exception as e:
                    print(f"[{get_formatted_time()}] Error during API request for {query_search}: {str(e)}")
                    print(f"[{get_formatted_time()}] Error type: {type(e).__name__}")
                    await bot.send_message(user_id, f"Error fetching data for {user_input}. Please try again later.")
                    continue
                
                # After successful response
                item_count = results.get("itemCount", 0)
                print(f"[{get_formatted_time()}] Processing {item_count} items for {query_search}")
                
                # Handle different result scenarios
                if item_count > 200:
                    print(f"[{get_formatted_time()}] Too many results ({item_count}) for {query_search}")
                    await bot.send_message(user_id, "Sorry, more than 200 items available. So I Deleted one of your /products:")
                    await bot.send_message(user_id, user_input)
                    with engine.connect() as conn:
                        query = text(f"DELETE FROM asos WHERE telegram_id = '{user_id}' AND user_input = '{user_input}'")
                        conn.execute(query)
                        conn.commit()
                    continue
                    
                elif item_count == 0:
                    if statistics == "yes":
                        await bot.send_message(user_id, f"{user_input}: No discounts. Maybe you want to look for something else?")
                    continue
                
                # Process products when count is within limits
                products = results.get("products", [])
                order_number = 0
                product_counter = 0
                
                for product in products:
                    try:
                        product_counter += 1
                        with engine.connect() as conn:
                            product_id = product.get('id')
                            query_db = text(f"SELECT 1 FROM asos WHERE telegram_id = '{user_id}' AND product_id = '{product_id}'")
                            existing_product = conn.execute(query_db).fetchone()
                            
                            if not existing_product:
                                order_number += 1
                                previous_price = product.get('price', {}).get('previous', {}).get('text', 'N/A')
                                current_price = product.get('price', {}).get('current', {}).get('text', 'N/A')
                                link = "https://www.asos.com/" + product.get('url', '')
                                
                                print(f"[{get_formatted_time()}] Found new product: {product.get('name', 'Unknown')}")
                                print(f"[{get_formatted_time()}] Price change: {previous_price} --> {current_price}")
                                
                                await bot.send_message(user_id, f"{product_counter} - {product.get('name')}"
                                    f"\n{link}"
                                    f"\nPrice: {previous_price} --> {current_price}"
                                    f"\nQuery: {user_input}")
                                
                                # Save product to database
                                current_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                query_db = text(
                                    f"INSERT INTO asos (telegram_id, user_input, product_id, size_id, "
                                    f"refresh_date, previous_price, current_price, link)"
                                    f"VALUES ('{user_id}', '{user_input}', '{product_id}', '{size_id}',"
                                    f"'{current_date}', '{previous_price}', '{current_price}', '{link}')"
                                    f"ON CONFLICT (telegram_id, user_input) DO UPDATE SET refresh_date = '{current_date}'")
                                conn.execute(query_db)
                                conn.commit()
                                print(f"[{get_formatted_time()}] Saved product to database")
                                
                                if order_number > 3:
                                    print(f"[{get_formatted_time()}] Reached product limit for {user_input}")
                                    await bot.send_message(user_id, f"I analyzed {product_counter} products out of {item_count} for {user_input}"
                                        "\nshow /more?")
                                    offset = 4
                                    order_number = product_counter
                                    more_what = user_input
                                    break
                    except Exception as e:
                        print(f"[{get_formatted_time()}] Error processing product {product_counter}: {str(e)}")
                        continue
                
                if statistics == "yes":
                    print(f"[{get_formatted_time()}] Sending statistics for {user_input}")
                    await bot.send_message(user_id, f"{user_input}: Found and Analyzed {item_count} items.")
                
                product_time = (datetime.now() - product_start_time).total_seconds()
                print(f"[{get_formatted_time()}] ⬆️ ⬆️ ⬆️ Finished processing product: {user_input} (Time: {product_time:.2f}s) ⬆️ ⬆️ ⬆️")
                    
            except Exception as e:
                print(f"[{get_formatted_time()}] Error processing product {user_input}: {str(e)}")
                await bot.send_message(user_id, f"Error processing {user_input}. Skipping to next product...")
                continue
        
        total_time = (datetime.now() - start_time).total_seconds()
        print(f"[{get_formatted_time()}] ⬆️ ⬆️ ⬆️ Send updates completed successfully for user {user_id} (Total time: {total_time:.2f}s) ⬆️ ⬆️ ⬆️")
        
    except Exception as e:
        print(f"[{get_formatted_time()}] Unexpected error in send_updates: {str(e)}")
        await bot.send_message(user_id, "An unexpected error occurred while checking for updates. Please try again later.")




@dp.message() # text message handler
async def handle_text(message: types.Message):
    print(f"[{get_formatted_time()}] ⬇️ ⬇️ ⬇️ Text message handler initiated ⬇️ ⬇️ ⬇️")
    if message.text.lower().startswith("delete "):
        try:
            # Get the part after "delete "
            delete_command = message.text[7:].strip()
            
            # If it's just a number (e.g., "delete 4")
            if delete_command.isdigit():
                number = int(delete_command)
                # Get the list of products
                with engine.connect() as conn:
                    query = text(
                        """
                        WITH latest_refresh AS (
                            SELECT DISTINCT ON (user_input) user_input, refresh_date
                            FROM asos 
                            WHERE telegram_id = :telegram_id
                            ORDER BY user_input, refresh_date DESC
                        )
                        SELECT user_input 
                        FROM latest_refresh 
                        ORDER BY refresh_date DESC
                        """
                    )
                    result = conn.execute(query, {"telegram_id": message.from_user.id})
                    products = [row[0] for row in result]
                    
                    if 1 <= number <= len(products):
                        user_product = products[number - 1]
                    else:
                        await message.answer(f"❌ Invalid product number. Please use a number between 1 and {len(products)}")
                        return
            else:
                # Handle the format "delete X: product_name"
                parts = delete_command.split(":", 1)
                if len(parts) != 2:
                    await message.answer("Invalid delete format. Please use either:\n- delete 4\n- delete 4: product_name")
                    return
                    
                user_product = parts[1].strip()
                if "last discount was" in user_product:
                    user_product = user_product.split(", last discount was")[0].strip()
            
            print(f"[{get_formatted_time()}] Attempting to delete product: {user_product}")
            
            # Delete the product
            with engine.connect() as conn:
                query = text(
                    "DELETE FROM asos WHERE telegram_id = :telegram_id AND user_input = :user_input"
                )
                result = conn.execute(
                    query,
                    {"telegram_id": message.from_user.id, "user_input": user_product}
                )
                conn.commit()
                
                if result.rowcount > 0:
                    await message.answer(f"✅ Successfully deleted: {user_product}")
                else:
                    await message.answer(f"❌ Could not find product to delete: {user_product}")
                
            await message.answer("Check your updated /products list 📦")
            print(f"[{get_formatted_time()}] ⬆️ ⬆️ ⬆️ Delete operation completed successfully ⬆️ ⬆️ ⬆️")
            
        except Exception as e:
            print(f"[{get_formatted_time()}] Error during delete operation: {str(e)}")
            await message.answer(f"❌ Error occurred while deleting: {str(e)}")
    else:
        global more_what
        global offset
        global order_number
        more_what = message.text
        offset = 0
        order_number = 0
        await more(message)



def size_replace(size):
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
    if size == "sizes_db":
        sizes_text = ', '.join(map(str, sizes_db.keys()))
        return sizes_text
    if size in sizes_db:
        final_id = sizes_db[size]
        return final_id
    else:
        return ""

def signal_handler(sig, frame):
    print(f"\n[{get_formatted_time()}] Received interrupt signal. Cleaning up...")
    asyncio.run(cleanup())
    sys.exit(0)

# Register signal handlers
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

async def main():
    try:
        print(f"[{get_formatted_time()}] ⬇️ ⬇️ ⬇️ Bot initialization started ⬇️ ⬇️ ⬇️")
        # Create a Bot instance with the specified token (needed to send messages without user's message)
        bot = Bot(token=TOKEN)
        # Start polling for updates using the Dispatcher
        await dp.start_polling(bot, skip_updates=True)
        print(f"[{get_formatted_time()}] ⬆️ ⬆️ ⬆️ Bot initialization completed successfully ⬆️ ⬆️ ⬆️")
    except Exception as e:
        print(f"[{get_formatted_time()}] Error in main: {str(e)}")
    finally:
        await cleanup()

if __name__ == '__main__':
    try:
        print(f"[{get_formatted_time()}] ⬇️ ⬇️ ⬇️ Bot startup initiated ⬇️ ⬇️ ⬇️")
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n[{get_formatted_time()}] Received keyboard interrupt. Exiting...")
    except Exception as e:
        print(f"[{get_formatted_time()}] Error: {str(e)}")
    finally:
        print(f"[{get_formatted_time()}] ⬆️ ⬆️ ⬆️ Bot shutdown completed ⬆️ ⬆️ ⬆️")
