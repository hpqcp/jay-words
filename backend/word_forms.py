import re


ANSWER_SPLIT_RE = re.compile(r"[,/;|，、；]+")
VOWELS = set("aeiou")

IRREGULAR_ADJECTIVE_FORMS = {
    "good": ("better", "best"),
    "well": ("better", "best"),
    "bad": ("worse", "worst"),
    "ill": ("worse", "worst"),
    "far": ("farther/further", "farthest/furthest"),
    "little": ("less", "least"),
    "many": ("more", "most"),
    "much": ("more", "most"),
    "old": ("older/elder", "oldest/eldest"),
}


def normalize_answer(value: str) -> str:
    value = (value or "").strip().lower()
    value = re.sub(r"\s+", " ", value)
    if value.startswith("the "):
        value = value[4:].strip()
    return value


def split_answers(value: str) -> list[str]:
    answers = []
    for part in ANSWER_SPLIT_RE.split(value or ""):
        normalized = normalize_answer(part)
        if normalized and normalized not in answers:
            answers.append(normalized)
    return answers


def answer_matches(correct_answer: str, user_answer: str) -> bool:
    expected = split_answers(correct_answer)
    return bool(expected) and normalize_answer(user_answer) in expected


def is_consonant(char: str) -> bool:
    return char.isalpha() and char not in VOWELS


def looks_like_cvc(word: str) -> bool:
    if len(word) < 3:
        return False
    a, b, c = word[-3], word[-2], word[-1]
    return (
        is_consonant(a)
        and b in VOWELS
        and is_consonant(c)
        and c not in {"w", "x", "y"}
    )


def generate_adjective_forms(word: str) -> dict:
    base = normalize_answer(word)
    if not base or not re.fullmatch(r"[a-z]+", base):
        return {"comparative": "", "superlative": "", "source": "unsupported"}

    if base in IRREGULAR_ADJECTIVE_FORMS:
        comparative, superlative = IRREGULAR_ADJECTIVE_FORMS[base]
        return {
            "comparative": comparative,
            "superlative": superlative,
            "source": "irregular",
        }

    if base.endswith("y") and len(base) > 1 and is_consonant(base[-2]):
        stem = base[:-1]
        comparative = f"{stem}ier"
        superlative = f"{stem}iest"
    elif base.endswith("e"):
        comparative = f"{base}r"
        superlative = f"{base}st"
    elif looks_like_cvc(base):
        comparative = f"{base}{base[-1]}er"
        superlative = f"{base}{base[-1]}est"
    else:
        comparative = f"{base}er"
        superlative = f"{base}est"

    return {
        "comparative": comparative,
        "superlative": superlative,
        "source": "rule",
    }
