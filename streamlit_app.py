import streamlit as st
import feedparser
import pandas as pd
from urllib.parse import quote
import ssl
from datetime import datetime

# --- 1. CONFIGURATION ---
WATCHLIST_GROUPS = {
   "Hammond Power": ["Hammond Power", "Dry Type Transformer", "Hyundai Electric", "AEG Power Systems", "Uninterruptible Power Supply", "Schneider Electric", "Siemens", "Eaton Corp"],
    "Tantalus": ["Tantalus", "Tantalus Systems", "Smart metering systems", "Itron", "Landis + Gyr", "Grid Tech",],
    "Kraken": ["Kraken", "PNG", "REMUS", "NAVSEA", "Lockheed Martin", "L3Harris", "Airbus", "Rtx defense", "Northrop Grumman", "Thales Defense", "Subsea battery", "Kongsberg", "Cellula Robotics", "Huntington Ingalls", "Teledyne Technologies", "Anduril""Covelya", "Sonardyne", "EIVA", "Forcys", "Wavefront", "Chelsea Technologies", "Voyis"],
    "5N Plus": ["5N Plus", "VNP", "Germanium", "Tellurium", "Cadmium", "AZUR Space", "Sierra Space", "Bismuth", "USA Rare Earth", "MP Materials", "First Solar"],
    "ISC": ["ISC", "Information Services Corp", "Dye & Durham", "Saskatchewan Registry", "Canada Business Registry"],
    "Neo Performance": ["NEO", "Neo Performance Materials", "Rare Earth Oxides", "Rare Earth Minerals"],
    "Polaris": ["Polaris Renewable Energy", "PIF"],
    "DIRTT": ["DIRTT", "DRT"],
    "Biorem": ["BRM", "Biorem"],
    "Atlas": ["AEP", "Atlas Engineered Products", "Canadian Roof Trusses", "Canadian Building Products"],
    "Calian": ["CGY", "Calian", "Arctic Sovereignty", "Canadian Armed Forces", "Canadian Defense", "Arctic War", "Canadian Navy"],
   "All": ["CGY", "Calian","Hammond Power", "Dry Type Transformer", "Hyundai Electric", "AEG Power Systems", "Uninterruptible Power Supply", "Schneider Electric", "Siemens", "Eaton Corp", "Tantalus", "Tantalus Systems", "Smart metering systems", "Itron", "Landis + Gyr", "Kraken", "PNG", "REMUS", "NAVSEA", "Lockheed Martin", "L3Harris", "Airbus", "Rtx defense", "Northrop Grumman", "Thales Defense", "Subsea battery", "Kongsberg", "Cellula Robotics", "Huntington Ingalls", "Teledyne Technologies", "Anduril", "Covelya", "Sonardyne", "EIVA", "Forcys", "Wavefront", "Chelsea Technologies", "Voyis", "Grid Tech", "ISC", "Information Services Corp", "Dye & Durham", "Saskatchewan Registry", "Canada Business Registry", "Polaris Renewable Energy", "PIF", "AEP", "Atlas Engineered Products", "Canadian Roof Trusses", "Canadian Building Products",  ],
}

# The Default Blacklist (Hidden automatically)
DEFAULT_BLACKLIST = ["MarketBeat", "Simply Wall St", "Zacks Investment Research", "Stock Traders Daily", "Defense World", "Best Stocks"]

# The Default Whitelist (Premium sources you might want to isolate)
PREMIUM_SOURCES = ["The Globe and Mail", "Bloomberg", "Reuters", "Financial Post", "CNBC", "Yahoo Finance"]

LOGO_URL = "https://cormark.com/Portals/_default/Skins/Cormark/Images/Cormark_4C_183x42px.png"

st.set_page_config(page_title="Purdchuk News Screener", page_icon=LOGO_URL, layout="wide")
st.logo(LOGO_URL, link="https://cormark.com/")

if 'news_data' not in st.session_state:
    st.session_state.news_data = []

# --- 2. SIDEBAR: THE DUAL-FILTER SYSTEM ---
with st.sidebar:
    st.title("Purdchuk Settings")
    selected_group = st.selectbox("Watchlist Category", options=list(WATCHLIST_GROUPS.keys()))
    
    st.divider()
    st.header("Source Controls")
    
    # Extract unique sources from data for the dropdowns
    available_sources = []
    if st.session_state.news_data:
        available_sources = sorted(list(set([item['Source'] for item in st.session_state.news_data])))
    
    # 1. WHITELIST: Only show these if selected
    whitelist = st.multiselect(
        "⭐ Whitelist (Show ONLY these):",
        options=available_sources,
        help="If you select sources here, all others will be hidden."
    )
    
    # 2. BLACKLIST: Hide these automatically
    present_blacklist = [s for s in DEFAULT_BLACKLIST if s in available_sources]
    blacklist = st.multiselect(
        "🚫 Blacklist (Always Hide):",
        options=available_sources,
        default=present_blacklist
    )

    st.divider()
    keyword_filter = st.text_input("🔍 Search Headlines", "").strip().lower()

# --- 3. THE SCANNER ---
def get_google_news(company_name):
    query = quote(f'{company_name} when:7d')
    url = f"https://news.google.com/rss/search?q={query}&hl=en-CA&gl=CA&ceid=CA:en"
    ssl_context = ssl._create_unverified_context()
    feed = feedparser.parse(url)
    results = []
    for entry in feed.entries[:10]:
        parsed_date = entry.get('published_parsed')
        sort_date = datetime(*parsed_date[:6]) if parsed_date else datetime(1900, 1, 1)
        results.append({
            "sort_key": sort_date,
            "Date": sort_date.strftime('%b %d, %Y'),
            "Company": company_name,
            "Source": entry.source.get('title', 'Google News'),
            "Headline": entry.title,
            "Link": entry.link
        })
    return results

# --- 4. MAIN UI & LOGIC ---
st.title("Purdchuk News Screener")
st.subheader(f"Current Watchlist: {selected_group}")

if st.button(f" Search {selected_group} List", use_container_width=True):
    all_hits = []
    with st.spinner('Gathering intelligence...'):
        for company in WATCHLIST_GROUPS[selected_group]:
            all_hits.extend(get_google_news(company))
    st.session_state.news_data = all_hits

if st.session_state.news_data:
    df = pd.DataFrame(st.session_state.news_data).sort_values(by="sort_key", ascending=False)
    
    # --- LOGIC: Apply Whitelist First ---
    if whitelist:
        df = df[df['Source'].isin(whitelist)]
    
    # --- LOGIC: Apply Blacklist Second ---
    if blacklist:
        df = df[~df['Source'].isin(blacklist)]
    
    # Keyword filter
    if keyword_filter:
        df = df[df['Headline'].str.lower().str.contains(keyword_filter)]

    st.success(f"Curated {len(df)} headlines for your review.")
    st.dataframe(
        df[["Date", "Company", "Source", "Headline", "Link"]], 
        column_config={"Link": st.column_config.LinkColumn("View Article")},
        use_container_width=True, 
        hide_index=True
    )
