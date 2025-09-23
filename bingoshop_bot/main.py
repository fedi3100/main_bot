import logging
import os
import sys
import requests
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

# Logging setup
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# Bot tokens
TOKEN = os.getenv("SHOP_BOT_TOKEN", "YOUR_SHOP_BOT_TOKEN")
ADMIN_BOT_TOKEN = os.getenv("ADMIN_BOT_TOKEN", "YOUR_ADMIN_BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", 6146268714))

# Get Render environment variables
RENDER_EXTERNAL_HOSTNAME = os.getenv('RENDER_EXTERNAL_HOSTNAME')
RENDER_GIT_COMMIT = os.getenv('RENDER_GIT_COMMIT', 'unknown')

# Wallets
BTC_WALLET = "3GqQV93WBW3ZWiHfx1JGu6nrgWfgADWL29"
USDT_WALLET = "TSEC8xaDprqJ21qFZ9pBNBhDHDJTccVUfr"

# Products
PRODUCTS = {
    "high_limit": {
        "name": "High Limit SMTP",
        "price": 100,
        "description": "50K Sending Limit<br>Sends To Inbox (Aged Gmail Tested)<br>STARTTLS Encryption Enabled<br>SPF & DMARC Authentication Validated<br>Fresh Hacked SMTP<br>SMS + Email Support<br>7 Day Free Replacements",
    },
    "spoofable": {
        "name": "Spoofable SMTP",
        "price": 200,
        "description": "50K Sending Limit<br>Sends To Inbox (Aged Gmail Tested)<br>STARTTLS Encryption Enabled<br>SPF & DMARC Authentication Validated<br>Fresh Hacked SMTP<br>SMS + Email Support<br>Supports Sender Address Spoofing<br>Includes Multiple Spoofing Methods<br>Multi-Provider Spoofing Support<br>7 Day Free Replacements<br>Includes SenderV4 Mailer Script",
    },
    "custom_spoofable": {
        "name": "Custom Spoofable SMTP",
        "price": 300,
        "description": "50K Sending Limit<br>Sends To Inbox (Aged Gmail Tested)<br>STARTTLS Encryption Enabled<br>SPF & DMARC Authentication Validated<br>Fresh Hacked SMTP<br>SMS + Email Support<br>Supports Sender Address Spoofing<br>Includes Multiple Spoofing Methods<br>Multi-Provider Spoofing Support<br>Your Own Custom SMTP Domain Name<br>7 Day Free Replacements<br>Includes SenderV4 Mailer Script",
    },
}

user_orders = {}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("📦 SMTPS", callback_data="smtps_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "🛍️ Welcome to <b>BingoShop</b>!\n\n✅ Inbox All Providers\n✅ 7 Day Free Replacement\n✅ Fast Delivery",
        reply_markup=reply_markup,
        parse_mode="HTML",
    )


async def smtps_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    keyboard = [
        [InlineKeyboardButton("High Limit SMTP - $100", callback_data="product_high_limit")],
        [InlineKeyboardButton("Spoofable SMTP - $200", callback_data="product_spoofable")],
        [InlineKeyboardButton("Custom Spoofable SMTP - $300", callback_data="product_custom_spoofable")],
        [InlineKeyboardButton("🔙 Retour", callback_data="start_menu")],
    ]
    await query.edit_message_text("📦 Choose an SMTP option:", reply_markup=InlineKeyboardMarkup(keyboard))


async def show_product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    product_id = query.data.replace("product_", "")
    product = PRODUCTS[product_id]

    keyboard = [
        [InlineKeyboardButton("💳 Buy Now", callback_data=f"buy_{product_id}")],
        [InlineKeyboardButton("🔙 Retour", callback_data="smtps_menu")],
    ]
    await query.edit_message_text(
        f"<b>{product['name']}</b>\n💵 Price: ${product['price']}\n\n📝 Description:<br>{product['description']}",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML",
    )


