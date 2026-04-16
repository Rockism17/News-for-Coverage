import streamlit as st
import feedparser
import pandas as pd
from urllib.parse import quote
import ssl
from datetime import datetime
import concurrent.futures

# --- 1. DATA STRUCTURE ---
SUBS_MAP = {
    "Alaris": ["3E, LLC", "Accscient, LLC", "Amur Financial Group", "SonoBello", "Cresa, LLC", "DNT Construction", "Edgewater Technical Associates", "Fleet Advantage", "Federal Management Partners", "GlobalWide Media", "Heritage Restoration", "Kubik, LP", "LMS Reinforcing Steel", "McCoy Roofing", "Ohana Growth Partners", "Optimus SBR", "Professional Electric Contractors", "Sagamore Plumbing", "SCR Mining & Tunnelling", "The Shipyard, LLC", "Unify Consulting", "D&M Leasing"],
    "Exchange Income": ["Canadian North", "PAL Aerospace", "PAL Airlines", "Perimeter Aviation", "Calm Air", "Bearskin Airlines", "Keewatin Air", "Regional One", "Custom Helicopters", "Moncton Flight College", "Newfoundland Helicopters", "Air Borealis", "Mach2", "BC Medevac", "Northern Mat and Bridge", "Spartan Mat", "WesTower Communications", "Quest Window Systems", "BVGlazing Systems", "Ben Machine Products", "Stainless Fabrication", "DryAir Manufacturing", "Hansen Industries", "Overlanders Manufacturing", "LV Control Mfg", "Water Blast Manufacturing", "Duhamel Sawmill"],
    "Bridgemarq": ["Royal LePage", "Proprio Direct", "Via Capitale"],
    "Diversified Royalty": ["Mr. Lube", "Air Miles", "Sutton Group", "Nurse Next Door", "Oxford Learning", "BarBurrito", "Cheba Hut", "Mr. Mikes"],
    "Dominion Lending": ["Mortgage Architects", "MCC Mortgage Centre", "Newton Connectivity"],
    "Fairfax": ["Odyssey Group", "Allied World", "Northbridge Financial", "Crum & Forster", "Brit Insurance"],
    "goeasy": ["easyfinancial", "easyhome", "LendCare"],
    "Propel": ["CreditFresh", "MoneyKey", "Fora Credit", "QuidMarket", "FreshLine"],
    "Trisura": ["Trisura Guarantee Insurance", "Trisura Specialty"],
    "Versabank": ["DRT Cyber", "Structured Receivable"],
    "Westaim": ["Skyward Specialty", "Arena Investors", "Arena Wealth Management"]
}

CORE_TICKERS = {
    "Alaris": ["Alaris Equity Partners", "AD.TO"],
    "Bridgemarq": ["Bridgemarq Real Estate Services", "BRE.TO"],
    "Canaccord": ["Canaccord Genuity", "CF.TO"],
    "Diversified Royalty": ["Diversified Royalty Corp", "DIV.TO"],
    "Dominion Lending": ["Dominion Lending Centres", "DLCG.TO"],
    "Exchange Income": ["Exchange Income", "EIF.TO"],
    "Fairfax": ["Fairfax Financial Holdings", "FFH.TO"],
    "goeasy": ["goeasy Ltd", "GSY.TO"],
    "Propel": ["Propel Holdings", "PRL.TO"],
    "RFA Financial": ["RFA Financial Inc", "RFA.TO"],
    "Trisura": ["Trisura Group", "TSU.TO"],
    "Versabank": ["VersaBank", "VSB.TO"],
    "Westaim": ["Westaim Corporation", "WED.TO"]
}

# --- 2. SOURCE CLASSIFICATION ---
CREDIBLE_KEYWORDS = [
    "Bloomberg", "Reuters", "Globe and Mail", "Financial Post", "CNBC", "Yahoo Finance", 
    "The Star", "BNN", "Wall Street Journal", "WSJ", "Barron's", "Financial Times", 
    "Associated Press", "AP", "Canadian Press", "GlobeNewswire", "CNW Group", 
    "PR Newswire", "Business Wire", "BusinessWire", "Accesswire", "Newsfile", "Marketwired",
    "Morningstar", "Barchart", "Seeking Alpha", "MarketWatch", "Newswire", "TMX"
]

SOCIAL_KEYWORDS = ["Twitter", "X.com", "Reddit", "Stocktwits", "Facebook", "LinkedIn", "YouTube"]

def classify_source(source_name):
    if not source_name: return "Other"
    source_lower = str(source_name).lower()
    if any(k.lower() in source_lower for k in CREDIBLE_KEYWORDS):
        return "Credible"
    if any(k.lower() in source_lower for k in SOCIAL_KEYWORDS):
        return "Social Media"
    return "Other"

