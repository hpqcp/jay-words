import os

DATABASE = {
    "host": os.getenv("DB_HOST", "192.168.1.2"),
    "port": int(os.getenv("DB_PORT", "3306")),
    "user": os.getenv("DB_USER", "jay"),
    "password": os.getenv("DB_PASSWORD", "jay@20171104"),
    "name": os.getenv("DB_NAME", "jay_words"),
}
