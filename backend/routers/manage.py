from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
from database import get_connection
from vocab_loader import import_json, import_csv
from word_forms import generate_adjective_forms

router = APIRouter(prefix="/api", tags=["manage"])


class GradeCreate(BaseModel):
    name: str


class LessonCreate(BaseModel):
    name: str


class SectionCreate(BaseModel):
    name: str


class WordCreate(BaseModel):
    english: str
    chinese: str
    phonetic: str = ""
    comparative: str = ""
    superlative: str = ""


class WordEdit(BaseModel):
    english: str
    chinese: str
    phonetic: str = ""
    comparative: str = ""
    superlative: str = ""


class Rename(BaseModel):
    name: str


# --- Grades ---

@router.get("/grades")
def list_grades():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM grades ORDER BY sort_order").fetchall()
    conn.close()
    return [dict(r) for r in rows]


@router.post("/grades")
def create_grade(data: GradeCreate):
    conn = get_connection()
    max_order = conn.execute("SELECT COALESCE(MAX(sort_order), -1) as val FROM grades").fetchone()["val"]
    conn.execute("INSERT INTO grades (name, sort_order) VALUES (?, ?)", (data.name, max_order + 1))
    conn.commit()
    row = conn.execute("SELECT * FROM grades WHERE id = LAST_INSERT_ID()").fetchone()
    conn.close()
    if not row:
        raise HTTPException(500, "Failed to create grade")
    return dict(row)


@router.put("/grades/{grade_id}")
def rename_grade(grade_id: int, data: Rename):
    conn = get_connection()
    conn.execute("UPDATE grades SET name = ? WHERE id = ?", (data.name, grade_id))
    conn.commit()
    row = conn.execute("SELECT * FROM grades WHERE id = ?", (grade_id,)).fetchone()
    conn.close()
    if not row:
        raise HTTPException(404, "Grade not found")
    return dict(row)


@router.delete("/grades/{grade_id}")
def delete_grade(grade_id: int):
    conn = get_connection()
    conn.execute("DELETE FROM grades WHERE id = ?", (grade_id,))
    conn.commit()
    conn.close()
    return {"ok": True}


# --- Lessons ---

@router.get("/grades/{grade_id}/lessons")
def list_lessons(grade_id: int):
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM lessons WHERE grade_id = ? ORDER BY sort_order", (grade_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


@router.post("/grades/{grade_id}/lessons")
def create_lesson(grade_id: int, data: LessonCreate):
    conn = get_connection()
    max_order = conn.execute(
        "SELECT COALESCE(MAX(sort_order), -1) as val FROM lessons WHERE grade_id = ?", (grade_id,)
    ).fetchone()["val"]
    conn.execute("INSERT INTO lessons (grade_id, name, sort_order) VALUES (?, ?, ?)",
                 (grade_id, data.name, max_order + 1))
    conn.commit()
    row = conn.execute("SELECT * FROM lessons WHERE id = LAST_INSERT_ID()").fetchone()
    conn.close()
    if not row:
        raise HTTPException(500, "Failed to create lesson")
    return dict(row)


@router.put("/lessons/{lesson_id}")
def rename_lesson(lesson_id: int, data: Rename):
    conn = get_connection()
    conn.execute("UPDATE lessons SET name = ? WHERE id = ?", (data.name, lesson_id))
    conn.commit()
    row = conn.execute("SELECT * FROM lessons WHERE id = ?", (lesson_id,)).fetchone()
    conn.close()
    if not row:
        raise HTTPException(404, "Lesson not found")
    return dict(row)


@router.delete("/lessons/{lesson_id}")
def delete_lesson(lesson_id: int):
    conn = get_connection()
    conn.execute("DELETE FROM lessons WHERE id = ?", (lesson_id,))
    conn.commit()
    conn.close()
    return {"ok": True}


# --- Sections ---

@router.get("/lessons/{lesson_id}/sections")
def list_sections(lesson_id: int):
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM sections WHERE lesson_id = ? ORDER BY sort_order", (lesson_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


@router.post("/lessons/{lesson_id}/sections")
def create_section(lesson_id: int, data: SectionCreate):
    conn = get_connection()
    max_order = conn.execute(
        "SELECT COALESCE(MAX(sort_order), -1) as val FROM sections WHERE lesson_id = ?", (lesson_id,)
    ).fetchone()["val"]
    conn.execute("INSERT INTO sections (lesson_id, name, sort_order) VALUES (?, ?, ?)",
                 (lesson_id, data.name, max_order + 1))
    conn.commit()
    row = conn.execute("SELECT * FROM sections WHERE id = LAST_INSERT_ID()").fetchone()
    conn.close()
    if not row:
        raise HTTPException(500, "Failed to create section")
    return dict(row)


@router.put("/sections/{section_id}")
def rename_section(section_id: int, data: Rename):
    conn = get_connection()
    conn.execute("UPDATE sections SET name = ? WHERE id = ?", (data.name, section_id))
    conn.commit()
    row = conn.execute("SELECT * FROM sections WHERE id = ?", (section_id,)).fetchone()
    conn.close()
    if not row:
        raise HTTPException(404, "Section not found")
    return dict(row)


