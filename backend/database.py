import pymysql
from pymysql.cursors import DictCursor
from config import DATABASE

DB_CONFIG = {
    "host": DATABASE["host"],
    "port": DATABASE["port"],
    "user": DATABASE["user"],
    "password": DATABASE["password"],
    "database": DATABASE["name"],
    "charset": "utf8mb4",
}


class ConnectionWrapper:
    """Mimics sqlite3.Connection API over pymysql for minimal code changes."""

    def __init__(self, conn):
        self.conn = conn

    def execute(self, sql, params=None):
        cur = self.conn.cursor()
        if params is None:
            cur.execute(sql)
        else:
            cur.execute(sql.replace("?", "%s"), params)
        wrapper = CursorWrapper(cur, self.conn)
        wrapper.lastrowid = cur.lastrowid
        return wrapper

    def close(self):
        self.conn.close()

    def commit(self):
        self.conn.commit()

    def cursor(self):
        return self.conn.cursor()


class CursorWrapper:
    """Wraps pymysql cursor to mimic sqlite3 cursor with dict-like rows."""

    def __init__(self, cur, conn):
        self.cur = cur
        self.conn = conn
        self.lastrowid = None

    def fetchone(self):
        row = self.cur.fetchone()
        if row is None:
            return None
        return row

    def fetchall(self):
        return self.cur.fetchall()

    def close(self):
        self.cur.close()


def get_connection():
    conn = pymysql.connect(**DB_CONFIG, cursorclass=DictCursor, autocommit=False)
    return ConnectionWrapper(conn)


def init_db():
    conn = pymysql.connect(
        host=DB_CONFIG["host"],
        port=DB_CONFIG["port"],
        user=DB_CONFIG["user"],
        password=DB_CONFIG["password"],
        charset="utf8mb4",
        autocommit=True,
    )
    with conn.cursor() as cur:
        cur.execute(f"CREATE DATABASE IF NOT EXISTS `{DB_CONFIG['database']}` DEFAULT CHARSET utf8mb4")
    conn.close()

    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS grades (
            id INT PRIMARY KEY AUTO_INCREMENT,
            name VARCHAR(255) NOT NULL,
            sort_order INT DEFAULT 0,
            is_builtin TINYINT DEFAULT 0
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS lessons (
            id INT PRIMARY KEY AUTO_INCREMENT,
            grade_id INT NOT NULL,
            name VARCHAR(255) NOT NULL,
            sort_order INT DEFAULT 0,
            FOREIGN KEY (grade_id) REFERENCES grades(id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS sections (
            id INT PRIMARY KEY AUTO_INCREMENT,
            lesson_id INT NOT NULL,
            name VARCHAR(255) NOT NULL,
            sort_order INT DEFAULT 0,
            FOREIGN KEY (lesson_id) REFERENCES lessons(id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS words (
            id INT PRIMARY KEY AUTO_INCREMENT,
            section_id INT NOT NULL,
            english VARCHAR(255) NOT NULL,
            chinese VARCHAR(255) NOT NULL,
            phonetic VARCHAR(255) DEFAULT '',
            comparative VARCHAR(255) DEFAULT '',
            superlative VARCHAR(255) DEFAULT '',
            sort_order INT DEFAULT 0,
            FOREIGN KEY (section_id) REFERENCES sections(id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS wrong_words (
            id INT PRIMARY KEY AUTO_INCREMENT,
            word_id INT NOT NULL,
            wrong_count INT DEFAULT 1,
            last_wrong_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (word_id) REFERENCES words(id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS learning_records (
            id INT PRIMARY KEY AUTO_INCREMENT,
            word_id INT NOT NULL,
            mode VARCHAR(50) NOT NULL,
            result TINYINT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (word_id) REFERENCES words(id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS articles (
            id          INT PRIMARY KEY AUTO_INCREMENT,
            title       VARCHAR(255) NOT NULL,
            content     TEXT NOT NULL,
            language    VARCHAR(10) NOT NULL DEFAULT 'en',
            created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS voice_practices (
            id              INT PRIMARY KEY AUTO_INCREMENT,
            article_id      INT NOT NULL,
            paragraph_index INT DEFAULT 0,
            sentence_index  INT DEFAULT NULL,
            mode            VARCHAR(10) DEFAULT 'full',
            level           INT DEFAULT 1,
            total_words     INT DEFAULT 0,
            correct_words   INT DEFAULT 0,
            accuracy        DECIMAL(5,2) DEFAULT 0,
            duration_ms     INT DEFAULT 0,
            created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (article_id) REFERENCES articles(id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS article_practices (
            id              INT PRIMARY KEY AUTO_INCREMENT,
            article_id      INT NOT NULL,
            paragraph_index INT DEFAULT 0,
            level           INT DEFAULT 1,
            total_blanks    INT DEFAULT 0,
            correct         INT DEFAULT 0,
            wrong           INT DEFAULT 0,
            completed       TINYINT DEFAULT 0,
            created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (article_id) REFERENCES articles(id) ON DELETE CASCADE,
            INDEX idx_article_para (article_id, paragraph_index, level)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """)
    # Add columns for existing databases (ignore if already exist)
    for col in ["comparative VARCHAR(255) DEFAULT ''", "superlative VARCHAR(255) DEFAULT ''"]:
        try:
            conn.execute(f"ALTER TABLE words ADD COLUMN {col}")
        except:
            pass
    try:
        conn.execute("ALTER TABLE voice_practices ADD COLUMN sentence_index INT DEFAULT NULL AFTER paragraph_index")
    except:
        pass
    conn.commit()
    conn.close()
