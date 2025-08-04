import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.sessions import StringSession
from pyrogram.errors import SessionPasswordNeeded
import os

BOT_API_ID = int(os.environ.get("BOT_API_ID"))
BOT_API_HASH = os.environ.get("BOT_API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN")
OWNER_ID = int(os.environ.get("OWNER_ID"))

bot = Client("session_bot", api_id=BOT_API_ID, api_hash=BOT_API_HASH, bot_token=BOT_TOKEN)

@bot.on_message(filters.command("getsession") & filters.user(OWNER_ID))
async def generate_session(_, message: Message):
    await message.reply("📩 Send your API ID:")
    api_id_msg = await bot.listen(message.chat.id)
    api_id = int(api_id_msg.text)

    await message.reply("🔑 Send your API HASH:")
    api_hash_msg = await bot.listen(message.chat.id)
    api_hash = api_hash_msg.text

    await message.reply("📞 Send your phone number (with country code):")
    phone_msg = await bot.listen(message.chat.id)
    phone = phone_msg.text.strip()

    async with Client(StringSession(), api_id=api_id, api_hash=api_hash) as app:
        try:
            sent_code = await app.send_code(phone)
            await message.reply("📲 Enter the OTP code you received:")
            otp_msg = await bot.listen(message.chat.id)
            otp = otp_msg.text.strip()

            try:
                await app.sign_in(phone, sent_code.phone_code_hash, otp)
            except SessionPasswordNeeded:
                await message.reply("🔐 Send your 2FA password:")
                pw_msg = await bot.listen(message.chat.id)
                password = pw_msg.text.strip()
                await app.check_password(password)

            session_str = app.export_session_string()
            await message.reply(f"✅ **SESSION STRING:**\n\n`{session_str}`")
        except Exception as e:
            await message.reply(f"❌ Error:\n`{str(e)}`")

bot.run()
