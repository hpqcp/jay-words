from fastapi import APIRouter
from pydantic import BaseModel
from database import get_connection
from datetime import date, timedelta

router = APIRouter(prefix="/api/records", tags=["records"])


class RecordCreate(BaseModel):
    word_id: int
    mode: str
    result: int


@router.post("/")
def create_record(data: RecordCreate):
    conn = get_connection()
    conn.execute(
        "INSERT INTO learning_records (word_id, mode, result) VALUES (?, ?, ?)",
        (data.word_id, data.mode, data.result)
    )
    conn.commit()
    conn.close()
    return {"ok": True}


@router.get("/stats")
def get_stats():
    conn = get_connection()
    today = date.today().isoformat()

    # Today's stats
    today_row = conn.execute(
        "SELECT COUNT(*) as cnt, COALESCE(SUM(CASE WHEN result=1 THEN 1 ELSE 0 END),0) as cor "
        "FROM learning_records WHERE date(created_at) = ?", (today,)
    ).fetchone()

    # Total stats
    total_row = conn.execute(
        "SELECT COUNT(*) as cnt, COALESCE(SUM(CASE WHEN result=1 THEN 1 ELSE 0 END),0) as cor "
        "FROM learning_records"
    ).fetchone()

    # Daily stats for last 14 days
    threshold = (date.today() - timedelta(days=13)).isoformat()
    daily_rows = conn.execute(
        "SELECT DATE(created_at) as d, COUNT(*) as cnt, "
        "COALESCE(SUM(CASE WHEN result=1 THEN 1 ELSE 0 END),0) as cor "
        "FROM learning_records WHERE DATE(created_at) >= %s "
        "GROUP BY d ORDER BY d", (threshold,)
    ).fetchall()

    # Build daily map (fill missing days with 0)
    daily_map = {}
    for r in daily_rows:
        daily_map[r["d"]] = {"count": r["cnt"], "correct": r["cor"]}
    daily_list = []
    for i in range(13, -1, -1):
        d = (date.today() - timedelta(days=i)).isoformat()
        entry = daily_map.get(d, {"count": 0, "correct": 0})
        daily_list.append({"date": d, "count": entry["count"], "correct": entry["correct"]})

    # Streak
    streak = 0
    check = date.today()
    while True:
        row = conn.execute(
            "SELECT COUNT(*) as cnt FROM learning_records WHERE date(created_at) = ?",
            (check.isoformat(),)
        ).fetchone()
        if row["cnt"] > 0:
            streak += 1
            check -= timedelta(days=1)
        else:
            break

    # Per-mode breakdown
    mode_rows = conn.execute(
        "SELECT mode, COUNT(*) as cnt, COALESCE(SUM(CASE WHEN result=1 THEN 1 ELSE 0 END),0) as cor "
        "FROM learning_records GROUP BY mode"
    ).fetchall()

    conn.close()

    return {
        "today_count": today_row["cnt"],
        "today_correct": today_row["cor"],
        "today_wrong": today_row["cnt"] - today_row["cor"],
        "total_count": total_row["cnt"],
        "total_correct": total_row["cor"],
        "total_wrong": total_row["cnt"] - total_row["cor"],
        "streak": streak,
        "daily": daily_list,
        "modes": [{"mode": r["mode"], "count": r["cnt"], "correct": r["cor"]} for r in mode_rows],
    }
