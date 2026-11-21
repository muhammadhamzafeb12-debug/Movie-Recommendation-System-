import streamlit as st
import pandas as pd
import json
import html
import os
from training import recommend, new_df

st.set_page_config(
    page_title="CineMatch | Discover Movies",
    page_icon="🎬",
    layout="wide"
)


@st.cache_data
def load_poster_map():
    df = pd.read_csv("9000plus.csv")
    df = df.dropna(subset=["Title", "Poster_Url"])

    def normalize(value):
        return "".join(
            ch.lower() for ch in str(value) if ch.isalnum()
        )

    df["key"] = df["Title"].apply(normalize)
    return dict(zip(df["key"], df["Poster_Url"]))

POSTER_MAP = load_poster_map()

@st.cache_data
def load_missing_poster_urls():
    try:
        with open("missing_poster_urls.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

MISSING_POSTER_URLS = load_missing_poster_urls()


@st.cache_data
def load_movies():
    return pd.read_csv("tmdb_5000_movies.csv").drop_duplicates("id")

movies = load_movies()

st.markdown("""
<style>
.stApp {
    background: radial-gradient(circle at top left, #292044 0%, #10111e 45%, #080a12 100%);
    color: #ffffff;
}
.block-container {
    max-width: 1450px;
    padding-top: 2rem;
}
h1,h2,h3,p,label {color:#f5f3ff !important;}
.hero {
    padding: 34px;
    border-radius: 22px;
    background: linear-gradient(115deg,#39275f,#171d38,#382047);
    border: 1px solid #66508b;
    margin-bottom: 28px;
}
.eyebrow {
    color: #f5c96b;
    letter-spacing: 4px;
    font-size: 12px;
    font-weight: bold;
}
.poster-frame {
    background: linear-gradient(145deg,#45336c,#1d2949,#713a62);
    border: 1px solid #65517f;
    border-radius: 15px;
    padding: 12px;
    text-align: center;
    min-height: 280px;
    display: flex;
    flex-direction: column;
    justify-content: center;
}
.poster-frame .emoji {font-size:55px;}
.poster-frame .poster-name {
    font-size: 23px;
    font-weight: 800;
    color: white;
}
.movie-card {
    background: linear-gradient(160deg,#24243b,#151827);
    border: 1px solid #45415e;
    padding: 13px;
    border-radius: 15px;
    min-height: 140px;
    margin-bottom: 10px;
}
.rating {color:#ffd166;font-weight:800;}
div.stButton > button {
    background: linear-gradient(90deg,#f5c96b,#d99b3d);
    color:#171321;
    border:0;
    border-radius:10px;
    font-weight:800;
    min-height:45px;
}
div.stButton > button:hover {
    background:#ffe09a;
    color:#171321;
}
[data-testid="stExpander"] {
    background:#191a2c;
    border:1px solid #45415e;
    border-radius:10px;
}
hr {border-color:#39334e;}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero">
  <div class="eyebrow">YOUR PERSONAL CINEMA EXPERIENCE</div>
  <h1 style="font-size:48px;margin:10px 0;">🎬 CineMatch</h1>
  <p style="font-size:17px;color:#ddd5ef;">
    Discover your next favourite movie with Machine Learning.
  </p>
</div>
""", unsafe_allow_html=True)

movie_list = sorted(new_df["title"].dropna().unique().tolist())

if not movie_list:
    st.error("No movies available.")
    st.stop()

default_index = movie_list.index("Avatar") if "Avatar" in movie_list else 0

selected_movie = st.selectbox(
    "🔎 Search your movie",
    movie_list,
    index=default_index
)

selected_data = movies[movies["title"] == selected_movie]

@st.cache_data
def load_local_poster_index():
    try:
        with open("posters/poster_index.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


LOCAL_POSTERS = load_local_poster_index()


def show_poster(title, movie_id=None):
    # 1. Prefer existing local poster files.
    local_path = LOCAL_POSTERS.get(str(int(movie_id))) if movie_id is not None and pd.notna(movie_id) else None
    if local_path and os.path.isfile(local_path):
        st.image(local_path, use_container_width=True)
        return

    # 2. Use newly recovered poster URLs by TMDB movie ID.
    if movie_id is not None and pd.notna(movie_id):
        url = MISSING_POSTER_URLS.get(str(int(movie_id)))
        if url:
            st.image(url, use_container_width=True)
            return

    # 3. Keep existing 9000plus.csv title-based poster fallback.
    key = "".join(ch.lower() for ch in str(title) if ch.isalnum())
    url = POSTER_MAP.get(key)
    if url:
        url = url.replace("/original/", "/w500/")
        st.image(url, use_container_width=True)
        return

    st.markdown(
        f'<div class="poster-frame"><div class="emoji">🎥</div>'
        f'<div class="poster-name">{html.escape(str(title))}</div>'
        f'<p style="color:#e2d7f7;">POSTER NOT FOUND IN PUBLIC DATASET</p></div>',
        unsafe_allow_html=True
    )


def get_genres(value):
    try:
        items = json.loads(value)
        return " • ".join(x["name"] for x in items[:3])
    except Exception:
        return "Movie"

if not selected_data.empty:
    movie = selected_data.iloc[0]
    left, right = st.columns([1, 2], gap="large")

    with left:
        show_poster(selected_movie, movie.get('id'))

    with right:
        st.markdown(f"## {selected_movie}")
        st.markdown(
            f'<p class="rating">⭐ {movie["vote_average"]}/10</p>',
            unsafe_allow_html=True
        )
        st.write("📅 Release:", movie.get("release_date", "N/A"))
        st.write("🎭 Genre:", get_genres(movie.get("genres", "")))
        st.markdown("### About this movie")
        st.write(movie.get("overview", "Description unavailable."))

st.divider()

if st.button("✨ DISCOVER 5 SIMILAR MOVIES", use_container_width=True):
    st.session_state["cine_recommendations"] = recommend(selected_movie)

if "cine_recommendations" in st.session_state:
    st.markdown("## 🍿 Recommended For You")
    st.caption("Content-based filtering • Cosine similarity")

    recommendations = st.session_state["cine_recommendations"]

    if recommendations:
        cols = st.columns(5)

        for i, title in enumerate(recommendations[:5]):
            result = movies[movies["title"] == title]

            with cols[i]:
                if not result.empty:
                    item = result.iloc[0]
                    show_poster(title, item.get('id'))
                    st.markdown(f"**{title}**")
                    st.markdown(
                        f'<p class="rating">⭐ {item["vote_average"]}/10</p>',
                        unsafe_allow_html=True
                    )
                    with st.expander("Movie details"):
                        st.write(item.get("overview", "No description."))
                else:
                    st.write(title)
    else:
        st.warning("No recommendations found.")

st.divider()
st.markdown(
    "<center style='color:#a69bbd;'>"
    "CineMatch | Python • Streamlit • Scikit-learn"
    "</center>",
    unsafe_allow_html=True
)
