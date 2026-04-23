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
    "Dominion Lending": ["Mortgage Architects", "MCC Mortgage Centre", "Newton Connectivity", "DLC Group"],
    "Fairfax": ["Odyssey Group", "Allied World", "Northbridge Financial", "Crum & Forster", "Brit Insurance"],
    "goeasy": ["easyfinancial", "easyhome", "LendCare"],
    "Propel": ["CreditFresh", "MoneyKey", "Fora Credit", "QuidMarket", "FreshLine"],
    "Trisura": ["Trisura Guarantee Insurance", "Trisura Specialty"],
    "Versabank": ["DRT Cyber", "Structured Receivable"],
    "Westaim": ["Skyward Specialty", "Arena Investors", "Arena Wealth Management"]
}

CORE_TICKERS = {
    # Expanded Alaris keywords to ensure press releases aren't filtered
    "Alaris": ["Alaris Equity Partners", "Alaris", "TSX:AD", "AD.UN", "AD.TO"],
    "Bridgemarq": ["Bridgemarq", "BRE.TO"],
    "Canaccord": ["Canaccord", "CF.TO"],
    "Diversified Royalty": ["Diversified Royalty", "DIV.TO", "DIV"],
    "Dominion Lending": ["Dominion Lending Centres", "DLCG.TO", "DLC Group", "DLCG"],
    "Exchange Income": ["Exchange Income", "EIF.TO", "EIF"],
    "Fairfax": ["Fairfax Financial", "FFH.TO"],
    "goeasy": ["goeasy", "GSY.TO"],
    "Propel": ["Propel Holdings", "PRL.TO"],
    "RFA Financial": ["RFA Financial", "RFA.TO"],
    "Trisura": ["Trisura", "TSU.TO"],
    "Versabank": ["VersaBank", "VSB.TO"],
    "Westaim": ["Westaim", "WED.TO"]
}

# --- 2. SOURCE CLASSIFICATION ---
# Added broader newswire and press release terms
CREDIBLE_KEYWORDS = [
    "Bloomberg", "Reuters", "Globe and Mail", "Financial Post", "CNBC", "Yahoo Finance", 
    "The Star", "BNN", "Wall Street Journal", "WSJ", "Barron's", "Financial Times", 
    "Associated Press", "AP", "Canadian Press", "GlobeNewswire", "Globe Newswire", 
    "CNW Group", "PR Newswire", "Business Wire", "BusinessWire", "Accesswire", 
    "Newsfile", "Marketwired", "Morningstar", "Barchart", "Seeking Alpha", 
    "MarketWatch", "Newswire", "TMX", "Press Release"
]

NON_CREDIBLE_SOURCES = ["magaproject", "coinmarketcap", "iowa capital dispatch", "crypto", "bitcoin", "blockchain", "investing.com"]

def classify_source(source_name, company_name=""):
    if not source_name: return "Other"
    source_lower = str(source_name).lower()
    
    # 1. Filter junk first
    if any(junk in source_lower for junk in NON_CREDIBLE_SOURCES):
        return "Other"
    
    # 2. Check if the source is the company itself (High Signal)
    if company_name and company_name.lower() in source_lower:
        return "Credible"
    
    # 3. Check official credible keywords
    if any(k.lower() in source_lower for k in CREDIBLE_KEYWORDS):
        return "Credible"
    
    # 4. Social Media
    if any(social in source_lower for social in ["twitter", "x.com", "reddit", "stocktwits", "facebook"]):
        return "Social Media"
    
    return "Other"

# --- 3. THE SCANNER ---
def get_google_news(search_term, display_name, validation_list):
    query = quote(f'{search_term} when:14d')
    url = f"https://news.google.com/rss/search?q={query}&hl=en-CA&gl=CA&ceid=CA:en"
    
    if hasattr(ssl, '_create_unverified_context'):
        ssl._create_default_https_context = ssl._create_unverified_context
        
    feed = feedparser.parse(url)
    results = []
    
    for entry in feed.entries[:30]:
        headline = entry.title
        headline_lower = headline.lower()
        
        # HEADLINE VALIDATION: Precise name-in-title check
        if not any(val.lower() in headline_lower for val in validation_list):
            continue

        parsed_date = entry.get('published_parsed')
        sort_date = datetime(*parsed_date[:6]) if parsed_date else datetime(1900, 1, 1)
        
        source = "Google News"
        if hasattr(entry, 'source'):
            source = entry.source.get('title', 'Google News')
        elif " - " in headline:
            source = headline.split(" - ")[-1]
        
        results.append({
            "sort_key": sort_date,
            "Date": sort_date.strftime('%b %d, %Y'),
            "Company": display_name,
            "Source": source,
            "Category": classify_source(source, display_name), # Pass company name to validation
            "Headline": headline, 
            "Link": entry.link
        })
    return results

# --- 4. UI ---
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
    
    is_subs_selected = selected_view.endswith(" Subs")
    
    st.subheader("Filter by Source Tier")
    show_credible = st.checkbox("Credible / Newswires", value=True)
    show_social = st.checkbox("Social Media", value=is_subs_selected)
    show_other = st.checkbox("Other Sources", value=is_subs_selected)
    
    st.divider()
    keyword_filter = st.text_input("🔍 Search Headlines", "").strip().lower()

st.title("DivFin News Screener")

search_tasks = []
if selected_view == "Core Coverage (All Parents)":
    for parent, terms in CORE_TICKERS.items():
        for t in terms: search_tasks.append((t, parent, CORE_TICKERS[parent]))

elif selected_view == "Full Universe (Everything)":
    for parent, terms in CORE_TICKERS.items():
        for t in terms: search_tasks.append((t, parent, CORE_TICKERS[parent]))
    for parent, subs in SUBS_MAP.items():
        for s in subs: search_tasks.append((s, s, [s]))

elif selected_view in CORE_TICKERS:
    for t in CORE_TICKERS[selected_view]: 
        search_tasks.append((t, selected_view, CORE_TICKERS[selected_view]))

elif selected_view.endswith(" Subs"):
    p_name = selected_view.replace(" Subs", "")
    if p_name in SUBS_MAP:
        for s in SUBS_MAP[p_name]: 
            search_tasks.append((s, s, [s]))

# --- EXECUTION ---
if not selected_view.startswith("---"):
    if st.button(f"Search {selected_view}", use_container_width=True):
        all_hits = []
        with st.spinner(f'Searching {selected_view}...'):
            with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
                future_to_company = {executor.submit(get_google_news, task[0], task[1], task[2]): task[0] for task in search_tasks}
                for future in concurrent.futures.as_completed(future_to_company):
                    all_hits.extend(future.result())
        st.session_state.news_data = all_hits

# --- DISPLAY ---
if st.session_state.news_data:
    df = pd.DataFrame(st.session_state.news_data)
    df = df.sort_values(by="sort_key", ascending=False)
    
    allowed_categories = []
    if show_credible: allowed_categories.append("Credible")
    if show_social: allowed_categories.append("Social Media")
    if show_other: allowed_categories.append("Other")
    
    df = df[df['Category'].isin(allowed_categories)]
    
    if keyword_filter:
        df = df[df['Headline'].str.lower().str.contains(keyword_filter)]

    st.success(f"Found {len(df)} headlines.")
    st.dataframe(
        df[["Date", "Company", "Category", "Source", "Headline", "Link"]], 
        column_config={"Link": st.column_config.LinkColumn("View", display_text="Open")},
        use_container_width=True, 
        hide_index=True
    )
