import sqlite3

class Database:
    def __init__(self, db):
        self.__db = db
        self.__cur = db.cursor()

    def addUser(self, login, password, role):
        try:
            self.__cur.execute("SELECT COUNT() as 'count' FROM users WHERE login=?", (login,))
            res = self.__cur.fetchone()
            if res['count'] > 0: return False
            self.__cur.execute("INSERT INTO users VALUES(NULL, ?, ?, ?, NULL)", (login, password, role))
            self.__db.commit()
            return True
        except sqlite3.Error as e:
            print("Ошибка БД (addUser) ", str(e))

    def getUserById(self, user_id):
        try:
            self.__cur.execute("SELECT * FROM users WHERE id=?", (user_id,))
            res = self.__cur.fetchone()
            if res: return res
        except sqlite3.Error as e:
            print("Ошибка БД (getUserById)", str(e))

    def getUserByLogin(self, login):
        try:
            self.__cur.execute("SELECT * FROM users WHERE login=?", (login,))
            res = self.__cur.fetchone()
            if res: return res
        except sqlite3.Error as e:
            print("Ошибка БД (getUserByLogin)", str(e))

    def getUserByVkId(self, vk_id):
        try:
            self.__cur.execute("SELECT * FROM users WHERE vk_id=?", (vk_id,))
            res = self.__cur.fetchone()
            if res: return res
        except sqlite3.Error as e:
            print("Ошибка БД (getUserByVkId)", str(e))

    def getMenu(self, category, exclude_url=()):	# exclude_url для удаления текущей страницы из списка ссылок
        try:
            self.__cur.execute(f"SELECT * FROM {category.lower()}menu")
            res = self.__cur.fetchall()
            if res:
                if exclude_url:
                    for i in range(len(res)):
                        if res[i]["url"] in exclude_url:
                            res.pop(i)
                            break
                return res
        except sqlite3.Error as e:
            print("Ошибка БД (getMenu)", str(e))

    def bindVk(self, vk_id, user_id):
        try:
            self.__cur.execute("UPDATE users SET vk_id=? WHERE id=?", (vk_id, user_id))
            self.__db.commit()
            return True
        except sqlite3.Error as e:
            print("Ошибка БД (bindVk)", str(e))

    def getSubscribers(self):
        try:
            self.__cur.execute("SELECT * FROM vk_notifications_subscribers")
            res = self.__cur.fetchall()
            if res: return res
        except sqlite3.Error as e:
            print("Ошибка БД (getSubscribers)", str(e))

    def getSubscriptionStatus(self, peer_id):
        try:
            self.__cur.execute("SELECT peer_id FROM vk_notifications_subscribers WHERE peer_id=?", (peer_id,))
            return True if self.__cur.fetchone() else False
        except sqlite3.Error as e:
            print("Ошибка БД (getSubscriptionStatus)", str(e))

    def addSubscriber(self, peer_id, name):
        try:
            if self.getSubscriptionStatus(peer_id):
                return False
            self.__cur.execute("INSERT INTO vk_notifications_subscribers VALUES(NULL, ?, ?)", (peer_id, name))
            self.__db.commit()
            return True
        except sqlite3.Error as e:
            print("Ошибка БД (addSubscriber)", str(e))

    def removeSubscriber(self, peer_id):
        try:
            if self.getSubscriptionStatus(peer_id):
                self.__cur.execute("DELETE FROM vk_notifications_subscribers WHERE peer_id=?", (peer_id,))
                self.__db.commit()
                return True
            return False
        except sqlite3.Error as e:
            print("Ошибка БД (removeSubscriber)", str(e))