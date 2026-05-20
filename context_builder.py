"""
Context builder for the Digital Li Bai chatbot.
Handles intent classification, knowledge loading, and system prompt assembly.
"""

import json
import os
import re
from typing import Optional

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
POEMS_PATH = os.path.join(BASE_DIR, "poems", "all_poems.json")
WIKI_DIR = os.path.join(BASE_DIR, "wiki")
SYSTEM_MD = os.path.join(BASE_DIR, "system.md")

# --- Data loading ---

def read_file(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def load_all_poems() -> list[dict]:
    with open(POEMS_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("poems", [])

def load_system_prompt() -> str:
    return read_file(SYSTEM_MD)

def load_wiki_file(name: str) -> str:
    return read_file(os.path.join(WIKI_DIR, name))

# --- Intent classification ---

INTENT_PATTERNS = {
    "teach_poem": [
        r"教.*诗", r"读.*诗", r"解释.*诗", r"这首诗", r"《.+》",
        r"什么意思", r"什么意思啊", r"赏析", r"讲讲.*诗", r"解读",
        r"这首诗写.*什么", r"帮.*理解", r"分析.*诗", r"这首诗.*意思",
    ],
    "discuss_poetry": [
        r"怎么.*写诗", r"作诗.*方法", r"写诗.*技巧", r"诗.*风格",
        r"什么.*体裁", r"律诗", r"绝句", r"乐府", r"古体",
        r"你的诗", r"诗歌.*特点", r"诗.*特点", r"擅长.*诗",
    ],
    "life": [
        r"人生", r"经历", r"故事", r"过去", r"一生", r"年轻",
        r"志向", r"抱负", r"理想", r"得意", r"失意", r"遗憾",
        r"后悔", r"最.*的.*事", r"什么时候", r"什么时候",
        r"哪里人", r"出生", r"老家", r"家乡", r"隐居",
        r"当官", r"做官", r"贬", r"流放", r"翰林",
        r"安史", r"永王", r"玄宗", r"皇上", r"朝廷",
    ],
    "create": [
        r"作一.*诗", r"写一.*诗", r"创作", r"即兴",
        r"模仿.*风格", r"以.*题.*诗", r"帮.*作诗", r"来一.*诗",
    ],
}

# Fallback if nothing matches — default to "chat"
DEFAULT_INTENT = "chat"


def classify_intent(user_input: str) -> str:
    text = user_input.lower()
    for intent, patterns in INTENT_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, text):
                return intent
    return DEFAULT_INTENT

# --- Poem search ---

def find_poem_by_title(title: str, poems: list[dict]) -> Optional[dict]:
    """Find a poem by approximate title match."""
    # Remove book marks
    clean = title.strip("《》")
    for poem in poems:
        p_title = poem.get("title", "").strip()
        if clean in p_title or p_title in clean:
            return poem
    return None


def find_poems_by_topic(topic: str, poems: list[dict], limit: int = 5) -> list[dict]:
    """Find poems related to a topic/keyword."""
    results = []
    for poem in poems:
        t = poem.get("title", "") + " " + " ".join(poem.get("paragraphs", []))
        if topic in t:
            results.append(poem)
        if len(results) >= limit:
            break
    return results


def get_poems_by_period(period_key: str, poems: list[dict], limit: int = 5) -> list[dict]:
    """Get poems from a specific period."""
    results = []
    for poem in poems:
        if poem.get("period") == period_key:
            results.append(poem)
        if len(results) >= limit:
            break
    return results


def extract_titles_from_input(text: str) -> list[str]:
    """Extract poem titles wrapped in 《》 from user input."""
    return re.findall(r'《(.+?)》', text)


def extract_keywords(text: str) -> list[str]:
    """Extract potential keywords for poem search."""
    # Remove common stop words and punctuation
    stops = set("的了是在我有你和就也都还不这那什么怎么为什么吗吧呢")
    words = re.findall(r'[一-鿿]{2,}', text)
    return [w for w in words if w not in stops][:5]

# --- Context assembly ---

def build_context(user_input: str, poems: list[dict]) -> str:
    """Build the knowledge context for the given user input."""
    intent = classify_intent(user_input)
    parts = []

    # Always include system prompt
    system_prompt = load_system_prompt()
    parts.append(f"<system_role>\n{system_prompt}\n</system_role>")

    # Load knowledge based on intent
    if intent == "teach_poem":
        # Extract poem titles from input
        titles = extract_titles_from_input(user_input)
        context_parts = []

        for title in titles:
            poem = find_poem_by_title(title, poems)
            if poem:
                full_text = "\n".join(poem.get("paragraphs", []))
                period_name = poem.get("period_name", "年代不详")
                form = poem.get("form", "")
                context_parts.append(
                    f"诗作《{poem['title']}》\n"
                    f"时期：{period_name}\n"
                    f"体裁：{form}\n"
                    f"全文：\n{full_text}"
                )

        if not context_parts:
            # Fallback: search by keywords
            keywords = extract_keywords(user_input)
            for kw in keywords[:3]:
                matches = find_poems_by_topic(kw, poems, limit=3)
                for m in matches:
                    full_text = "\n".join(m.get("paragraphs", []))
                    context_parts.append(
                        f"相关诗作《{m['title']}》\n"
                        f"时期：{m.get('period_name', '年代不详')}\n"
                        f"全文：\n{full_text}"
                    )

        if context_parts:
            parts.append("<poems_context>\n" + "\n\n---\n\n".join(context_parts) + "\n</poems_context>")

    elif intent == "discuss_poetry":
        # Load themes and imagery
        try:
            themes = load_wiki_file("themes.md")
            parts.append(f"<themes>\n{themes}\n</themes>")
        except Exception:
            pass
        try:
            imagery = load_wiki_file("imagery.md")
            parts.append(f"<imagery>\n{imagery}\n</imagery>")
        except Exception:
            pass

    elif intent == "life":
        # Load timeline + entity relations
        try:
            timeline = load_wiki_file("timeline.md")
            parts.append(f"<timeline>\n{timeline}\n</timeline>")
        except Exception:
            pass
        try:
            entities = load_wiki_file("entities.md")
            parts.append(f"<entities>\n{entities}\n</entities>")
        except Exception:
            pass
        # Also load poems from relevant periods
        keywords = extract_keywords(user_input)
        period_keywords = {
            "shuzhong": ["蜀中", "四川", "年轻", "少年", "峨眉", "江油"],
            "youman": ["漫游", "安陆", "金陵", "扬州", "孟浩然"],
            "changan": ["长安", "翰林", "玄宗", "供奉", "朝廷", "当官"],
            "youman2": ["杜甫", "高适", "梁宋", "东鲁", "再漫游"],
            "liufang": ["安史", "夜郎", "流放", "晚年", "永王"],
        }
        for period_kw, p_kws in period_keywords.items():
            if any(kw in user_input for kw in p_kws):
                period_poems = get_poems_by_period(period_kw, poems, limit=8)
                if period_poems:
                    poem_texts = []
                    for p in period_poems:
                        full_text = "\n".join(p.get("paragraphs", []))
                        poem_texts.append(f"《{p['title']}》\n{full_text}")
                    parts.append(
                        f"<period_poems period='{period_kw}'>\n"
                        + "\n\n".join(poem_texts)
                        + "\n</period_poems>"
                    )
                break

    elif intent == "create":
        # Load imagery for style reference
        try:
            imagery = load_wiki_file("imagery.md")
            parts.append(f"<imagery>\n{imagery}\n</imagery>")
        except Exception:
            pass
        # Load representative poems as style reference
        rep_poems = []
        for period_key in ["youman", "youman2", "changan"]:
            rep_poems.extend(get_poems_by_period(period_key, poems, limit=2))
        if rep_poems:
            poem_texts = []
            for p in rep_poems[:5]:
                full_text = "\n".join(p.get("paragraphs", []))
                poem_texts.append(f"《{p['title']}》\n{full_text}")
            parts.append(
                "<style_references>\n"
                + "\n\n".join(poem_texts)
                + "\n</style_references>"
            )

    else:  # chat
        # Load entities + imagery for general context
        try:
            entities = load_wiki_file("entities.md")
            parts.append(f"<entities>\n{entities}\n</entities>")
        except Exception:
            pass
        try:
            imagery = load_wiki_file("imagery.md")
            parts.append(f"<imagery>\n{imagery}\n</imagery>")
        except Exception:
            pass

    return "\n\n".join(parts)
