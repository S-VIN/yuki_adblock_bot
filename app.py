from telethon import TelegramClient, events
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.tl.functions.channels import LeaveChannelRequest
import re
import db
import asyncio
import os


api_id = int(os.environ.get("TG_API_ID", 111111111))
api_hash = os.environ.get("TG_API_HASH", "default_api_hash")

userbot = TelegramClient('db/user_session', api_id, api_hash)

default_filter_words = ['реклама', 'advertisement', '#реклама', 'о рекламодателе', 'предложение', 'донат', 'спасибо', 'канал', 'подписаться']


########################################################################################################################
# userbot funcs
########################################################################################################################

async def join_channel(channel_username):
    entity = await userbot.get_entity(channel_username)
    if entity.left:
        try:
            await userbot(JoinChannelRequest(channel_username))
            return None
        except Exception as e:
            return "Subscription error"
    return None


async def leave_channel(channel_username):
    try:
        entity = await userbot.get_entity(channel_username)
        if not entity.left:
            await userbot(LeaveChannelRequest(channel_username))
            return None
        return "Already left"
    except Exception as e:
        return f"Unsubscription error: {e}"


async def send_instructions(chat_id):
    instructions = f'''
👋 Welcome to the Ad-Free Channel Forwarder Bot!

This bot helps you follow public Telegram channels without seeing ads.
It automatically forwards new posts from selected channels, **excluding advertisements** based on filter keywords.

✨ Here’s how to use the bot:

📥 **1. Add a channel**
Just send a link to a public channel (like `https://t.me/somechannel`) to subscribe to it.

🗑️ **2. Remove a channel**
Send:
`delete https://t.me/somechannel`

🚫 **3. Add a new filter word**
Send:
`add filter yourword`

Messages containing that word will be blocked.

♻️ **4. Remove a filter word**
Send:
`delete filter yourword`

📋 **5. View your current subscriptions and filters**
Send:
`ls`

🔍 **Default filter words:** {default_filter_words}  
(you can add more to block other unwanted content)

---

💡 Tip: This bot only works with **public** channels and skips messages that match your filter list.

Happy reading — minus the ads! ✨
'''
    msg = await userbot.send_message(chat_id, instructions)
    await userbot.pin_message(chat_id, msg, notify=False)
    db.register_sending_instructions(chat_id)


async def add_channel_command(event, sender, channel_username):
    user_id = sender.id
    if len(db.get_all_channels_for_user(user_id)) >= 10:
        await event.respond(
            f"⚠️ You can subscribe up to 10 channels only.")
        return
    
    if len(channel_username) > 300:
        await event.respond(
            f"⚠️ Channel username must be less than 300 characters.")
        return 
    
    db.add_subscription(user_id, channel_username)
    await join_channel(channel_username)
    await event.respond(
        f"✅ You are now subscribed to @{channel_username}.")


async def delete_channel_command(event, sender, channel_username):
    user_id = sender.id
    result = db.delete_subscription(user_id, channel_username)
    if result:
        await event.respond(f"✅ Success unsubscribe from @{channel_username}.")
    else:
        await event.respond(f"⚠️ Wrong unsubscribe from @{channel_username}. No subscription to channel.")


async def ls_command(event, sender):
    user_id = sender.id
    all_channels = db.get_all_channels_for_user(user_id)
    all_filter_words = db.get_filters(user_id)
    response_message = 'Your filter words: \n'
    for filter_word in all_filter_words:
        response_message += f"- `{filter_word}`\n"
    response_message += "\n Your current subscriptions: \n"
    for channel in all_channels:
        response_message += f"- `@{channel}`\n"
    await event.respond(response_message)


