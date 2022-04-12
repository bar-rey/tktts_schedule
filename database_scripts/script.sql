CREATE TABLE IF NOT EXISTS defaultmenu (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    url TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS guestmenu (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    url TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS moderatormenu (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    url TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS administratormenu (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    url TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    login TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('user', 'moderator', 'administrator')),
    vk_id INTEGER UNIQUE
);
CREATE TABLE IF NOT EXISTS vk_notifications_subscribers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    peer_id INTEGER NOT NULL UNIQUE,
    name TEXT NOT NULL
);
INSERT OR REPLACE INTO "main"."administratormenu" ("id", "title", "url") VALUES ('1', 'Расписание', '/schedule/show/');
INSERT OR REPLACE INTO "main"."administratormenu" ("id", "title", "url") VALUES ('2', 'Добавление', '/schedule/add/');
INSERT OR REPLACE INTO "main"."administratormenu" ("id", "title", "url") VALUES ('3', 'Рассылка', '/vk/notify/');
INSERT OR REPLACE INTO "main"."administratormenu" ("id", "title", "url") VALUES ('4', 'Привязка ВК', '/vk/bind/');
INSERT OR REPLACE INTO "main"."administratormenu" ("id", "title", "url") VALUES ('5', 'Регистрация', '/register/');
INSERT OR REPLACE INTO "main"."administratormenu" ("id", "title", "url") VALUES ('6', 'Выход', '/logout/');
INSERT OR REPLACE INTO "main"."defaultmenu" ("id", "title", "url") VALUES ('1', 'Расписание', '/schedule/show/');
INSERT OR REPLACE INTO "main"."defaultmenu" ("id", "title", "url") VALUES ('2', 'Вход', '/login/');
INSERT OR REPLACE INTO "main"."guestmenu" ("id", "title", "url") VALUES ('1', 'Расписание', '/schedule/show/');
INSERT OR REPLACE INTO "main"."guestmenu" ("id", "title", "url") VALUES ('2', 'Выход', '/logout/');
INSERT OR REPLACE INTO "main"."moderatormenu" ("id", "title", "url") VALUES ('1', 'Расписание', '/schedule/show/');
INSERT OR REPLACE INTO "main"."moderatormenu" ("id", "title", "url") VALUES ('2', 'Добавление', '/schedule/add/');
INSERT OR REPLACE INTO "main"."moderatormenu" ("id", "title", "url") VALUES ('3', 'Рассылка', '/vk/notify/');
INSERT OR REPLACE INTO "main"."moderatormenu" ("id", "title", "url") VALUES ('4', 'Привязка ВК', '/vk/bind/');
INSERT OR REPLACE INTO "main"."moderatormenu" ("id", "title", "url") VALUES ('5', 'Выход', '/logout/');