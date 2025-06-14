import os
import sqlite3
import time
from datetime import datetime
import schedule
from whatsapp_bot import send_message

DB_PATH = os.environ.get('JARVISS_DB', 'jarvis.db')


def check_reminders():
    now = datetime.utcnow().strftime('%Y-%m-%d %H:%M')
    with sqlite3.connect(DB_PATH) as con:
        cur = con.cursor()
        cur.execute(
            'SELECT id, mensagem FROM lembretes WHERE enviado = 0 AND data_hora <= ?',
            (now,)
        )
        rows = cur.fetchall()
        for rid, msg in rows:
            send_message(msg)
            cur.execute('UPDATE lembretes SET enviado = 1 WHERE id = ?', (rid,))
        con.commit()


def start_scheduler():
    schedule.every(1).minutes.do(check_reminders)
    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__ == '__main__':
    start_scheduler()
