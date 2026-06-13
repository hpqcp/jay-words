from fastapi import APIRouter
from database import get_connection

router = APIRouter(prefix="/api", tags=["vocab"])


@router.get("/vocab/tree")
def vocab_tree():
    conn = get_connection()
    grades = conn.execute("SELECT * FROM grades ORDER BY sort_order").fetchall()
    result = []
    for g in grades:
        grade = {"id": g["id"], "name": g["name"], "lessons": []}
        lessons = conn.execute(
            "SELECT * FROM lessons WHERE grade_id = ? ORDER BY sort_order", (g["id"],)
        ).fetchall()
        for l in lessons:
            lesson = {"id": l["id"], "name": l["name"], "sections": []}
            sections = conn.execute(
                "SELECT * FROM sections WHERE lesson_id = ? ORDER BY sort_order", (l["id"],)
            ).fetchall()
            for s in sections:
                word_count = conn.execute(
                    "SELECT COUNT(*) as cnt FROM words WHERE section_id = ?", (s["id"],)
                ).fetchone()["cnt"]
                lesson["sections"].append({
                    "id": s["id"],
                    "name": s["name"],
                    "word_count": word_count
                })
            grade["lessons"].append(lesson)
        result.append(grade)
    conn.close()
    return result


@router.get("/sections/{section_id}/words")
def get_section_words(section_id: int):
    conn = get_connection()
    rows = conn.execute(
        """SELECT w.*,
           COALESCE(wr.wrong_count, 0) as wrong_count
           FROM words w
           LEFT JOIN wrong_words wr ON wr.word_id = w.id
           WHERE w.section_id = ?
           ORDER BY w.sort_order""",
        (section_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