@router.delete("/sections/{section_id}")
def delete_section(section_id: int):
    conn = get_connection()
    conn.execute("DELETE FROM sections WHERE id = ?", (section_id,))
    conn.commit()
    conn.close()
    return {"ok": True}


# --- Words ---

@router.get("/sections/{section_id}/words")
def list_words(section_id: int):
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM words WHERE section_id = ? ORDER BY sort_order", (section_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


@router.post("/sections/{section_id}/words")
def create_word(section_id: int, data: WordCreate):
    conn = get_connection()
    max_order = conn.execute(
        "SELECT COALESCE(MAX(sort_order), -1) as val FROM words WHERE section_id = ?", (section_id,)
    ).fetchone()["val"]
    conn.execute("INSERT INTO words (section_id, english, chinese, phonetic, comparative, superlative, sort_order) VALUES (?, ?, ?, ?, ?, ?, ?)",
                 (section_id, data.english, data.chinese, data.phonetic, data.comparative, data.superlative, max_order + 1))
    conn.commit()
    row = conn.execute("SELECT * FROM words WHERE id = LAST_INSERT_ID()").fetchone()
    conn.close()
    if not row:
        raise HTTPException(500, "Failed to create word")
    return dict(row)


@router.get("/words/{word_id}")
def get_word(word_id: int):
    conn = get_connection()
    row = conn.execute(
        "SELECT w.*, COALESCE(wr.wrong_count, 0) as wrong_count FROM words w LEFT JOIN wrong_words wr ON wr.word_id = w.id WHERE w.id = ?",
        (word_id,)
    ).fetchone()
    conn.close()
    if not row:
        return {"error": "not found"}
    return dict(row)


@router.put("/words/{word_id}")
def edit_word(word_id: int, data: WordEdit):
    conn = get_connection()
    conn.execute(
        "UPDATE words SET english = ?, chinese = ?, phonetic = ?, comparative = ?, superlative = ? WHERE id = ?",
        (data.english, data.chinese, data.phonetic, data.comparative, data.superlative, word_id)
    )
    conn.commit()
    row = conn.execute("SELECT * FROM words WHERE id = ?", (word_id,)).fetchone()
    conn.close()
    if not row:
        raise HTTPException(404, "Word not found")
    return dict(row)


@router.delete("/words/{word_id}")
def delete_word(word_id: int):
    conn = get_connection()
    conn.execute("DELETE FROM words WHERE id = ?", (word_id,))
    conn.commit()
    conn.close()
    return {"ok": True}


# --- Word Lookup ---

@router.get("/lookup")
def lookup_word(word: str):
    import urllib.request, urllib.parse, json
    result = {"english": word, "chinese": "", "phonetic": "", "comparative": "", "superlative": ""}

    # Get Chinese translation
    try:
        url = f"https://api.mymemory.translated.net/get?q={urllib.parse.quote(word)}&langpair=en|zh-CN"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read())
            if data.get("responseStatus") == 200:
                t = data.get("responseData", {}).get("translatedText", "")
                if t:
                    result["chinese"] = t
    except Exception:
        pass

    # Get phonetic
    try:
        url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{urllib.parse.quote(word)}"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read())
            if data and len(data) > 0:
                entry = data[0]
                if entry.get("phonetic"):
                    result["phonetic"] = entry["phonetic"]
                elif entry.get("phonetics"):
                    for p in entry["phonetics"]:
                        if p.get("text"):
                            result["phonetic"] = p["text"]
                            break
    except Exception:
        pass

    forms = generate_adjective_forms(word)
    result["comparative"] = forms["comparative"]
    result["superlative"] = forms["superlative"]
    result["word_form_source"] = forms["source"]

    return result


# --- Import / Export ---

@router.post("/import")
async def import_file(file: UploadFile = File(...)):
    content = await file.read()
    text = content.decode("utf-8")
    if file.filename.endswith(".csv"):
        result = import_csv(text)
    else:
        result = import_json(text)
    return result


@router.get("/export")
def export_vocab(grade_id: int = None):
    conn = get_connection()
    if grade_id:
        grades = conn.execute("SELECT * FROM grades WHERE id = ?", (grade_id,)).fetchall()
    else:
        grades = conn.execute("SELECT * FROM grades ORDER BY sort_order").fetchall()
    result = []
    for g in grades:
        grade = {"grade": g["name"], "lessons": []}
        lessons = conn.execute(
            "SELECT * FROM lessons WHERE grade_id = ? ORDER BY sort_order", (g["id"],)
        ).fetchall()
        for l in lessons:
            lesson = {"lesson": l["name"], "sections": []}
            sections = conn.execute(
                "SELECT * FROM sections WHERE lesson_id = ? ORDER BY sort_order", (l["id"],)
            ).fetchall()
            for s in sections:
                section = {"section": s["name"], "words": []}
                words = conn.execute(
                    "SELECT english, chinese, phonetic, comparative, superlative FROM words WHERE section_id = ? ORDER BY sort_order",
                    (s["id"],)
                ).fetchall()
                section["words"] = [dict(w) for w in words]
                lesson["sections"].append(section)
            grade["lessons"].append(lesson)
        result.append(grade)
    conn.close()
    return result
