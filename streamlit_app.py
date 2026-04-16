import streamlit as st
import feedparser
import pandas as pd
from urllib.parse import quote
import ssl
from datetime import datetime
import concurrent.futures

# --- 1. DATA STRUCTURE ---
# Define the subsidiaries separately so we can map them to parents easily
SUBS_MAP = {
    "Alaris": ["3E, LLC", "Accscient, LLC", "Amur Financial Group", "SonoBello", "Cresa, LLC", "DNT Construction", "Edgewater Technical Associates", "Fleet Advantage", 
               "Federal Management Partners", "GlobalWide Media", "Heritage Restoration", "Kubik, LP", "LMS Reinforcing Steel", "McCoy Roofing", "Ohana Growth Partners", 
               "Optimus SBR", "Professional Electric Contractors", "Sagamore Plumbing", "SCR Mining & Tunnelling", "The Shipyard, LLC", "Unify Consulting", "D&M Leasing"],
    
    "Exchange Income": ["Canadian North", "PAL Aerospace", "PAL Airlines", "Perimeter Aviation", "Calm Air", "Bearskin Airlines", "Keewatin Air", "Regional One", 
                        "Custom Helicopters", "Moncton Flight College", "Newfoundland Helicopters", "Air Borealis", "Mach2", "BC Medevac", "Northern Mat and Bridge", 
                        "Spartan Mat", "WesTower Communications", "Quest Window Systems", "BVGlazing Systems", "Ben Machine Products", "Stainless Fabrication", 
                        "DryAir Manufacturing", "Hansen Industries", "Overlanders Manufacturing", "LV Control Mfg", "Water Blast Manufacturing", "Duhamel Sawmill"],
    
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
    "Exchange Income": ["Exchange Income Corp", "EIF.TO"],
    "Fairfax": ["Fairfax Financial Holdings", "FFH.TO"],
    "goeasy": ["goeasy Ltd", "GSY.TO"],
    "Propel": ["Propel Holdings", "PRL.TO"],
    "RFA Financial": ["RFA Financial Inc", "RFA.TO"],
    "Trisura": ["Trisura Group", "TSU.TO"],
    "Versabank": ["VersaBank", "VSB.TO"],
    "Westaim": ["Westaim Corporation", "WED.TO"]
}

# Build the selection options for the dropdown
dropdown_options = ["--- MASTER VIEWS ---", "Core Coverage (All Parents)", "Full Universe (Everything)"]
dropdown_options += ["--- INDIVIDUAL PARENTS ---"] + sorted(list(CORE_TICKERS.keys()))
dropdown_options += ["--- SUBSIDIARY GROUPS ---"] + sorted([f"{k} Subs" for k in SUBS_MAP.keys()])

DEFAULT_BLACKLIST = ["MarketBeat", "Simply Wall St", "Zacks Investment Research", "Stock Traders Daily", "Defense World", "Best Stocks"]

LOGO_URL = "https://cormark.com/Portals/_default/Skins/Cormark/Images/Cormark_4C_183x42px.png"

st.set_page_config(page_title="DivFin News Screener", page_icon="📈", layout="wide")

# --- 2. THE SCANNER ---
def get_google_news(company_name):
    query = quote(f'{company_name} when:7d')
    url = f"https://news.google.com/rss/search?q={query}&hl=en-CA&gl=CA&ceid=CA:en"
    
    if hasattr(ssl, '_create_unverified_context'):
        ssl._create_default_https_context = ssl._create_unverified_context
        
    feed = feedparser.parse(url)
    results = []
    for entry in feed.entries[:10]:
        parsed_date = entry.get('published_parsed')
        sort_date = datetime(*parsed_date[:6]) if parsed_date else datetime(1900, 1, 1)
        
        results.append({
            "sort_key": sort_date,
            "Date": sort_date.strftime('%b %d, %Y'),
            "Company": company_name,
            "Source": entry.source.get('title', 'Google News'), # Extracts publisher name
            "Headline": entry.title, # Raw headline from feed
            "Link": entry.link
        })
    return results

# --- 3. UI LAYOUT & SIDEBAR ---
if 'news_data' not in st.session_state:
    st.session_state.news_data = []

with st.sidebar:
    st.image(LOGO_URL)
    st.title("DivFin Settings")
    selected_group = st.selectbox("Watchlist Category", options=list(WATCHLIST_GROUPS.keys()))
    
    st.divider()
    
    available_sources = sorted(list(set([item['Source'] for item in st.session_state.news_data]))) if st.session_state.news_data else []
    
    whitelist = st.multiselect("⭐ Whitelist (Show ONLY):", options=available_sources)
    
    present_blacklist = [s for s in DEFAULT_BLACKLIST if s in available_sources]
    blacklist = st.multiselect("🚫 Blacklist (Always Hide):", options=available_sources, default=present_blacklist)

    st.divider()
    keyword_filter = st.text_input("🔍 Search Headlines", "").strip().lower()

# --- 4. MAIN LOGIC ---
st.title("DivFin News Screener")

if st.button(f"Search {selected_group} List", use_container_width=True):
    all_hits = []
    
    if selected_group == "All":
        items_to_search = [item for group_name, group_list in WATCHLIST_GROUPS.items() if group_name != "All" for item in group_list]
    else:
        items_to_search = WATCHLIST_GROUPS[selected_group]

    with st.spinner('Gathering intelligence...'):
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            future_to_company = {executor.submit(get_google_news, comp): comp for comp in items_to_search}
            for future in concurrent.futures.as_completed(future_to_company):
                all_hits.extend(future.result())
                
    st.session_state.news_data = all_hits

if st.session_state.news_data:
    df = pd.DataFrame(st.session_state.news_data)
    
    df = df.drop_duplicates(subset=['Link'])
    df = df.sort_values(by="sort_key", ascending=False)
    
    if whitelist:
        df = df[df['Source'].isin(whitelist)]
    if blacklist:
        df = df[~df['Source'].isin(blacklist)]
    
    if keyword_filter:
        df = df[df['Headline'].str.lower().str.contains(keyword_filter)]

    st.success(f"Curated {len(df)} headlines for your review.")
    st.dataframe(
        df[["Date", "Company", "Source", "Headline", "Link"]], 
        column_config={
            "Link": st.column_config.LinkColumn("View", display_text="Open")
        },
        use_container_width=True, 
        hide_index=True
    )
