import telebot
import requests
from flask import Flask, request
from telebot import types
from datetime import datetime, timedelta, timezone
import os

# 1. Setup Flask and Bot
BOT_TOKEN = os.environ.get('DUCKYDUCK_TOKEN')
# BOT_TOKEN = '7429676241:AAHacB_Byvxk1Dw_Ogv22qDOfOh9_KBs8mQ'
bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)
last_message_ids = dict()

# --- Keep your existing functions (get_crypto_price, etc.) ---
def get_crypto_price_coinmarketcap(symbol):
    url = f"https://api.kucoin.com/api/v1/market/orderbook/level1?symbol={symbol}"
    response = requests.get(url)
    data = response.json()

    utc_time = datetime.now(timezone.utc)
    est_offset = timedelta(hours=3.5)
    est_time = utc_time.astimezone(timezone(est_offset)).replace(microsecond=0)

    est_time = str(est_time)[:-6]

    
    return data['data']['price'], est_time


@bot.message_handler(commands=['start'])
def send_welcome(message):
    # Create inline keyboard
    keyboard = types.InlineKeyboardMarkup()
    
    button1 = types.InlineKeyboardButton(text="💰 Symbol price", callback_data='symbolPrice')
    
    keyboard.add(button1)  # Add buttons to the keyboard
    
    sent = bot.send_message(message.chat.id, f"Oi Oi, How you doin, {message.from_user.first_name}?\nWhat can I do for you?", reply_markup=keyboard)
    last_message_ids[message.chat.id] = sent.message_id  # Save the message ID


def show_symbols(chat_id):
    # Create the second inline keyboard
    keyboard = types.InlineKeyboardMarkup()
    button3 = types.InlineKeyboardButton(text="    🔄 Back 🔄   ", callback_data='back')
    button4 = types.InlineKeyboardButton(text="    🪙 BTC 🪙    ", callback_data='BTC')
    button5 = types.InlineKeyboardButton(text="    🪙 TON 🪙    ", callback_data='TON')
    button6 = types.InlineKeyboardButton(text="    🪙 ETH 🪙    ", callback_data='ETH')
    button7 = types.InlineKeyboardButton(text="    🪙 HMSTR 🪙    ", callback_data='HMSTR')

    keyboard.add(button3, button4, button5, button6, button7)
    sent_message = bot.send_message(chat_id, "Choose a crypto currency:", reply_markup=keyboard)
    last_message_ids[chat_id] = sent_message.message_id  # Save the new message ID


@bot.callback_query_handler(func=lambda call: call.data in ["symbolPrice", "back"])
def handle_callback(call):
    # Delete the previous message
    if call.message.chat.id in last_message_ids:
        bot.delete_message(call.message.chat.id, last_message_ids[call.message.chat.id])

    if (call.data == "symbolPrice"):
        show_symbols(call.message.chat.id)
    else:
        bot.send_message(call.message.chat.id, "wtf?")


@bot.callback_query_handler(func= lambda call: call.data in ["BTC", "TON", "ETH", "HMSTR"])
def show_price(call):
    price, date = get_crypto_price_coinmarketcap(call.data + "-" + "USDT")
    ans = f"Date -> {date}📅\nCoin -> {call.data}🪙\nPrice -> {price} USDT💵"
    bot.send_message(call.message.chat.id, ans)



# 2. CREATE THE WEB SERVICE ROUTE
@app.route('/' + BOT_TOKEN, methods=['POST'])
def getMessage():
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "!", 200

@app.route("/")
def webhook():
    bot.remove_webhook()
    # USE YOUR NEW CLOUDFLARE URL
    bot.set_webhook(url='https://bags-deer-egg-settled.trycloudflare.com/' + BOT_TOKEN)
    return "Webhook set!", 200

# 3. RUN THE FLASK APP
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))