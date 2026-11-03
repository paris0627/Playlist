"""무드 플레이리스트 추천기 - Streamlit 앱

실행: streamlit run app.py
"""
import html
import random
import re
from collections import Counter
from urllib.parse import quote_plus

import pandas as pd
import streamlit as st

from songs_data import CATEGORIES, MOODS, PLACES, SONGS, WEATHERS

CATEGORY_ICON = {"POP": "🎤", "K-Pop": "💿", "클래식": "🎻", "기타": "🎷"}
CATEGORY_COLOR = {"POP": "#E0457B", "K-Pop": "#3A6FF7", "클래식": "#B8892B", "기타": "#1F9D8A"}

st.set_page_config(page_title="무드 플레이리스트", page_icon="🎧", layout="wide")

# ------------------------------------------------------------------
# 스타일 (커스텀 CSS는 여기 한 곳에만)
# ------------------------------------------------------------------
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Gowun+Dodum&family=IBM+Plex+Sans+KR:wght@400;600&display=swap');

.stApp { font-family: 'IBM Plex Sans KR', 'Malgun Gothic', 'Apple SD Gothic Neo', sans-serif;
  /* 테마 색을 하드코딩하지 않는다: 글자색은 Streamlit 테마를 상속하고, 바탕은 반투명 틴트라
     라이트/다크 어느 테마로 바꿔도(재실행 없이도) 즉시 어울린다. */
  --muted: color-mix(in srgb, currentColor 72%, transparent);
  --paper: rgba(110, 118, 180, 0.13); --surface: rgba(110, 118, 180, 0.05); --line: rgba(110, 118, 180, 0.28); }
.stApp h1, .stApp h2, .stApp h3 { font-family: 'Gowun Dodum', 'Malgun Gothic', 'Apple SD Gothic Neo', sans-serif; letter-spacing: -0.01em; }

/* 히어로 */
.hero { display: flex; align-items: flex-end; gap: 1.25rem; padding: 1.75rem 1.5rem;
        border-radius: 18px; background: var(--paper); color: inherit; margin-bottom: 0.5rem; }
.hero h1 { font-family: 'Gowun Dodum', 'Malgun Gothic', 'Apple SD Gothic Neo', sans-serif; font-size: clamp(1.6rem, 4vw, 2.6rem);
           line-height: 1.15; margin: 0; padding: 0; color: inherit; }