async def buy_product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    product_id = query.data.replace("buy_", "")
    product = PRODUCTS[product_id]
    user_id = query.from_user.id

    user_orders[user_id] = {"product": product["name"], "price": product["price"], "status": "pending_payment"}

    keyboard = [[InlineKeyboardButton("🔙 Retour", callback_data=f"product_{product_id}")]]
    payment_text = (
        f"Please send <b>${product['price']}</b> to one of these wallets:<br><br>"
        f"💰 <b>Bitcoin (BTC):</b><br><code>{BTC_WALLET}</code><br><br>"
        f"💰 <b>USDT (TRC20):</b><br><code>{USDT_WALLET}</code><br><br>"
        "After payment, send a screenshot here.<br>"
        "Your SMTP will be delivered within 7 minutes.<br><br>"
        "Support: @support_bot"
    )

    await query.edit_message_text(payment_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")


async def handle_screenshot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id not in user_orders:
        await update.message.reply_text("⚠️ Please select a product first with /start")
        return

    order = user_orders[user_id]
    caption = (
        f"[BingoShop] Payment screenshot received!\n"
        f"User: {update.message.from_user.full_name} (@{update.message.from_user.username})\n"
        f"Product: {order['product']}\nPrice: ${order['price']}\nStatus: {order['status']}"
    )

    photo_file_id = update.message.photo[-1].file_id
    try:
        file_resp = requests.get(f"https://api.telegram.org/bot{TOKEN}/getFile?file_id={photo_file_id}")
        file_path = file_resp.json()["result"]["file_path"]
        file_bytes = requests.get(f"https://api.telegram.org/file/bot{TOKEN}/{file_path}").content

        requests.post(
            f"https://api.telegram.org/bot{ADMIN_BOT_TOKEN}/sendPhoto",
            data={"chat_id": ADMIN_ID, "caption": caption},
            files={"photo": ("screenshot.jpg", file_bytes)},
        )
    except Exception as e:
        logger.error(f"Failed to send screenshot: {e}")

    await update.message.reply_text("✅ Screenshot received. Your order is being processed.")


async def health_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Health check command to verify the bot is running"""
    await update.message.reply_text(
        f"✅ Bot is running!\n"
        f"Commit: {RENDER_GIT_COMMIT}\n"
        f"Host: {RENDER_EXTERNAL_HOSTNAME or 'Local'}"
    )


def main():
    logger.info(f"Starting bingoshop_bot with Python {sys.version}")
    
    # Check Python version compatibility
    if sys.version_info >= (3, 12):
        logger.error("python-telegram-bot v20.x is not compatible with Python 3.12+. Use Python 3.11.9.")
        raise SystemExit(1)

    # Create application
    application = Application.builder().token(TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("health", health_check))
    application.add_handler(CallbackQueryHandler(smtps_menu, pattern="^smtps_menu$"))
    application.add_handler(CallbackQueryHandler(show_product, pattern="^product_"))
    application.add_handler(CallbackQueryHandler(buy_product, pattern="^buy_"))
    application.add_handler(CallbackQueryHandler(start, pattern="^start_menu$"))
    application.add_handler(MessageHandler(filters.PHOTO, handle_screenshot))

    # Check if we're running on Render (with webhook) or locally (with polling)
    if RENDER_EXTERNAL_HOSTNAME:
        # Webhook mode for Render
        webhook_url = f"https://{RENDER_EXTERNAL_HOSTNAME}/webhook"
        logger.info(f"Starting webhook mode on {webhook_url}")
        
        # Set webhook - this is important!
        application.run_webhook(
            listen="0.0.0.0",
            port=int(os.environ.get("PORT", 8443)),
            url_path=TOKEN,
            webhook_url=webhook_url
        )
    else:
        # Polling mode for local development
        logger.info("Starting polling mode for local development")
        application.run_polling()


if __name__ == "__main__":
    main()
