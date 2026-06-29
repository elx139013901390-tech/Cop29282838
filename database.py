import sqlite3

DB_NAME = "lovebot.db"


def connect():
    return sqlite3.connect(DB_NAME)


def init_db():

    conn = connect()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users(
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        first_name TEXT,
        tests INTEGER DEFAULT 0,
        best_score INTEGER DEFAULT 0
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS history(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        name1 TEXT,
        age1 INTEGER,
        name2 TEXT,
        age2 INTEGER,
        love INTEGER,
        trust_score INTEGER,
        respect_score INTEGER,
        loyalty_score INTEGER,
        jealousy_score INTEGER,
        marriage_score INTEGER,
        breakup_score INTEGER,
        result TEXT
    )
    """)

    conn.commit()
    conn.close()


def add_user(user_id, username="", first_name=""):

    conn = connect()
    cur = conn.cursor()

    cur.execute("""
    INSERT OR IGNORE INTO users(
        user_id,
        username,
        first_name
    )
    VALUES(?,?,?)
    """, (
        user_id,
        username,
        first_name
    ))

    conn.commit()
    conn.close()


def save_test(
    user_id,
    name1,
    age1,
    name2,
    age2,
    love,
    trust,
    respect,
    loyalty,
    jealousy,
    marriage,
    breakup,
    result
):

    conn = connect()
    cur = conn.cursor()

    cur.execute("""
    INSERT INTO history(
        user_id,
        name1,
        age1,
        name2,
        age2,
        love,
        trust_score,
        respect_score,
        loyalty_score,
        jealousy_score,
        marriage_score,
        breakup_score,
        result
    )
    VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, (
        user_id,
        name1,
        age1,
        name2,
        age2,
        love,
        trust,
        respect,
        loyalty,
        jealousy,
        marriage,
        breakup,
        result
    ))

    cur.execute("""
    UPDATE users
    SET tests = tests + 1
    WHERE user_id = ?
    """, (user_id,))

    cur.execute("""
    UPDATE users
    SET best_score = ?
    WHERE user_id = ?
    AND best_score < ?
    """, (
        love,
        user_id,
        love
    ))

    conn.commit()
    conn.close()


def get_profile(user_id):

    conn = connect()
    cur = conn.cursor()

    cur.execute("""
    SELECT tests, best_score
    FROM users
    WHERE user_id = ?
    """, (user_id,))

    row = cur.fetchone()

    conn.close()

    return row


def get_history(user_id):

    conn = connect()
    cur = conn.cursor()

    cur.execute("""
    SELECT
    name1,
    name2,
    love,
    result
    FROM history
    WHERE user_id = ?
    ORDER BY id DESC
    """, (user_id,))

    rows = cur.fetchall()

    conn.close()

    return rows
