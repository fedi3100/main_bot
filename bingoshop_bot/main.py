
import asyncio
import logging
import os
import sys

import requests
from telegram import (InlineKeyboardButton, InlineKeyboardMarkup, InputFile,
                      Update)
from telegram.ext import (Application, CallbackQueryHandler, CommandHandler,
                          ContextTypes, MessageHandler, filters)

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


# Bot Token from environment variable
TOKEN = "8351481104:AAHYs8pUnyNwduTceytI-sGzz7UJ84PWNeI"

# Admin bot details (hard-coded per user request)
ADMIN_BOT_TOKEN = "7603048146:AAG1pwQg9W63MHv_89TV8cRufJH8WQNns80"
ADMIN_ID = 6146268714

# Wallet addresses
BTC_WALLET = "3GqQV93WBW3ZWiHfx1JGu6nrgWfgADWL29"
USDT_WALLET = "TSEC8xaDprqJ21qFZ9pBNBhDHDJTccVUfr"

# Products
PRODUCTS = {
    "high_limit": {
        "name": "High Limit SMTP",
        "price": 100,
        "description": "50K Sending Limit\nSends To Inbox (Aged Gmail Tested)\nSTARTTLS Encryption Enabled\nSPF & DMARC Authentication Validated\nFresh Hacked SMTP\nSMS + Email Support\n7 Day Free Replacements"
    },
    "spoofable": {
        "name": "Spoofable SMTP",
        "price": 200,
        "description": "50K Sending Limit\nSends To Inbox (Aged Gmail Tested)\nSTARTTLS Encryption Enabled\nSPF & DMARC Authentication Validated\nFresh Hacked SMTP\nSMS + Email Support\nSupports Sender Address Spoofing\nIncludes Multiple Spoofing Methods\nMulti-Provider Spoofing Support\n7 Day Free Replacements\nIncludes SenderV4 Mailer Script"
    },
    "custom_spoofable": {
        "name": "Custom Spoofable SMTP",
        "price": 300,
        "description": "50K Sending Limit\nSends To Inbox (Aged Gmail Tested)\nSTARTTLS Encryption Enabled\nSPF & DMARC Authentication Validated\nFresh Hacked SMTP\nSMS + Email Support\nSupports Sender Address Spoofing\nIncludes Multiple Spoofing Methods\nMulti-Provider Spoofing Support\nYour Own Custom SMTP Domain Name\n7 Day Free Replacements\nIncludes SenderV4 Mailer Script"
    }
}

# User orders storage
user_orders = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /start is issued."""
    keyboard = [[InlineKeyboardButton("SMTPS", callback_data='smtps_menu')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    # Try to send smtp.png as a welcome image, fallback to text if not found
    try:
        with open(os.path.join(os.path.dirname(__file__), '../smtp.png'), 'rb') as img:
            await update.message.reply_photo(
                photo=img,
                caption="🛍️ Welcome to BingoShop! 🛍️\n\nWe deliver premium SMTPs for all your needs.\n\n✅ Inbox All Providers\n✅ 7 Day Free Replacement\n✅ Fast Delivery",
                reply_markup=reply_markup
            )
    except Exception as e:
        await update.message.reply_text(
            text="🛍️ Welcome to BingoShop! 🛍️\n\nWe deliver premium SMTPs for all your needs.\n\n✅ Inbox All Providers\n✅ 7 Day Free Replacement\n✅ Fast Delivery",
            reply_markup=reply_markup
        )

async def smtps_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show SMTP options"""
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [InlineKeyboardButton("High Limit SMTP - $100", callback_data='product_high_limit')],
        [InlineKeyboardButton("Spoofable SMTP - $200", callback_data='product_spoofable')],
        [InlineKeyboardButton("Custom Spoofable SMTP - $300", callback_data='product_custom_spoofable')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        text="Choose an SMTP option:",
        reply_markup=reply_markup
    )

