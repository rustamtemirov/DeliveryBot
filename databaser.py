import sqlite3
from config import db_name as database


class Databaser:

    def __init__(self):
        self.conn = sqlite3.connect(database, check_same_thread=False)
        self.cursor = self.conn.cursor()

    def com(self):
        self.cursor.close()
        self.conn.commit()

    def try_add_user(self, uid, lang):
        self.cursor.execute('UPDATE users SET lang=? WHERE user_id=?', (lang, uid))
        if self.cursor.rowcount == 0:
            self.cursor.execute('INSERT OR IGNORE INTO users (user_id, status, lang) VALUES (?, 0, ?)', (uid, lang))
        self.conn.commit()

    def set_state(self, uid, state):
        self.cursor.execute('UPDATE users SET status = ? WHERE user_id = ?', (state, uid))
        self.conn.commit()

    def get_state(self, uid):
        self.cursor.execute('SELECT status FROM users WHERE user_id = ?', (uid,))
        try:
            return self.cursor.fetchall()[0][0]
        except Exception:
            return '0'

    def set_addr(self, uid, addr):
        self.cursor.execute('UPDATE users SET addr=?, provided=? WHERE user_id = ?', (addr, 'addr', uid))
        self.conn.commit()

    def set_loc(self, uid, lat, lon):
        self.cursor.execute('UPDATE users SET lat=?, lon=?, provided="loc" WHERE user_id = ?', (lat, lon, uid))
        self.conn.commit()

    def set_phone(self, uid, phone):
        self.cursor.execute('UPDATE users SET phone = ? WHERE user_id = ?', (phone, uid))
        self.conn.commit()

    def get_phone(self, uid):
        self.cursor.execute('SELECT phone FROM users WHERE user_id = ?', (uid,))
        return self.cursor.fetchall()[0][0]

    def what_is_provided(self, uid):
        self.cursor.execute('SELECT provided FROM users WHERE user_id = ?', (uid,))
        return self.cursor.fetchall()[0][0]

    def get_addr(self, uid):
        self.cursor.execute('SELECT addr FROM users WHERE user_id = ?', (uid,))
        return self.cursor.fetchall()[0][0]

    def get_loc(self, uid):
        self.cursor.execute('SELECT lat, lon FROM users WHERE user_id = ?', (uid,))
        return self.cursor.fetchall()[0]

    def check_cat(self, cat_id):
        self.cursor.execute('SELECT * FROM groups WHERE id = ?', (cat_id,))
        data = self.cursor.fetchall()
        return True if len(data) > 0 or int(cat_id) == 0 else False

    def check_item(self, item_id):
        self.cursor.execute('SELECT * FROM items WHERE id = ?', (item_id,))
        data = self.cursor.fetchall()
        return True if len(data) > 0 else False

    def get_parent(self, cat_id):
        self.cursor.execute('SELECT parent FROM groups WHERE id = ?', (cat_id,))
        return self.cursor.fetchall()

    def get_categories(self, cat_id):
        self.cursor.execute('SELECT id, name FROM groups WHERE parent = ?', (cat_id,))
        data = self.cursor.fetchall()
        return data

    def get_items(self, cat_id):
        self.cursor.execute('SELECT id, title FROM items WHERE category = ?', (cat_id,))
        data = self.cursor.fetchall()
        return data

    def add_cat(self, parent, name):
        self.cursor.execute('INSERT INTO groups (name, parent) VALUES (?, ?)', (name, parent))
        self.conn.commit()

    def del_cat(self, cat_id):
        try:
            parent = self.get_parent(cat_id)[0][0]
        except IndexError:
            return
        self.cursor.execute('DELETE FROM groups WHERE id = ?', (cat_id,))
        self.conn.commit()
        return parent

    def del_item(self, item_id):
        self.cursor.execute('DELETE FROM items WHERE id = ?', (item_id,))
        self.conn.commit()

    def create_item(self, parent, uid):
        self.cursor.execute('INSERT INTO items (title, desc, photo, category, by_id, price) VALUES ("nf", "nf", "nf", ?, ?, "nf")',
                            (parent, uid))
        self.conn.commit()

    def set_title(self, title, uid):
        self.cursor.execute('UPDATE items SET title = ? WHERE title = "nf" AND by_id = ?', (title, uid))
        self.conn.commit()

    def set_desc(self, desc, uid):
        self.cursor.execute('UPDATE items SET desc = ? WHERE desc = "nf" AND by_id = ?', (desc, uid))
        self.conn.commit()

    def set_price(self, price, uid):
        self.cursor.execute('UPDATE items SET price = ? WHERE price = "nf" AND by_id = ?', (price, uid))
        self.conn.commit()

    def set_photo(self, photo, uid):
        item_id = self.cursor.execute('SELECT id FROM items WHERE photo = "nf" AND by_id = ?', (uid,)).fetchall()[0][0]
        self.cursor.execute('UPDATE items SET photo = ? WHERE id = ?', (photo, item_id))
        self.conn.commit()
        return item_id

    def get_item_by_id(self, item_id):
        self.cursor.execute('SELECT * FROM items WHERE id = ?', (item_id,))
        return self.cursor.fetchall()

    def cancel_item(self, uid):
        self.cursor.execute('DELETE FROM items WHERE by_id = ? AND photo = "nf"', (uid,))
        self.conn.commit()

    def add_to_cart(self, uid, iid):
        try:
            price = self.get_item_by_id(iid)[0][6]
            self.cursor.execute('INSERT INTO cart (user_id, item_id, price) VALUES (?, ?, ?)', (uid, iid, price))
            self.conn.commit()
        except IndexError:
            return

    def del_from_cart(self, uid, iid):
        self.cursor.execute('DELETE FROM cart WHERE user_id = ? AND item_id = ?', (uid, iid))
        self.conn.commit()

    def get_user_cart(self, uid):
        self.cursor.execute('SELECT SUM(price) FROM cart WHERE user_id = ?', (uid,))
        price = self.cursor.fetchall()[0]
        self.cursor.execute('SELECT * FROM cart WHERE user_id = ?', (uid,))
        items = self.cursor.fetchall()
        return price, items

    def clear_cart(self, uid):
        self.cursor.execute('DELETE FROM cart WHERE user_id=?', (uid,))
        self.conn.commit()

    def set_order(self, uid, order):
        self.cursor.execute('UPDATE users SET ot = ? WHERE user_id = ?', (order, uid))
        self.conn.commit()

    def get_order(self, uid):
        self.cursor.execute('SELECT ot FROM users WHERE user_id = ?', (uid,))
        return self.cursor.fetchall()[0][0]

    def get_users_list(self):
        self.cursor.execute('SELECT user_id FROM users')
        return self.cursor.fetchall()

    def add_media(self, content_type, text=None, file_id=None, lon=None, lat=None):
        self.cursor.execute('INSERT INTO announce VALUES (?, ?, ?, ?, ?)', (content_type, text, file_id, lon, lat))
        self.conn.commit()

    def get_media(self):
        self.cursor.execute('SELECT * FROM announce')
        return self.cursor.fetchall()

    def clear_media(self):
        self.cursor.execute('DELETE FROM announce')
        self.conn.commit()

    def get_user_lang(self, uid):
        self.cursor.execute('SELECT lang FROM users WHERE user_id=?', (uid,))
        return self.cursor.fetchall()

    def update_last(self, uid, time):
        self.cursor.execute('UPDATE users SET last=? WHERE user_id=?', (time, uid))
        self.conn.commit()

    def get_active(self, time):
        self.cursor.execute('select lang, count(*) from users group by lang;')
        total = self.cursor.fetchall()
        self.cursor.execute('select lang, count(*) from users where last > ? - 172800 group by lang;', (time,))
        active = self.cursor.fetchall()
        ans = {}
        for r in total:
            ans[r[0]] = [r[1]]
        for r in active:
            ans[r[0]].append(r[1])
        return ans