async def add_filter_command(event, sender, new_filter_word):
    user_id = sender.id
    word = new_filter_word.strip()

    if len(word) < 3 or len(word) > 30:
        await event.respond("⚠️ Filter word must be between 3 and 30 characters.")
        return

    if ' ' in word:
        await event.respond("⚠️ Filter must be a single word without spaces.")
        return

    if not re.match(r'^[\w\-]+$', word):
        await event.respond("⚠️ Filter can only contain letters, digits, underscores or hyphens.")
        return

    filters = db.get_filters(user_id)
    if word.lower() not in [f.lower() for f in filters]:
        filters.append(word)
        db.set_filters(user_id, filters)
        await event.respond(f"✅ Successfully added new filter word: `{word}`")
    else:
        await event.respond(f"⚠️ Filter `{word}` already exists.")


async def delete_filter_command(event, sender, new_filter_word):
    user_id = sender.id
    filter = db.get_filters(user_id)
    if new_filter_word not in filter:
        await event.respond(f'⚠️ Filter `{new_filter_word}` does not exist.')
    else:
        filter.remove(new_filter_word)
        db.set_filters(user_id, filter)
        await event.respond(f"✅ Filter `{new_filter_word}` successfully removed.")


async def process_message_from_user(event, sender):
    user_id = sender.id
    if not db.is_instructions_was_sent(user_id):
        await send_instructions(event.chat_id)
        db.set_filters(user_id, default_filter_words)
        return

    text = event.raw_text.strip()
    if len(text) > 200:
        return

    # === Команда: /ls
    if text.lower() == "ls":
        await ls_command(event, sender)
        return

    # === Команда: add filter <word>
    if text.lower().startswith("add filter "):
        word = text[11:].strip()
        if word:
            await add_filter_command(event, sender, word)
        else:
            await event.respond("⚠️ Use word after 'add filter'")
        return

    # === Команда: delete filter <word>
    if text.lower().startswith("delete filter "):
        word = text[14:].strip()
        if word:
            await delete_filter_command(event, sender, word)
        else:
            await event.respond("⚠️ Use word after 'delete filter'")
        return

    # === Команда: delete <channel_link>
    if text.lower().startswith("delete "):
        match = re.match(r'delete\s+https?://t\.me/([a-zA-Z0-9_]{5,})', text, re.IGNORECASE)
        if match:
            channel_username = match.group(1)
            await delete_channel_command(event, sender, channel_username)
        else:
            await event.respond("⚠️ Use command in format: delete https://t.me/channel_name")
        return

    # === Добавление новой подписки (если просто ссылка)
    match = re.match(r'https?://t\.me/([a-zA-Z0-9_]{5,})', text)
    if match:
        await add_channel_command(event, sender, match.group(1))
    else:
        await event.respond(
            "📎 Plese send link to channel in format: https://t.me/channel_name\n"
            "Or use command: ls, add filter ..., delete filter ..., delete ...")


def filter_message(filters, message):
    message_lower = message.lower()
    for filter in filters:
        if filter in message_lower:
            return False
    return True


async def process_message_from_channel(event, sender):
    chat = await event.get_chat()
    channel_username = getattr(chat, 'username', None)
    if not channel_username:
        print("Channel has no username, skipping...")
        return

    message_text = event.raw_text.lower()
    subscribers = db.get_subscribers(channel_username)

    for user_id in subscribers:
        filters = db.get_filters(user_id)
        if not filter_message(filters, message_text):
            continue
        # Forward message
        await userbot.forward_messages(user_id, event.message)
        print(f"Forwarded message from @{channel_username} to user {user_id}")


@userbot.on(events.NewMessage())
async def handle_message(event):
    print(event)
    sender = await event.get_sender()

    # === 1. Сообщение от пользователя (private message)
    if event.is_private:
        await process_message_from_user(event, sender)

    # === 2. Сообщение из канала
    elif event.is_channel:
       await process_message_from_channel(event, sender)


async def main():
    await userbot.connect()

    if not await userbot.is_user_authorized():
        print('Try to login with login.py. Run it.')

    print("Userbot is running.")
    await userbot.run_until_disconnected()


if __name__ == "__main__":
    asyncio.run(main())