# --- 3. THE SCANNER ---
def get_google_news(company_name, use_exact=False):
    search_term = f'"{company_name}"' if use_exact else company_name
    query = quote(f'{search_term} when:14d')
    url = f"https://news.google.com/rss/search?q={query}&hl=en-CA&gl=CA&ceid=CA:en"
    
    if hasattr(ssl, '_create_unverified_context'):
        ssl._create_default_https_context = ssl._create_unverified_context
        
    feed = feedparser.parse(url)
    results = []
    
    for entry in feed.entries[:20]: # Keep the 20 result buffer
        parsed_date = entry.get('published_parsed')
        sort_date = datetime(*parsed_date[:6]) if parsed_date else datetime(1900, 1, 1)
        
        source = "Google News"
        if hasattr(entry, 'source'):
            source = entry.source.get('title', 'Google News')
        elif " - " in entry.title:
            source = entry.title.split(" - ")[-1]
        
        results.append({
            "sort_key": sort_date,
            "Date": sort_date.strftime('%b %d, %Y'),
            "Company": company_name,
            "Source": source,
            "Category": classify_source(source),
            "Headline": entry.title, 
            "Link": entry.link
        })
    return results

# --- 4. STREAMLIT UI ---
st.set_page_config(page_title="DivFin News Screener", page_icon="📈", layout="wide")

if 'news_data' not in st.session_state:
    st.session_state.news_data = []

with st.sidebar:
    LOGO_URL = "https://cormark.com/Portals/_default/Skins/Cormark/Images/Cormark_4C_183x42px.png"
    st.image(LOGO_URL)
    st.title("Screener Settings")
    
    dropdown_options = ["--- MASTER VIEWS ---", "Core Coverage (All Parents)", "Full Universe (Everything)"]
    dropdown_options += ["--- INDIVIDUAL PARENTS ---"] + sorted(list(CORE_TICKERS.keys()))
    dropdown_options += ["--- SUBSIDIARY GROUPS ---"] + sorted([f"{k} Subs" for k in SUBS_MAP.keys()])
    
    selected_view = st.selectbox("Select Watchlist", options=dropdown_options)
    
    st.divider()
    st.subheader("Filter by Source Tier")
    show_credible = st.checkbox("Credible / Newswires", value=True)
    show_social = st.checkbox("Social Media", value=False)
    show_other = st.checkbox("Other Sources", value=False)
    
    st.divider()
    keyword_filter = st.text_input("🔍 Search Headlines", "").strip().lower()

st.title("DivFin News Screener")

# Building the task list
search_tasks = []
if selected_view == "Core Coverage (All Parents)":
    search_tasks = [(item, False) for sublist in CORE_TICKERS.values() for item in sublist]
elif selected_view == "Full Universe (Everything)":
    search_tasks += [(item, False) for sublist in CORE_TICKERS.values() for item in sublist]
    search_tasks += [(item, True) for sublist in SUBS_MAP.values() for item in sublist]
elif selected_view in CORE_TICKERS:
    search_tasks = [(item, False) for item in CORE_TICKERS[selected_view]]
elif selected_view.replace(" Subs", "") in SUBS_MAP:
    search_tasks = [(item, True) for item in SUBS_MAP[selected_view.replace(" Subs", "")]]

is_valid_selection = not selected_view.startswith("---")

if is_valid_selection:
    if st.button(f"Search {selected_view}", use_container_width=True):
        all_hits = []
        with st.spinner(f'Searching {len(search_tasks)} terms...'):
            with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
                future_to_company = {executor.submit(get_google_news, name, is_sub): name for name, is_sub in search_tasks}
                for future in concurrent.futures.as_completed(future_to_company):
                    all_hits.extend(future.result())
        st.session_state.news_data = all_hits

# --- 5. CATEGORY FILTERING LOGIC ---
if st.session_state.news_data:
    df = pd.DataFrame(st.session_state.news_data)
    
    # Keeping duplicates as requested in that specific version
    df = df.sort_values(by="sort_key", ascending=False)
    
    allowed_categories = []
    if show_credible: allowed_categories.append("Credible")
    if show_social: allowed_categories.append("Social Media")
    if show_other: allowed_categories.append("Other")
    
    df = df[df['Category'].isin(allowed_categories)]
    
    if keyword_filter:
        df = df[df['Headline'].str.lower().str.contains(keyword_filter)]

    st.success(f"Displaying {len(df)} headlines.")
    st.dataframe(
        df[["Date", "Company", "Category", "Source", "Headline", "Link"]], 
        column_config={"Link": st.column_config.LinkColumn("View", display_text="Open")},
        use_container_width=True, 
        hide_index=True
    )
else:
    st.info("Select a watchlist and click Search.")
