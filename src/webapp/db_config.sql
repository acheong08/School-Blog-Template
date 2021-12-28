DROP TABLE IF EXISTS admin_accounts;
CREATE TABLE admin_accounts (
  user_id INTEGER UNIQUE PRIMARY KEY AUTOINCREMENT NOT NULL,
  username TEXT UNIQUE NOT NULL,
  password_hash TEXT NOT NULL,
  department TEXT NOT NULL
);
DROP TABLE IF EXISTS client_accounts;
CREATE TABLE client_accounts (
  user_id INTEGER UNIQUE PRIMARY KEY AUTOINCREMENT NOT NULL,
  email TEXT UNIQUE NOT NULL,
  username TEXT UNIQUE NOT NULL,
  password_hash TEXT NOT NULL
);
DROP TABLE IF EXISTS posts;
CREATE TABLE posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    created DATETIME DEFAULT (DATETIME(CURRENT_TIMESTAMP, 'LOCALTIME')),
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    preview TEXT,
    content TEXT NOT NULL,
    department TEXT NOT NULL
);