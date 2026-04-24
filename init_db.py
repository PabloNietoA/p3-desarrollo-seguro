import sqlite3
import hashlib
import os

db_dir = os.path.join(os.path.dirname(__file__), 'db')
os.makedirs(db_dir, exist_ok=True)

users_db = os.path.join(db_dir, 'users.db')
data_db = os.path.join(db_dir, 'data.db')

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Crear base de datos de usuarios
conn = sqlite3.connect(users_db)
c = conn.cursor()
c.execute("DROP TABLE IF EXISTS users")
c.execute("""CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password TEXT,
    role TEXT
)""")
users = [
    ('alice', hash_password('password1'), 'user'),
    ('bob', hash_password('password2'), 'owner'),
    ('admin', hash_password('admin123'), 'admin')
]
c.executemany("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", users)
conn.commit()
conn.close()

# Crear base de datos de empresas y comentarios
conn = sqlite3.connect(data_db)
c = conn.cursor()
c.execute("DROP TABLE IF EXISTS companies")
c.execute("DROP TABLE IF EXISTS comments")
c.execute("""CREATE TABLE companies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    owner TEXT
)""")
c.execute("""CREATE TABLE comments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id INTEGER,
    user TEXT,
    comment TEXT
)""")
# Insertar empresa de ejemplo
c.execute("INSERT INTO companies (name, owner) VALUES ('Insegura Corp', 'bob')")
conn.commit()
conn.close()

print("Bases de datos inicializadas.")
