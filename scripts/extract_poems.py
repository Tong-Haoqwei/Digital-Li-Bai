#!/usr/bin/env python3
"""
Extract Li Bai's poems from chinese-poetry/chinese-poetry repository.
Filter for poems with clear dating, deduplicate against existing skeleton.
Output: poems/all_poems.json
"""

import json
import re
import os
import sys
import time
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# BASE_DIR = libai/ directory (parent of scripts/)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POEMS_DIR = os.path.join(BASE_DIR, "poems")
WIKI_DIR = os.path.join(BASE_DIR, "wiki")
OUTPUT = os.path.join(POEMS_DIR, "all_poems.json")
UNDATED_OUTPUT = os.path.join(POEMS_DIR, "undated.json")

REPO_RAW = "https://raw.githubusercontent.com/chinese-poetry/chinese-poetry/master/%E5%85%A8%E5%94%90%E8%AF%97"

# Session with retry and no SSL verify
session = requests.Session()
retry = Retry(total=3, backoff_factor=3, status_forcelist=[429, 500, 502, 503, 504])
adapter = HTTPAdapter(max_retries=retry)
session.mount("https://", adapter)
session.mount("http://", adapter)
# Disable SSL verification for environments without proper CA certs
session.verify = False
# Suppress InsecureRequestWarning
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def load_existing_titles():
    """Scan all .md files in poems/ and wiki/ for known poem titles."""
    titles = set()
    for md_dir in [POEMS_DIR, WIKI_DIR]:
        if not os.path.exists(md_dir):
            continue
        for fname in os.listdir(md_dir):
            if not fname.endswith(".md"):
                continue
            fpath = os.path.join(md_dir, fname)
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    content = f.read()
            except Exception:
                continue
            for match in re.finditer(r'《([^》]+)》', content):
                title = match.group(1).strip()
                if title and len(title) > 1:
                    titles.add(title)
    return titles


def normalize_title(title):
    """Normalize a poem title for comparison."""
    title = title.strip()
    title = re.sub(r'[·（）\(\)].*$', '', title)
    return title


def is_duplicate(title, existing_titles):
    """Check if a poem title already exists in our skeleton."""
    normalized = normalize_title(title)
    for existing in existing_titles:
        if normalize_title(existing) == normalized:
            return True
        if len(normalized) > 4 and len(existing) > 4:
            if normalized in existing or existing in normalized:
                return True
    return False


