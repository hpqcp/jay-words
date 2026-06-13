import csv
import json
import io
from database import get_connection


def import_json(file_content: str) -> dict:
    data = json.loads(file_content)
    return _import_structure(data)


def import_csv(file_content: str) -> dict:
    reader = csv.DictReader(io.StringIO(file_content))
    # Convert flat CSV into nested structure
    grades_map = {}
    for row in reader:
        grade_name = row.get("grade", "").strip()
        lesson_name = row.get("lesson", "").strip()
        section_name = row.get("section", "").strip()
        english = row.get("english", "").strip()
        chinese = row.get("chinese", "").strip()
        phonetic = row.get("phonetic", "").strip()
        comparative = row.get("comparative", "").strip()
        superlative = row.get("superlative", "").strip()
        if not grade_name or not lesson_name or not section_name or not english or not chinese:
            continue
        if grade_name not in grades_map:
            grades_map[grade_name] = {}
        if lesson_name not in grades_map[grade_name]:
            grades_map[grade_name][lesson_name] = {}
        if section_name not in grades_map[grade_name][lesson_name]:
            grades_map[grade_name][lesson_name][section_name] = []
        grades_map[grade_name][lesson_name][section_name].append({
            "english": english,
            "chinese": chinese,
            "phonetic": phonetic,
            "comparative": comparative,
            "superlative": superlative
        })
    nested = []
    for g_name, lessons in grades_map.items():
        lesson_list = []
        for l_name, sections in lessons.items():
            section_list = []
            for s_name, words in sections.items():
                section_list.append({"section": s_name, "words": words})
            lesson_list.append({"lesson": l_name, "sections": section_list})
        nested.append({"grade": g_name, "lessons": lesson_list})
    return _import_structure(nested)


def _import_structure(data: list) -> dict:
    conn = get_connection()
    imported = {"grades": 0, "lessons": 0, "sections": 0, "words": 0}
    try:
        for g in data:
            grade_name = g.get("grade", "").strip()
            if not grade_name:
                continue
            existing = conn.execute(
                "SELECT id FROM grades WHERE name = ?", (grade_name,)
            ).fetchone()
            if existing:
                grade_id = existing["id"]
            else:
                conn.execute(
                    "INSERT INTO grades (name, sort_order, is_builtin) VALUES (?, 0, 0)",
                    (grade_name,)
                )
                grade_id = conn.execute("SELECT LAST_INSERT_ID() as id").fetchone()["id"]
                imported["grades"] += 1

            for li, l in enumerate(g.get("lessons", [])):
                lesson_name = l.get("lesson", "").strip()
                if not lesson_name:
                    continue
                existing = conn.execute(
                    "SELECT id FROM lessons WHERE grade_id = ? AND name = ?",
                    (grade_id, lesson_name)
                ).fetchone()
                if existing:
                    lesson_id = existing["id"]
                else:
                    conn.execute(
                        "INSERT INTO lessons (grade_id, name, sort_order) VALUES (?, ?, ?)",
                        (grade_id, lesson_name, li)
                    )
                    lesson_id = conn.execute("SELECT LAST_INSERT_ID() as id").fetchone()["id"]
                    imported["lessons"] += 1

                for si, s in enumerate(l.get("sections", [])):
                    section_name = s.get("section", "").strip()
                    if not section_name:
                        continue
                    existing = conn.execute(
                        "SELECT id FROM sections WHERE lesson_id = ? AND name = ?",
                        (lesson_id, section_name)
                    ).fetchone()
                    if existing:
                        section_id = existing["id"]
                    else:
                        conn.execute(
                            "INSERT INTO sections (lesson_id, name, sort_order) VALUES (?, ?, ?)",
                            (lesson_id, section_name, si)
                        )
                        section_id = conn.execute("SELECT LAST_INSERT_ID() as id").fetchone()["id"]
                        imported["sections"] += 1

                    for wi, w in enumerate(s.get("words", [])):
                        english = w.get("english", "").strip()
                        chinese = w.get("chinese", "").strip()
                        phonetic = w.get("phonetic", "").strip()
                        comparative = w.get("comparative", "").strip()
                        superlative = w.get("superlative", "").strip()
                        if not english or not chinese:
                            continue
                        existing = conn.execute(
                            "SELECT id FROM words WHERE section_id = ? AND english = ?",
                            (section_id, english)
                        ).fetchone()
                        if not existing:
                            conn.execute(
                                "INSERT INTO words (section_id, english, chinese, phonetic, comparative, superlative, sort_order) VALUES (?, ?, ?, ?, ?, ?, ?)",
                                (section_id, english, chinese, phonetic, comparative, superlative, wi)
                            )
                            imported["words"] += 1
                        elif comparative or superlative:
                            conn.execute(
                                """
                                UPDATE words
                                SET comparative = CASE WHEN comparative = '' THEN ? ELSE comparative END,
                                    superlative = CASE WHEN superlative = '' THEN ? ELSE superlative END
                                WHERE id = ?
                                """,
                                (comparative, superlative, existing["id"])
                            )
        conn.commit()
    finally:
        conn.close()
    return imported
