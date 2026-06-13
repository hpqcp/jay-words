from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from database import get_connection
from word_forms import answer_matches, split_answers

router = APIRouter(prefix="/api/quiz", tags=["quiz"])


class SubmitAnswer(BaseModel):
    word_id: int
    answer: str


class WordFormSubmit(BaseModel):
    word_id: int
    question_type: str  # 'to_comparative', 'to_superlative', 'to_base_from_comp', 'to_base_from_super'
    answer: str


@router.post("/submit")
def submit_answer(data: SubmitAnswer):
    conn = get_connection()
    word = conn.execute("SELECT * FROM words WHERE id = ?", (data.word_id,)).fetchone()
    if not word:
        conn.close()
        return {"correct": False, "error": "Word not found"}

    correct = word["english"].strip().lower() == data.answer.strip().lower()

    if not correct:
        existing = conn.execute(
            "SELECT * FROM wrong_words WHERE word_id = ?", (data.word_id,)
        ).fetchone()
        if existing:
            conn.execute(
                "UPDATE wrong_words SET wrong_count = wrong_count + 1, last_wrong_at = CURRENT_TIMESTAMP WHERE word_id = ?",
                (data.word_id,)
            )
        else:
            conn.execute(
                "INSERT INTO wrong_words (word_id, wrong_count) VALUES (?, 1)",
                (data.word_id,)
            )
        conn.commit()

    conn.close()
    return {
        "correct": correct,
        "correct_answer": word["english"],
        "chinese": word["chinese"]
    }


@router.post("/word-form")
def submit_word_form(data: WordFormSubmit):
    conn = get_connection()
    word = conn.execute("SELECT * FROM words WHERE id = ?", (data.word_id,)).fetchone()
    if not word:
        conn.close()
        return {"correct": False, "error": "Word not found"}

    correct_answer = ""
    prompt = ""

    if data.question_type == "to_comparative":
        correct_answer = word["comparative"] or ""
        prompt = f"{word['english']} → 比较级"
    elif data.question_type == "to_superlative":
        correct_answer = word["superlative"] or ""
        prompt = f"{word['english']} → 最高级"
    elif data.question_type == "to_base_from_comp":
        correct_answer = word["english"] or ""
        prompt = f"{word['comparative']} → 原型"
    elif data.question_type == "to_base_from_super":
        correct_answer = word["english"] or ""
        prompt = f"{word['superlative']} → 原型"
    else:
        conn.close()
        raise HTTPException(400, "Invalid question_type")

    conn.close()
    correct = answer_matches(correct_answer, data.answer)
    return {
        "correct": correct,
        "correct_answer": correct_answer,
        "accepted_answers": split_answers(correct_answer),
        "prompt": prompt,
        "chinese": word["chinese"]
    }