# Period classification based on poem title keywords
# NOTE: Data uses traditional characters, so we include both 简/繁 variants
PERIOD_RULES = {
    "shuzhong": [
        # Simplified + Traditional
        "峨眉", "峨嵋", "戴天山", "锦城", "錦城", "成都", "蜀", "渝州", "江油",
        "上李邕", "初月", "咏萤", "詠螢", "访戴天山", "訪戴天山", "登锦城", "登錦城",
        "白頭吟", "白头吟", "詠螢火", "咏萤火",
    ],
    "youman": [
        # Simplified + Traditional
        "黄鹤楼", "黃鶴樓", "孟浩然", "庐山", "廬山", "天门山", "天門山",
        "长干", "長干", "金陵", "扬州", "揚州", "安陆", "安陸",
        "秋浦", "荆州", "荊州", "襄阳", "襄陽", "洛城", "江陵", "洞庭",
        "太原", "宣城", "泾县", "涇縣", "夜泊", "牛渚",
        "王昌龄", "王昌齡", "越中", "苏台", "蘇台", "下邳", "圯桥", "圯橋",
        "泰山", "徂徕", "徂徠", "竹溪", "金陵酒肆", "劳劳亭", "勞勞亭",
        "横江", "橫江", "关山月", "關山月", "塞下曲", "战城南", "戰城南",
        "子夜吴歌", "子夜吳歌", "杨叛儿", "楊叛兒", "采莲曲", "採蓮曲",
        "春夜洛城", "紫藤", "咏槿", "詠槿", "白鹰", "白鷹",
        "题北榭", "題北榭", "北榭碑", "静夜思", "靜夜思",
        "古朗月行", "渡荆门", "渡荊門", "夜宿山寺", "春思",
        "赠孟浩然", "贈孟浩然", "苏台览古", "蘇臺覽古", "越中览古", "越中覽古",
        "望庐山", "望廬山", "望天门", "望天門", "黄鹤楼送", "黃鶴樓送",
        "望庐山瀑布", "望廬山瀑布", "望天门山", "望天門山",
        "经下邳圯桥", "經下邳圯橋", "西岳云台歌", "西岳雲臺歌",
        "登太白峰", "山中问答", "山中問答", "题北榭碑", "題北榭碑",
        "横江词", "橫江詞",
        "送孟浩然", "荆州歌", "荊州歌", "襄阳歌", "襄陽歌", "秋浦歌",
        "夜宿", "劳劳亭", "勞勞亭", "玉階怨", "玉阶怨",
        "长门怨", "長門怨", "闺怨", "閨怨", "春怨", "怨情",
        "远别离", "遠別離", "白头吟", "白頭吟", "长门", "長門",
        "乌栖曲", "烏棲曲", "梁園吟", "梁园吟",
        "梁甫吟", "梁父吟", "襄阳曲", "襄陽曲",
        "登新平楼", "登新平樓", "秋日煉藥院",
        "赠裴", "贈裴", "送裴", "送裴十八",
    ],
    "changan": [
        # === 长安时期专属关键词（42-44岁，供奉翰林） ===
        # 清平调系列
        "清平调", "清平調", "清平樂", "清平乐",
        # 行路难系列（长安失意）
        "行路难", "行路難",
        # 宫中行乐词系列（奉诏之作）
        "宫中行乐", "宮中行樂", "行乐词", "行樂詞", "行樂詞",
        # 翰林/奉诏相关
        "翰林", "奉诏", "奉詔", "应制", "應制", "侍从", "侍從",
        "侍奉", "宜春苑", "龍池", "龙池", "興慶", "兴庆",
        "溫泉宮", "温泉宫", "溫泉", "温泉",
        # 贺知章相关
        "贺监", "賀監", "贺宾客", "賀賓客", "贺知章", "賀知章",
        "忆贺监", "憶賀監",
        # 玉壶吟
        "玉壶吟", "玉壺吟",
        # 南陵别儿童入京（入长安前）
        "南陵别", "南陵別", "别儿童", "別兒童", "入京",
        # 长相思（长安期间）
        "长相思", "長相思",
        # 其他长安专属
        "对酒忆贺", "對酒憶賀", "春日醉起", "醉起言志",
        "下终南山", "下終南山", "终南山", "終南山", "斛斯",
        "驾去温泉", "駕去溫泉", "贈楊山人", "赠杨山人",
        "詶岑勳", "酬岑勋", "元丹丘對酒", "元丹丘对酒",
        "对酒醉", "對酒醉", "屈突明府",
        "送賀", "送贺", "送舍弟",
        "古意", "白紵", "白纻", "白苧", "楊叛", "杨叛",
        "相逢行", "侠客行", "俠客行", "结客", "結客",
        "出自蓟北", "出自薊北", "薊北門", "薊北门",
        "长安", "長安",
    ],
    "youman2": [
        # Simplified + Traditional
        "天姥", "谢朓楼", "謝朓樓", "月下独酌", "月下獨酌",
        "早发白帝", "早發白帝",
        "送友人", "听蜀僧", "聽蜀僧", "游洞庭", "遊洞庭", "醉后", "醉後",
        "凤凰台", "鳳凰台", "把酒问月", "把酒問月", "王十二", "沙丘城",
        "石门送杜", "石門送杜",
        "王屋山人", "魏万", "魏萬", "独坐敬亭", "獨坐敬亭", "寄东鲁", "寄東魯",
        "江夏", "木瓜山", "东鲁", "東魯", "梁宋", "杜甫", "高适", "高適",
        "齐鲁", "齊魯", "鲁郡", "魯郡", "兖州", "兗州",
        "幽州", "安禄山", "安祿山", "赠钱", "贈錢", "上三峡", "上三峽",
        "病酒", "对雪", "對雪", "冬日归", "冬日歸", "五月东鲁", "五月東魯",
        "宣城见杜鹃", "宣城見杜鵑", "粉图山水", "粉圖山水", "泛沔州",
        "夜下征虏亭", "夜下徵虜亭", "寻雍尊师", "尋雍尊師",
        "将进酒", "將進酒", "赠汪伦", "贈汪倫", "答王十二", "北风行", "北風行",
        "梦游天姥", "夢遊天姥", "宣州谢朓楼", "宣州謝朓樓", "秋登宣城",
        "鲁郡东石门", "魯郡東石門", "沙丘城下寄", "送友人入蜀",
        "送王屋山人", "游泰山", "山中与幽人", "山中與幽人", "答王十二寒夜",
        "奔亡道中", "赠升州", "贈升州", "上崔相", "留别贾舍人", "留別賈舍人",
        "谢朓楼饯别", "謝朓樓餞別", "陪侍郎叔", "听蜀僧濬弹琴", "聽蜀僧濬彈琴",
        "陪族叔", "当涂赵炎", "當塗趙炎", "自汉阳病酒", "自漢陽病酒",
        "秋登宣城谢朓", "秋登宣城謝朓", "陪侍郎叔游洞庭",
        "游洞庭醉后", "遊洞庭醉後", "登金陵鳳凰臺", "登金陵凤凰台",
        "寄东鲁二稚子", "寄東魯二稚子", "东鲁门", "東魯門",
        "鲁中送", "魯中送", "韩侍御", "韓侍御", "赵炎", "趙炎",
        # Re-added: these were incorrectly matched to earlier periods
        "汪伦", "汪倫", "桃花潭",
        "早发", "早發", "白帝",
    ],
    "liufang": [
        # Simplified + Traditional
        "夜郎", "流夜郎", "临路", "臨路", "临终", "臨終", "笑歌行",
        "南奔", "安史", "永王", "浔阳", "潯陽", "狱中", "獄中",
        "崔相", "万愤词", "萬憤詞", "西塞驿", "西塞驛", "巴东", "巴東",
        "瞿塘峡", "瞿塘峽", "巫山", "豫章", "李阳冰", "李陽冰",
        "当涂", "當塗", "司空山", "赠张相镐", "贈張相鎬", "经乱离后",
        "經亂離後", "放后遇恩", "放後遇恩", "献从叔", "獻從叔",
        "赠江夏韦太守", "贈江夏韋太守", "经乱離", "經亂離",
        "流夜郎", "忆旧游", "憶舊遊", "赠韦", "贈韋",
    ],
}

