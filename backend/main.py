import os, time
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from database import init_db, get_connection
from vocab_data import BUILTIN_VOCAB
from vocab_loader import _import_structure
from routers import manage, vocab, quiz, wrong_words, records, articles
from version import VERSION

app = FastAPI(title="小杰背单词")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(manage.router)
app.include_router(vocab.router)
app.include_router(quiz.router)
app.include_router(wrong_words.router)
app.include_router(records.router)
app.include_router(articles.router)

# Serve built frontend (used in Docker/production)
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.isdir(static_dir):
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")


@app.on_event("startup")
def startup():
    for attempt in range(30):
        try:
            init_db()
            break
        except Exception as e:
            if attempt == 29:
                raise
            print(f"Waiting for MySQL ({attempt+1}/30)...")
            time.sleep(2)
    conn = get_connection()
    has_data = conn.execute("SELECT COUNT(*) as cnt FROM grades").fetchone()["cnt"]
    conn.close()
    if has_data == 0:
        _import_structure(BUILTIN_VOCAB)
        conn = get_connection()
        conn.execute("UPDATE grades SET is_builtin = 1")
        conn.commit()
        conn.close()


@app.get("/api/health")
def health():
    return {"status": "ok", "version": VERSION}


@app.get("/api/version")
def get_version():
    return {"version": VERSION}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=18001)
