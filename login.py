from telethon import TelegramClient, events
from telethon.errors import SessionPasswordNeededError

# для userbot
api_id = 19203792
api_hash = '7338aa03be99dd1860924aefdb6734b6'

userbot = TelegramClient('db/user_session', api_id, api_hash)

async def main():
    await userbot.connect()
    if not await userbot.is_user_authorized():
        phone = input("Phone number (example +79998887766): ")
        await userbot.send_code_request(phone)

        code = input("Code from Telegram: ")
        try:
            await userbot.sign_in(phone=phone, code=code)
        except SessionPasswordNeededError:
            password = input("Password (2FA): ")
            await userbot.sign_in(password=password)