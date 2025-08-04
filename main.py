import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.sessions import StringSession
from pyrogram.errors import SessionPasswordNeeded
import os

API_ID = int(os.environ.get("BOT_API_ID"))
API_HASH = os.environ.get("BOT_API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN")
OWNER_ID = int(os.environ.get("OWNER_ID"))

bot = Client("session_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

@bot.on_message(filters.command("getsession") & filters.user(OWNER_ID))
async def start_session_generator(_, message: Message):
    await message.reply_text("📨 Send your API ID:")
    api_id_msg = await bot.listen(message.chat.id)
    api_id = int(api_id_msg.text)

    await message.reply_text("🔑 Send your API HASH:")
    api_hash_msg = await bot.listen(message.chat.id)
    api_hash = api_hash_msg.text

    await message.reply_text("📱 Send your phone number with country code:")
    phone_msg = await bot.listen(message.chat.id)
    phone = phone_msg.text.strip()

    app = Client(
        session_name=StringSession(),
        api_id=api_id,
        api_hash=api_hash,
        in_memory=True
    )

    async with app:
        try:
            code = await app.send_code(phone)
            await message.reply_text("📩 Enter the OTP:")
            otp_msg = await bot.listen(message.chat.id)
            otp = otp_msg.text.strip()

            try:
                await app.sign_in(phone_number=phone, phone_code_hash=code.phone_code_hash, phone_code=otp)
            except SessionPasswordNeeded:
                await message.reply_text("🔐 2FA Password is enabled, send it:")
                pw_msg = await bot.listen(message.chat.id)
                pw = pw_msg.text.strip()
                await app.check_password(password=pw)

            session_string = app.export_session_string()
            await message.reply_text(f"✅ **SESSION STRING:**\n\n`{session_string}`")
        except Exception as e:
            await message.reply_text(f"❌ ERROR:\n`{str(e)}`")

bot.run()
