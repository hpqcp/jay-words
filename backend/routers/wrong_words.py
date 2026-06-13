from fastapi import APIRouter
from database import get_connection

router = APIRouter(prefix="/api/wrong", tags=["wrong_words"])


@router.get("/")
def list_wrong_words():
    conn = get_connection()
    rows = conn.execute("""
        SELECT wr.id as wrong_id, wr.wrong_count, wr.last_wrong_at,
               w.id as word_id, w.english, w.chinese, w.phonetic,
               s.id as section_id, s.name as section_name,
               l.id as lesson_id, l.name as lesson_name,
               g.id as grade_id, g.name as grade_name
        FROM wrong_words wr
        JOIN words w ON w.id = wr.word_id
        JOIN sections s ON s.id = w.section_id
        JOIN lessons l ON l.id = s.lesson_id
        JOIN grades g ON g.id = l.grade_id
        ORDER BY wr.last_wrong_at DESC
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]


@router.delete("/{wrong_id}")
def remove_wrong_word(wrong_id: int):
    conn = get_connection()
    conn.execute("DELETE FROM wrong_words WHERE id = ?", (wrong_id,))
    conn.commit()
    conn.close()
    return {"ok": True}


@router.delete("/")
def clear_wrong_words():
    conn = get_connection()
    conn.execute("DELETE FROM wrong_words")
    conn.commit()
    conn.close()
    return {"ok": True}
