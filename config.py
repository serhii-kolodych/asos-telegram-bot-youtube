# 📺 watch Python Tutorial for this code on YouTube: https://www.youtube.com/@serhiikolodych

# ✅ 1. TOKEN for your bot you can get from BotFather in Telegram: https://t.me/botfather
TOKEN = ""

# ✅ 2. Token for my database looks like this: "dialect+driver://username:password@host:port/database"
# I'm using PlanetScale: https://planetscale.com
engine_token = ""

# ✅ 3. After inserting engine_token don't forget to create database table, by writing:
# CREATE TABLE `asos` (`id` int NOT NULL AUTO_INCREMENT, `telegram_id` int, `user_input` varchar(255), `product_id` int, `size_id` varchar(255), `refresh_date` datetime, `previous_price` varchar(255), `current_price` varchar(255), `link` text, PRIMARY KEY (`id`), UNIQUE KEY `telegram_id` (`telegram_id`, `product_id`))