PERIOD_NAMES = {
    "shuzhong": "蜀中时期（701-725）",
    "youman": "漫游时期（725-742）",
    "changan": "长安时期（742-744）",
    "youman2": "再漫游时期（744-755）",
    "liufang": "流放时期（755-762）",
}


def classify_period(title, paragraphs=None):
    """Try to classify a poem into one of the five periods."""
    full_text = title
    if paragraphs:
        full_text += " " + " ".join(paragraphs)

    best_period = None
    best_score = 0

    for period, keywords in PERIOD_RULES.items():
        score = 0
        for kw in keywords:
            if kw in full_text:
                score += 1
        if score > best_score:
            best_score = score
            best_period = period

    return best_period if best_score > 0 else None


def fetch_all_tang_poems():
    """Download all poet.tang.*.json files and extract Li Bai's poems."""
    li_bai_poems = []

    for i in range(0, 58):
        url = f"{REPO_RAW}/poet.tang.{i * 1000}.json"
        try:
            resp = session.get(url, timeout=30)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            if i == 0:
                print(f"[ERROR] Failed to fetch first batch: {e}")
                return []
            print(f"  [skip] poet.tang.{i*1000}.json: {e}")
            continue

        for poem in data:
            if poem.get("author") == "李白":
                li_bai_poems.append(poem)

        print(f"  poet.tang.{i*1000}.json: {len(data)} poems, "
              f"Li Bai total: {len(li_bai_poems)}")

    return li_bai_poems


