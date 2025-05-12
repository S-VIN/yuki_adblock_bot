import sqlite3

conn = sqlite3.connect("db/subscriptions.db")
cursor = conn.cursor()
cursor.execute("""
    CREATE TABLE IF NOT EXISTS subscriptions (
        user_id INTEGER NOT NULL,
        channel_id INTEGER NOT NULL
    );""")
cursor.execute("""
    CREATE TABLE IF NOT EXISTS instructions_was_sent (
        user_id INTEGER PRIMARY KEY NOT NULL UNIQUE
    );
""")
cursor.execute("""
    CREATE TABLE IF NOT EXISTS filter_words
    (
        user_id INTEGER NOT NULL,
        filter TEXT
    );
""")
conn.commit()

# instructions_was_sent
def is_instructions_was_sent(user_id):
    cursor.execute("SELECT user_id FROM instructions_was_sent WHERE user_id=?", (user_id,))
    rows = cursor.fetchall()
    return len(rows) != 0

def register_sending_instructions(user_id):
    cursor.execute("INSERT INTO instructions_was_sent VALUES (?)", (user_id,))
    conn.commit()


# subscriptions
def add_subscription(user_id, channel):
    cursor.execute("SELECT 1 FROM subscriptions WHERE user_id=? AND channel_id=?", (user_id, channel,))
    if not cursor.fetchone():
        cursor.execute("INSERT INTO subscriptions (user_id, channel_id) VALUES (?, ?)", (user_id, channel,))
        conn.commit()

def delete_subscription(user_id, channel):
    cursor.execute("SELECT 1 FROM subscriptions WHERE user_id=? AND channel_id=?", (user_id, channel,))
    if cursor.fetchone():
        cursor.execute("DELETE FROM subscriptions WHERE user_id=? AND channel_id=?", (user_id, channel,))
        conn.commit()
        return True
    return False

def get_subscribers(channel):
    cursor.execute("SELECT user_id FROM subscriptions WHERE channel_id=?", (channel,))
    return [row[0] for row in cursor.fetchall()]

def get_all_channels_for_user(user_id):
    cursor.execute("SELECT DISTINCT channel_id FROM subscriptions WHERE user_id=?", (user_id,))
    return [row[0] for row in cursor.fetchall()]


# filter_words
def set_filters(user_id, filters):
    cursor.execute("DELETE FROM filter_words WHERE user_id=?", (user_id,))
    for word in filters:
        cursor.execute("INSERT INTO filter_words (user_id, filter) VALUES (?, ?)", (user_id, word,))
    conn.commit()

def get_filters(user_id):
    cursor.execute("SELECT DISTINCT filter FROM filter_words WHERE user_id=?", (user_id,))
    return [row[0] for row in cursor.fetchall()]