import asyncio
import os
from pyrogram import Client, filters
from pyrogram.enums import ParseMode
from pyrogram.session import StringSession
from pyrogram.errors import SessionPasswordNeeded, PhoneCodeInvalid

BOT_API_ID = int(os.getenv("BOT_API_ID"))
BOT_API_HASH = os.getenv("BOT_API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID"))

bot = Client("gen_session_bot", api_id=BOT_API_ID, api_hash=BOT_API_HASH, bot_token=BOT_TOKEN)

user_states = {}

@bot.on_message(filters.private & filters.command("start"))
async def start_handler(client, message):
    await message.reply_text("👋 Welcome! Use /getsession to generate a Pyrogram session string (Owner only).")

@bot.on_message(filters.private & filters.command("getsession") & filters.user(OWNER_ID))
async def get_session_handler(client, message):
    await message.reply_text("📩 Send your API ID:")
    user_states[message.from_user.id] = {"step": "api_id"}

@bot.on_message(filters.private & filters.user(OWNER_ID))
async def collect_info(client, message):
    user_id = message.from_user.id
    if user_id not in user_states:
        return

    state = user_states[user_id]

    # Step 1: API ID
    if state["step"] == "api_id":
        try:
            api_id = int(message.text)
            user_states[user_id]["api_id"] = api_id
            user_states[user_id]["step"] = "api_hash"
            await message.reply_text("🔑 Send your API HASH:")
        except:
            await message.reply_text("❌ Invalid API ID. Please send a number.")

    # Step 2: API Hash
    elif state["step"] == "api_hash":
        api_hash = message.text.strip()
        user_states[user_id]["api_hash"] = api_hash
        user_states[user_id]["step"] = "phone"
        await message.reply_text("📞 Send your phone number (with country code):")

    # Step 3: Phone number
    elif state["step"] == "phone":
        phone = message.text.strip()
        api_id = user_states[user_id]["api_id"]
        api_hash = user_states[user_id]["api_hash"]
        user_states[user_id]["phone"] = phone

        app = Client(StringSession(), api_id=api_id, api_hash=api_hash)
        await app.connect()
        try:
            sent_code = await app.send_code(phone)
            user_states[user_id]["client"] = app
            user_states[user_id]["code_hash"] = sent_code.phone_code_hash
            user_states[user_id]["step"] = "otp"
            await message.reply_text("📲 Enter the OTP code you received:")
        except Exception as e:
            await app.disconnect()
            del user_states[user_id]
            await message.reply_text(f"❌ Failed to send code: `{e}`", parse_mode=ParseMode.MARKDOWN)

    # Step 4: OTP
    elif state["step"] == "otp":
        otp = message.text.strip()
        app = state["client"]
        phone = state["phone"]
        code_hash = state["code_hash"]

        try:
            await app.sign_in(phone_number=phone, phone_code_hash=code_hash, phone_code=otp)
        except SessionPasswordNeeded:
            user_states[user_id]["step"] = "password"
            await message.reply_text("🔐 2FA Password is enabled. Send your password:")
            return
        except PhoneCodeInvalid:
            await message.reply_text("❌ Invalid OTP. Please restart with /getsession")
            await app.disconnect()
            del user_states[user_id]
            return
        except Exception as e:
            await message.reply_text(f"❌ Error signing in: `{e}`")
            await app.disconnect()
            del user_states[user_id]
            return

        session = app.export_session_string()
        await message.reply_text(f"✅ Your SESSION STRING:\n\n`{session}`", parse_mode=ParseMode.MARKDOWN)
        await app.disconnect()
        del user_states[user_id]

    # Step 5: 2FA Password
    elif state["step"] == "password":
        password = message.text.strip()
        app = state["client"]
        try:
            await app.check_password(password)
            session = app.export_session_string()
            await message.reply_text(f"✅ Your SESSION STRING:\n\n`{session}`", parse_mode=ParseMode.MARKDOWN)
        except Exception as e:
            await message.reply_text(f"❌ Password error: `{e}`", parse_mode=ParseMode.MARKDOWN)
        await app.disconnect()
        del user_states[user_id]

bot.run()