def infer_form(paragraphs):
    """Infer the poem form from structure."""
    if not paragraphs:
        return "未知"

    lines = [p for p in paragraphs if p.strip()]
    n_lines = len(lines)
    punct_pattern = re.compile(r'[，。！？、；：“”‘’（）\(\)\s]')

    if n_lines == 4:
        chars = sum(len(punct_pattern.sub('', line)) for line in lines)
        if chars > 0:
            avg = chars // n_lines
            if avg <= 5:
                return "五绝"
            elif avg <= 7:
                return "七绝"
    elif n_lines == 8:
        chars = sum(len(punct_pattern.sub('', line)) for line in lines)
        if chars > 0:
            avg = chars // n_lines
            if avg <= 5:
                return "五律"
            elif avg <= 7:
                return "七律"

    return "古体/乐府"


def main():
    print("=" * 60)
    print("Li Bai Poem Extraction Tool")
    print("=" * 60)

    # Load existing titles
    print("\n[1] Loading existing skeleton titles...")
    existing_titles = load_existing_titles()
    print(f"  Existing skeleton: {len(existing_titles)} poems")
    if existing_titles:
        sample = list(existing_titles)[:5]
        print(f"  Sample: {sample}")

    # Fetch from GitHub
    print("\n[2] Downloading Li Bai poems from github...")
    all_li_bai = fetch_all_tang_poems()
    print(f"  Total Li Bai poems found: {len(all_li_bai)}")

    if not all_li_bai:
        print("[ERROR] No Li Bai poems found, check network or repo URL")
        sys.exit(1)

    # Deduplicate
    print("\n[3] Deduplication...")
    new_poems = []
    duplicate_count = 0
    for poem in all_li_bai:
        title = poem.get("title", "")
        if not is_duplicate(title, existing_titles):
            new_poems.append(poem)
        else:
            duplicate_count += 1
    print(f"  Duplicates (already in skeleton): {duplicate_count}")
    print(f"  New poems: {len(new_poems)}")

    # Classify periods
    print("\n[4] Classifying by period...")
    dated_poems = []
    undated_poems = []

    for poem in new_poems:
        title = poem.get("title", "")
        paragraphs = poem.get("paragraphs", [])
        period = classify_period(title, paragraphs)

        poem_entry = {
            "title": title,
            "author": "李白",
            "paragraphs": paragraphs,
            "form": infer_form(paragraphs),
        }

        if period:
            poem_entry["period"] = period
            poem_entry["period_name"] = PERIOD_NAMES.get(period, period)
            dated_poems.append(poem_entry)
        else:
            undated_poems.append(poem_entry)

    print(f"  With clear dating: {len(dated_poems)}")
    print(f"  Undated: {len(undated_poems)}")

    # Group by period
    period_groups = {}
    for poem in dated_poems:
        p = poem["period"]
        if p not in period_groups:
            period_groups[p] = []
        period_groups[p].append(poem)

    print("\n  Distribution by period:")
    for period, poems in sorted(period_groups.items()):
        name = PERIOD_NAMES.get(period, period)
        print(f"    {name}: {len(poems)}")

    # Save
    print(f"\n[5] Saving to {OUTPUT}...")
    os.makedirs(POEMS_DIR, exist_ok=True)
    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump({
            "total": len(dated_poems),
            "by_period": period_groups,
            "poems": dated_poems
        }, f, ensure_ascii=False, indent=2)

    if undated_poems:
        print(f"  Saving undated to {UNDATED_OUTPUT}...")
        with open(UNDATED_OUTPUT, "w", encoding="utf-8") as f:
            json.dump({
                "total": len(undated_poems),
                "poems": undated_poems
            }, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 60)
    print(f"Done! Dated: {len(dated_poems)}, Undated: {len(undated_poems)}")
    print("=" * 60)


if __name__ == "__main__":
    main()