.hero p { margin: 0.4rem 0 0; color: var(--muted); font-size: 1rem; max-width: 36em; }
.eq { display: flex; align-items: flex-end; gap: 5px; height: 56px; flex: none; }
.eq span { width: 9px; border-radius: 3px; animation: eq 1.1s ease-in-out infinite alternate; }
.eq span:nth-child(1) { background: #E0457B; height: 40%; animation-delay: -.2s; }
.eq span:nth-child(2) { background: #3A6FF7; height: 90%; animation-delay: -.6s; }
.eq span:nth-child(3) { background: #B8892B; height: 60%; animation-delay: -.9s; }
.eq span:nth-child(4) { background: #1F9D8A; height: 75%; animation-delay: -.4s; }
@keyframes eq { from { transform: scaleY(.35); } to { transform: scaleY(1); } }
.eq span { transform-origin: bottom; }
@media (prefers-reduced-motion: reduce) { .eq span { animation: none; } }

/* 카테고리 구성 막대 */
.mix { margin: 0.25rem 0 1rem; }
.mix-bar { display: flex; height: 10px; border-radius: 999px; overflow: hidden; gap: 2px; }
.mix-legend { display: flex; flex-wrap: wrap; gap: 0.4rem 1.1rem; margin-top: 0.5rem; font-size: 0.9rem; }
.mix-key i { display: inline-block; width: 10px; height: 10px; border-radius: 50%; margin-right: 6px; }

/* 트랙(곡) 카드 */
.track { display: grid; grid-template-columns: 3.2rem 1fr auto; gap: 0.25rem 1rem; align-items: start;
         background: var(--surface); color: inherit; border: 1px solid var(--line);
         border-left: 6px solid var(--cat); border-radius: 12px; padding: 1rem 1.1rem; margin-bottom: 0.75rem; }
.track-no { font-family: 'Gowun Dodum', 'Malgun Gothic', 'Apple SD Gothic Neo', sans-serif; font-size: 2rem; line-height: 1; color: var(--cat); }
.track-head { display: flex; flex-wrap: wrap; align-items: center; gap: 0.4rem; }
.track-title { font-size: 1.15rem; font-weight: 600; margin-right: 0.3rem; }
.badge { font-size: 0.78rem; padding: 0.12rem 0.55rem; border-radius: 999px; background: var(--cat); color: #fff; }
.badge-ghost { background: transparent; color: var(--cat); border: 1px solid var(--cat); }
.match { font-size: 0.8rem; font-weight: 600; color: inherit; }
.track-desc { margin: 0.35rem 0 0.6rem; color: var(--muted); font-size: 0.92rem; }
.track-meta { display: flex; flex-wrap: wrap; gap: 0.4rem 1.6rem; margin: 0 0 0.6rem; }
.track-meta dt { font-size: 0.75rem; color: var(--muted); margin: 0; font-weight: 400; }
.track-meta dd { margin: 0; font-size: 0.95rem; }
.chips { display: flex; flex-wrap: wrap; gap: 0.35rem; }
.chip { font-size: 0.78rem; padding: 0.1rem 0.5rem; border-radius: 6px; background: var(--paper); color: inherit; }
.play { align-self: center; white-space: nowrap; text-decoration: none !important; font-weight: 600; font-size: 0.9rem;
        padding: 0.45rem 0.9rem; border-radius: 999px; border: 1.5px solid var(--cat); color: var(--cat) !important; }
.play:hover { background: var(--cat); color: #fff !important; }
.play:focus-visible { outline: 3px solid var(--cat); outline-offset: 2px; }

@media (max-width: 640px) {
  .hero { padding: 1.25rem 1rem; gap: 0.9rem; }
  .eq { height: 40px; }
  .track { grid-template-columns: 2.2rem 1fr; padding: 0.85rem 0.9rem; }
  .track-no { font-size: 1.5rem; }
  .play { grid-column: 2; justify-self: start; margin-top: 0.4rem; }
}
</style>
""",
    unsafe_allow_html=True,
)

# ------------------------------------------------------------------
# 세션 상태
# ------------------------------------------------------------------
if "seed" not in st.session_state:
    st.session_state.seed = random.randint(0, 10**6)


# ------------------------------------------------------------------
# 추천 로직
# ------------------------------------------------------------------
def filter_by_category(songs, categories):
    return [s for s in songs if s["category"] in categories]


def recommend_single(field, value, categories, n, seed):
    """기분/날씨/장소 중 하나의 조건으로 추천."""
    pool = [s for s in filter_by_category(SONGS, categories) if value in s[field]]
    rng = random.Random(f"{seed}-{field}-{value}")
    rng.shuffle(pool)
    return pool[:n]


def recommend_combined(mood, weather, place, categories, n, seed):
    """여러 조건을 동시에 고려: 일치 조건 수가 많은 곡부터."""
    conditions = [("moods", mood), ("weathers", weather), ("places", place)]
    conditions = [(f, v) for f, v in conditions if v]
    if not conditions:
        return [], 0

    rng = random.Random(f"{seed}-combo-{mood}-{weather}-{place}")
    scored = []
    for s in filter_by_category(SONGS, categories):
        score = sum(v in s[f] for f, v in conditions)
        if score > 0:
            scored.append((score, rng.random(), s))
    scored.sort(key=lambda x: (-x[0], x[1]))
    return [(score, s) for score, _, s in scored[:n]], len(conditions)


# ------------------------------------------------------------------
# UI 컴포넌트
# ------------------------------------------------------------------
def is_classical(s):
    return s["category"] == "클래식"


def youtube_url(s):
    # 클래식은 artist가 "작곡가 (작품)" 형식이라 검색어로 부적합 → 작곡가 원어 이름 사용
    who = s["composer"] if is_classical(s) else s["artist"]
    return "https://www.youtube.com/results?search_query=" + quote_plus(f"{s['title']} {who}")


def render_summary(songs):
    """카테고리 비율 막대 + 범례."""
    counts = Counter(s["category"] for s in songs)
    total = len(songs)
    segments = "".join(
        f'<span class="mix-seg" style="flex:{counts[c]};background:{CATEGORY_COLOR[c]}"></span>'
        for c in CATEGORIES if counts.get(c)
    )
    legend = "".join(
        f'<span class="mix-key"><i style="background:{CATEGORY_COLOR[c]}"></i>'
        f'{c} <b>{counts.get(c, 0)}</b></span>'
        for c in CATEGORIES
    )
    st.markdown(
        f'<div class="mix" role="img" aria-label="카테고리 구성, 총 {total}곡">'
        f'<div class="mix-bar">{segments}</div><div class="mix-legend">{legend}</div></div>',
        unsafe_allow_html=True,
    )


def render_song_card(idx, s, match_text=None):
    e = html.escape
    color = CATEGORY_COLOR[s["category"]]
    chips = (
        [f"{MOODS[m]} {m}" for m in s["moods"]]
        + [f"{WEATHERS[w]} {w}" for w in s["weathers"]]
        + [f"{PLACES[p]} {p}" for p in s["places"]]
    )
    match_html = f'<span class="match">🎯 {e(match_text)}</span>' if match_text else ""
    html_block(
        f"""
<div class="track" style="--cat:{color}">
  <div class="track-no">{idx:02d}</div>
  <div class="track-body">
    <div class="track-head">
      <span class="track-title">{e(s['title'])}</span>
      <span class="badge">{CATEGORY_ICON[s['category']]} {e(s['category'])}</span>
      <span class="badge badge-ghost">{e(s['sub_genre'])}</span>
      {match_html}
    </div>
    <p class="track-desc">{e(s['description'])}</p>
    <dl class="track-meta">
      <div><dt>가수/연주</dt><dd>{e(s['artist'])}</dd></div>
      <div><dt>작곡가</dt><dd>{e(s['composer'])}</dd></div>
      <div><dt>{'작곡연도' if is_classical(s) else '발매연도'}</dt><dd>{s['year']}</dd></div>
    </dl>
    <div class="chips">{''.join(f'<span class="chip">{e(c)}</span>' for c in chips)}</div>
  </div>
  <a class="play" href="{e(youtube_url(s))}" target="_blank" rel="noopener noreferrer"
     aria-label="{e(s['title'])} YouTube에서 듣기">▶ 듣기</a>
</div>"""
    )


def html_block(markup):
    """Markdown이 들여쓰기/빈 줄을 코드 블록으로 오인하지 않도록 한 줄로 합친다."""
    st.markdown(re.sub(r"\n\s*", " ", markup).strip(), unsafe_allow_html=True)


def render_playlist(songs, title, matches=None, total_conditions=None):
    if not songs:
        st.warning("조건에 맞는 곡이 없어요. 사이드바에서 카테고리를 더 선택해 보세요.")
        return
    st.subheader(f"{title} ({len(songs)}곡)")
    render_summary(songs)
    for i, s in enumerate(songs, 1):
        match_text = None
        if matches is not None:
            match_text = f"일치도 {matches[i - 1]}/{total_conditions}"
        render_song_card(i, s, match_text)


def option_radio(label, options, key):
    """이모지가 붙은 가로형 라디오 버튼. 선택된 키(이모지 제외)를 반환."""
    choice = st.radio(
        label, list(options.keys()), horizontal=True, key=key,
        format_func=lambda k: f"{options[k]} {k}",
    )
    return choice


# ------------------------------------------------------------------
# 사이드바
# ------------------------------------------------------------------
with st.sidebar:
    st.header("추천 설정")
    selected_categories = st.multiselect(
        "음악 카테고리",
        CATEGORIES,
        default=CATEGORIES,
        format_func=lambda c: f"{CATEGORY_ICON[c]} {c}",
    )
    n_songs = st.slider("추천 곡 수", min_value=3, max_value=15, value=7)
    if st.button("🔀 다시 섞기", width="stretch"):
        st.session_state.seed = random.randint(0, 10**6)
    st.divider()
    st.subheader("라이브러리")
    st.caption(f"전체 {len(SONGS)}곡을 이렇게 나눠 담았어요.")
    render_summary(SONGS)

if not selected_categories:
    st.sidebar.error("카테고리를 하나 이상 선택해 주세요.")

seed = st.session_state.seed

# ------------------------------------------------------------------
# 메인
# ------------------------------------------------------------------
html_block(
    """
<header class="hero">
  <div class="eq" aria-hidden="true"><span></span><span></span><span></span><span></span></div>
  <div>
    <h1>무드 플레이리스트</h1>
    <p>지금 기분, 날씨, 있는 곳을 고르면 어울리는 곡을 골라 드려요.</p>
  </div>
</header>"""
)

tab_mood, tab_weather, tab_place, tab_combo, tab_lib = st.tabs(
    ["😊 기분", "🌦️ 날씨", "📍 장소", "🎯 종합 추천", "📚 라이브러리"]
)

with tab_mood:
    mood = option_radio("지금 기분은 어떤가요?", MOODS, "mood_single")
    render_playlist(
        recommend_single("moods", mood, selected_categories, n_songs, seed),
        f"{MOODS[mood]} '{mood}' 기분을 위한 플레이리스트",
    )

with tab_weather:
    weather = option_radio("오늘 날씨는?", WEATHERS, "weather_single")
    render_playlist(
        recommend_single("weathers", weather, selected_categories, n_songs, seed),
        f"{WEATHERS[weather]} '{weather}' 날씨에 어울리는 플레이리스트",
    )

with tab_place:
    place = option_radio("지금 어디에 있나요?", PLACES, "place_single")
    render_playlist(
        recommend_single("places", place, selected_categories, n_songs, seed),
        f"{PLACES[place]} '{place}'에서 듣기 좋은 플레이리스트",
    )

with tab_combo:
    st.write("여러 조건을 함께 고르면 더 많이 일치하는 곡부터 추천해요.")
    c1, c2, c3 = st.columns(3)
    none = "선택 안 함"
    combo_mood = c1.selectbox(
        "기분", [none] + list(MOODS),
        format_func=lambda k: k if k == none else f"{MOODS[k]} {k}",
    )
    combo_weather = c2.selectbox(
        "날씨", [none] + list(WEATHERS),
        format_func=lambda k: k if k == none else f"{WEATHERS[k]} {k}",
    )
    combo_place = c3.selectbox(
        "장소", [none] + list(PLACES),
        format_func=lambda k: k if k == none else f"{PLACES[k]} {k}",
    )
    picks = [v if v != none else None for v in (combo_mood, combo_weather, combo_place)]
    results, total = recommend_combined(*picks, selected_categories, n_songs, seed)
    if total == 0:
        st.info("기분, 날씨, 장소 중 하나 이상을 선택해 주세요.")
    else:
        label = " + ".join(v for v in picks if v)
        render_playlist(
            [s for _, s in results],
            f"'{label}' 맞춤 플레이리스트",
            matches=[score for score, _ in results],
            total_conditions=total,
        )

with tab_lib:
    st.subheader("📚 전체 음악 라이브러리")
    query = st.text_input("검색 (곡명 / 가수 / 작곡가)", placeholder="예: 아이유, Chopin, Rain")
    df = pd.DataFrame(filter_by_category(SONGS, selected_categories))
    if not df.empty:
        if query:
            q = query.lower()
            mask = df[["title", "artist", "composer"]].apply(
                lambda col: col.str.lower().str.contains(q, regex=False)
            ).any(axis=1)
            df = df[mask]
        for col in ("moods", "weathers", "places"):
            df[col] = df[col].apply(", ".join)
        df = df.rename(columns={
            "title": "곡명", "artist": "가수/연주", "composer": "작곡가",
            "year": "발매/작곡연도", "category": "카테고리", "sub_genre": "세부 장르",
            "moods": "기분", "weathers": "날씨", "places": "장소", "description": "설명",
        })
        st.caption(f"{len(df)}곡")
        st.dataframe(df, width="stretch", hide_index=True)
    else:
        st.info("선택된 카테고리가 없어요.")
