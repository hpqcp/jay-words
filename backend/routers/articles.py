import re
import random
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from database import get_connection

router = APIRouter(prefix="/api", tags=["articles"])

class ArticleCreate(BaseModel):
    title: str
    content: str
    language: str = "en"

class ArticleUpdate(BaseModel):
    title: str | None = None
    content: str | None = None
    language: str | None = None

class PracticeSubmit(BaseModel):
    paragraph_index: int
    level: int
    total_blanks: int
    correct: int
    wrong: int
    completed: bool

def tokenize(text, language):
    if language == "zh":
        import jieba
        words = list(jieba.cut(text))
    else:
        words = re.findall(r'\b\w+(?:\'\w+)?\b|[^\w\s]|\s+', text)
    return words

def split_paragraphs(content):
    return [p.strip() for p in re.split(r'\n\s*\n', content) if p.strip()]

def select_hidden_indices(token_count, ratio):
    if token_count <= 1:
        return []
    ratio = max(0, min(1, ratio))
    count = max(1, int(token_count * ratio))
    if count >= token_count:
        count = token_count - 1
    indices = list(range(token_count))
    step = token_count / count if count > 0 else token_count
    selected = set()
    for i in range(count):
        idx = min(int(i * step + step / 2), token_count - 1)
        selected.add(idx)
    return sorted(selected)

@router.get("/articles")
def list_articles():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM articles ORDER BY updated_at DESC").fetchall()
    conn.close()
    result = []
    for r in rows:
        d = dict(r)
        d["paragraph_count"] = len(split_paragraphs(d["content"]))
        result.append(d)
    return result

@router.get("/articles/{article_id}")
def get_article(article_id: int):
    conn = get_connection()
    row = conn.execute("SELECT * FROM articles WHERE id = ?", (article_id,)).fetchone()
    conn.close()
    if not row:
        raise HTTPException(404, "Article not found")
    return dict(row)

@router.post("/articles")
def create_article(data: ArticleCreate):
    conn = get_connection()
    conn.execute("INSERT INTO articles (title, content, language) VALUES (?, ?, ?)",
                 (data.title, data.content, data.language))
    conn.commit()
    row = conn.execute("SELECT * FROM articles WHERE id = LAST_INSERT_ID()").fetchone()
    conn.close()
    if not row:
        raise HTTPException(500, "Failed to create article")
    return dict(row)

@router.put("/articles/{article_id}")
def update_article(article_id: int, data: ArticleUpdate):
    conn = get_connection()
    existing = conn.execute("SELECT * FROM articles WHERE id = ?", (article_id,)).fetchone()
    if not existing:
        conn.close()
        raise HTTPException(404, "Article not found")
    title = data.title if data.title is not None else existing["title"]
    content = data.content if data.content is not None else existing["content"]
    language = data.language if data.language is not None else existing["language"]
    conn.execute("UPDATE articles SET title=?, content=?, language=? WHERE id=?",
                 (title, content, language, article_id))
    conn.commit()
    row = conn.execute("SELECT * FROM articles WHERE id = ?", (article_id,)).fetchone()
    conn.close()
    return dict(row)

@router.delete("/articles/{article_id}")
def delete_article(article_id: int):
    conn = get_connection()
    conn.execute("DELETE FROM articles WHERE id = ?", (article_id,))
    conn.commit()
    conn.close()
    return {"ok": True}

@router.get("/articles/{article_id}/recite")
def get_recite_data(article_id: int, level: int = 1):
    if level < 1 or level > 5:
        raise HTTPException(400, "Level must be 1-5")
    conn = get_connection()
    article = conn.execute("SELECT * FROM articles WHERE id = ?", (article_id,)).fetchone()
    if not article:
        conn.close()
        raise HTTPException(404, "Article not found")

    paragraphs = split_paragraphs(article["content"])
    hide_ratio = level * 0.2
    result_paragraphs = []

    for pi, para_text in enumerate(paragraphs):
        tokens = tokenize(para_text, article["language"])
        if not tokens:
            continue
        word_indices = [i for i, t in enumerate(tokens) if re.match(r'\w+(?:\'\w+)?', t) and t.strip()]
        hidden_indices = select_hidden_indices(len(word_indices), hide_ratio)
        hidden_indices = [word_indices[i] for i in hidden_indices]

        progress = conn.execute(
            "SELECT level, completed FROM article_practices WHERE article_id=? AND paragraph_index=? AND level=? ORDER BY created_at DESC LIMIT 1",
            (article_id, pi, level)
        ).fetchone()

        result_paragraphs.append({
            "index": pi,
            "text": para_text,
            "tokens": tokens,
            "hidden_indices": hidden_indices,
            "progress": {
                "level": progress["level"] if progress else level,
                "completed": bool(progress["completed"]) if progress else False
            }
        })

    overall_stats = conn.execute(
        "SELECT COALESCE(SUM(total_blanks),0) as total, COALESCE(SUM(correct),0) as correct, COALESCE(SUM(wrong),0) as wrong FROM article_practices WHERE article_id=? AND level=? AND completed=1",
        (article_id, level)
    ).fetchone()
    conn.close()

    return {
        "id": article["id"],
        "title": article["title"],
        "language": article["language"],
        "content": article["content"],
        "paragraphs": result_paragraphs,
        "level": level,
        "stats": dict(overall_stats)
    }

@router.post("/articles/{article_id}/practice")
def submit_practice(article_id: int, data: PracticeSubmit):
    conn = get_connection()
    conn.execute(
        "INSERT INTO article_practices (article_id, paragraph_index, level, total_blanks, correct, wrong, completed) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (article_id, data.paragraph_index, data.level, data.total_blanks, data.correct, data.wrong, 1 if data.completed else 0)
    )
    conn.commit()
    row = conn.execute("SELECT * FROM article_practices WHERE id = LAST_INSERT_ID()").fetchone()
    conn.close()
    if not row:
        raise HTTPException(500, "Failed to record practice")
    return dict(row)

@router.get("/articles/{article_id}/progress")
def get_article_progress(article_id: int):
    conn = get_connection()
    rows = conn.execute(
        "SELECT paragraph_index, level, MAX(completed) as completed FROM article_practices WHERE article_id=? GROUP BY paragraph_index, level",
        (article_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


class VoicePracticeSubmit(BaseModel):
    paragraph_index: int
    mode: str = "full"
    level: int = 1
    total_words: int = 0
    correct_words: int = 0
    accuracy: float = 0
    duration_ms: int = 0


@router.post("/articles/{article_id}/voice-practice")
def submit_voice_practice(article_id: int, data: VoicePracticeSubmit):
    conn = get_connection()
    conn.execute(
        "INSERT INTO voice_practices (article_id, paragraph_index, mode, level, total_words, correct_words, accuracy, duration_ms) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (article_id, data.paragraph_index, data.mode, data.level, data.total_words, data.correct_words, data.accuracy, data.duration_ms)
    )
    conn.commit()
    row = conn.execute("SELECT * FROM voice_practices WHERE id = LAST_INSERT_ID()").fetchone()
    conn.close()
    if not row:
        raise HTTPException(500, "Failed to record voice practice")
    return dict(row)


@router.get("/articles/{article_id}/voice-progress")
def get_voice_progress(article_id: int):
    conn = get_connection()
    rows = conn.execute(
        "SELECT paragraph_index, mode, level, MAX(accuracy) as accuracy, COUNT(*) as attempts FROM voice_practices WHERE article_id=? GROUP BY paragraph_index, mode, level",
        (article_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]