async def show_product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show product details"""
    query = update.callback_query
    await query.answer()
    
    product_id = query.data.replace('product_', '')
    product = PRODUCTS[product_id]
    
    keyboard = [[InlineKeyboardButton("Buy Now", callback_data=f'buy_{product_id}')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        text=f"🚀 {product['name']}\n💵 Price: ${product['price']}\n\n📝 Description:\n{product['description']}",
        reply_markup=reply_markup
    )

async def buy_product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle product purchase"""
    query = update.callback_query
    await query.answer()
    
    product_id = query.data.replace('buy_', '')
    product = PRODUCTS[product_id]
    
    # Store user order
    user_id = query.from_user.id
    user_orders[user_id] = {
        "product": product['name'],
        "price": product['price'],
        "status": "pending_payment"
    }
    
    def escape_md(text):
        chars = r'_ * [ ] ( ) ~ ` > # + - = | { } . !'
        for c in chars.split():
            text = text.replace(c, '\\' + c)
        return text

    payment_text = f"Please send ${product['price']} to one of these wallets:\n\n"
    payment_text += f"💰 Bitcoin (BTC):\n`{BTC_WALLET}`\n\n"
    payment_text += f"💰 USDT (TRC20):\n`{USDT_WALLET}`\n\n"
    payment_text += "After sending, please send a screenshot of the transaction here.\n"
    payment_text += "Your SMTP will be delivered within 7 minutes after payment confirmation.\n\n"
    payment_text += "For any problems, contact our support bot: @support_bot"

    payment_text_escaped = escape_md(payment_text)
    await query.edit_message_text(
        text=payment_text_escaped,
        parse_mode='MarkdownV2'
    )

async def handle_screenshot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle screenshot from user"""
    user = update.message.from_user
    user_id = user.id
    if user_id in user_orders:
        order = user_orders[user_id]
        caption = (
            f"[BingoShop] New payment screenshot received!\n"
            f"User: {user.full_name} (@{user.username})\nUser ID: {user_id}\n"
            f"Product: {order['product']}\nPrice: ${order['price']}\n"
            f"Status: {order['status']}"
        )
        # Get the file_id of the largest photo
        photo_file_id = update.message.photo[-1].file_id

        # Step 1: Get file path from Telegram API (shop bot)
        get_file_url = f"https://api.telegram.org/bot{TOKEN}/getFile?file_id={photo_file_id}"
        file_resp = requests.get(get_file_url)
        file_path = file_resp.json()["result"]["file_path"]

        # Step 2: Download the file bytes
        file_url = f"https://api.telegram.org/file/bot{TOKEN}/{file_path}"
        file_bytes = requests.get(file_url).content

        # Step 3: Send to admin bot using its API (upload file)
        send_url = f"https://api.telegram.org/bot{ADMIN_BOT_TOKEN}/sendPhoto"
        files = {"photo": ("screenshot.jpg", file_bytes)}
        data = {"chat_id": ADMIN_ID, "caption": caption}
        try:
            requests.post(send_url, data=data, files=files)
        except Exception as e:
            logger.error(f"Failed to send photo to admin bot: {e}")

        await update.message.reply_text(
            "Thank you! We've received your payment screenshot. "
            "Your order is being processed and will be delivered within 7 minutes. "
            "For any issues, contact @support_bot."
        )
    else:
        await update.message.reply_text(
            "Please select a product first using the /start command."
        )

def main():
    """Start the bot."""
    logger.info(f"Starting bingoshop_bot with Python {sys.version}")
    if sys.version_info >= (3, 12):
        logger.error(
            "Incompatible Python runtime detected. python-telegram-bot v20.x is not compatible with Python 3.12+.\n"
            "Please set your Render service runtime to Python 3.11.9 (use runtime.txt or service settings)."
        )
        raise SystemExit(1)
    # Enforce compatible Python version for python-telegram-bot v20.x
    if sys.version_info >= (3, 12):
        logger.error(
            "Incompatible Python runtime detected. python-telegram-bot v20.x is not compatible with Python 3.12+.\n"
            "Please set your Render service runtime to Python 3.11.9 (use runtime.txt or service settings)."
        )
        raise SystemExit(1)
    if not TOKEN:
        logger.error("BOT_TOKEN environment variable not set!")
        return
    if not ADMIN_BOT_TOKEN:
        logger.warning("ADMIN_BOT_TOKEN not set; admin notifications will fail until configured.")
    
    application = Application.builder().token(TOKEN).build()

    # Command handlers
    application.add_handler(CommandHandler("start", start))
    
    # Callback query handlers
    application.add_handler(CallbackQueryHandler(smtps_menu, pattern='^smtps_menu$'))
    application.add_handler(CallbackQueryHandler(show_product, pattern='^product_'))
    application.add_handler(CallbackQueryHandler(buy_product, pattern='^buy_'))
    
    # Message handlers
    application.add_handler(MessageHandler(filters.PHOTO, handle_screenshot))

    # Start the Bot
    application.run_polling()

if __name__ == '__main__':
    main()