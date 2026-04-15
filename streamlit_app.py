import streamlit as st
import feedparser
import pandas as pd
from urllib.parse import quote
import ssl
from datetime import datetime
import urllib.request

# --- 1. CONFIGURATION ---
WATCHLIST_GROUPS = {
    "Alaris": ["Alaris", "Alaris Equity Partners", "3E, LLC", "Accscient, LLC", "Amur Financial Group Inc.", "Berg Demo Holdings, LLC", "Body Contour Centers, LLC (SonoBello)", "Carey Electric Contracting, LLC", 
               "Cresa, LLC", "DNT Construction, LLC", "Edgewater Technical Associates, LLC", "Fleet Advantage, LLC", "Federal Management Partners, LLC (FMP)", "GWM Holdings, Inc. (GlobalWide Media)", 
               "Heritage Restoration, LLC", "Kubik, LP", "LMS Reinforcing Steel Group", "McCoy Roofing Holdings LLC", "Ohana Growth Partners, LLC", "Optimus SBR", 
               "Professional Electric Contractors of Connecticut, Inc. (PEC)", "Sagamore Plumbing and Heating LLC", "SCR Mining & Tunnelling L.P.", "The Shipyard, LLC", "Unify Consulting, LLC", 
               "Vehicle Leasing Holdings, LLC (D&M Leasing)"],
    
    "Bridgemarq (BRE)": ["Bridgemarq Real Estate Services", "BRE.TO", "Royal LePage", "Proprio Direct", "Via Capitale", "Spencer Enright", "Phil Soper", "Johnston & Daniel"],
    
    "Canaccord (CF)": ["Canaccord Genuity", "CF.TO", "Dan Daviau", "Canaccord Wealth Management", "Sawaya Partners", "Questrade partner", "Canaccord Genuity Group"],
    
    "Diversified Royalties (DIV)": ["Diversified Royalty Corp", "DIV.TO", "Sean Morrison", "Mr. Lube", "Air Miles", "Sutton Group", "Nurse Next Door", "Oxford Learning", "BarBurrito", "Cheba Hut", "Mr. Mikes"],
    
    "Dominion Lending (DLCG)": ["Dominion Lending Centres", "DLCG.TO", "Gary Mauris", "Mortgage Architects", "MCC Mortgage Centre", "Newton Connectivity", "Chris Kayat"],
    
    "Exchange Income (EIF)": [
        "Exchange Income Corp", "EIF.TO", "Mike Pyle", "Adam Terwin", "Jake Trainor",
        "Canadian North", "PAL Aerospace", "PAL Airlines", "Perimeter Aviation", 
        "Calm Air", "Bearskin Airlines", "Keewatin Air", "Regional One", 
        "Custom Helicopters", "Moncton Flight College", "Newfoundland Helicopters", 
        "Air Borealis", "Mach2", "BC Medevac",
        "Northern Mat and Bridge", "Spartan Mat", "Spartan Composites", 
        "WesTower Communications", "Quest Window Systems", "BVGlazing Systems", 
        "Ben Machine Products", "Stainless Fabrication", "DryAir Manufacturing", 
        "Hansen Industries", "Overlanders Manufacturing", "LV Control Mfg", 
        "Water Blast Manufacturing", "Duhamel Sawmill"
    ],
    
    "Fairfax (FFH)": ["Fairfax Financial Holdings", "FFH.TO", "Prem Watsa", "Odyssey Group", "Allied World", "Northbridge Financial", "Crum & Forster", "Brit Insurance"],
    "goeasy (GSY)": ["goeasy Ltd", "GSY.TO", "Jason Mullins", "easyfinancial", "easyhome", "LendCare"],
    "Propel (PRL)": ["Propel Holdings", "PRL.TO", "Clive Kinross", "CreditFresh", "MoneyKey", "Fora Credit", "QuidMarket", "FreshLine"],
    "RFA Financial (RFA)": ["RFA Financial Inc", "RFA.TO", "RFA Bank of Canada", "RFA Mortgage", "RFA REIT", "Holloway Lodging"],
    "Trisura (TSU)": ["Trisura Group", "TSU.TO", "David Clare", "Trisura Guarantee Insurance", "Trisura Specialty", "Chris Sekine"],
    "Versabank (VSB)": ["VersaBank", "VSB.TO", "David Taylor", "DRT Cyber", "Structured Receivable"],
    "Westaim (WED)": ["Westaim Corporation", "WED.TO", "Cameron MacDonald", "Skyward Specialty", "Arena Investors", "Arena Wealth Management"],
    
    "All": ["Alaris", "Bridgemarq", "Canaccord", "Diversified Royalty", "Dominion Lending", "Exchange Income", "Fairfax", "goeasy", "Propel", "RFA Financial", "Trisura", "VersaBank", "Westaim"]
}

PRIMARY_TICKERS = [
    "Alaris", "Bridgemarq", "Canaccord", "Diversified", "Dominion", 
    "Exchange Income", "Fairfax", "goeasy", "Propel", "RFA", 
    "Trisura", "Versabank", "Westaim"
]

# --- 1. BRAND-BASED CREDIBLE SOURCES ---
# Using keywords rather than full phrases to ensure "Yahoo! Finance" etc are caught
CREDIBLE_KEYWORDS = [
    "globe", "bloomberg", "reuter", "financial post", "cnbc", "yahoo", 
    "wsj", "wall street", "barron", "forbes", "marketwatch", "newswire", 
    "cision", "accesswire", "newsfile", "press", "official"
]

SOCIAL_SOURCES = ["twitter", "x.com", "linkedin", "facebook", "truth social", "reddit", "substack", "medium"]

LOGO_URL = "https://cormark.com/Portals/_default/Skins/Cormark/Images/Cormark_4C_183x42px.png"

st.set_page_config(page_title="DivFin News Screener", page_icon=LOGO_URL, layout="wide")
st.logo(LOGO_URL, link="https://cormark.com/")

if 'news_data' not in st.session_state:
    st.session_state.news_data = []

# --- 2. SIDEBAR ---
with st.sidebar:
    st.title("DivFin Settings")
    selected_group = st.selectbox("Watchlist Category", options=list(WATCHLIST_GROUPS.keys()))
    
    st.divider()
    st.header("Source Filters")
    show_credible = st.checkbox("⭐ Show Credible (Yahoo, Globe, Wires)", value=True)
    show_social = st.checkbox("📱 Show Social Media & Blogs", value=False)
    show_other = st.checkbox("🌑 Show All Other Sources", value=False)

    st.divider()
    keyword_filter = st.text_input("🔍 Search Headlines", "").strip().lower()

# --- 3. THE SCANNER ---
def get_google_news(company_name, watchlist_names):
    is_primary = any(ticker.lower() in company_name.lower() for ticker in PRIMARY_TICKERS)
    clean_name = company_name.replace(", LLC", "").replace(" LLC", "").replace(", Inc.", "").replace(" Inc.", "")
    
    # 1. SEARCH STRATEGY: Broad for parents, quoted for subsidiaries
    if is_primary:
        query = quote(f'{clean_name} when:7d')
    else:
        query = quote(f'"{clean_name}" when:7d')
    
    url = f"https://news.google.com/rss/search?q={query}&hl=en-CA&gl=CA&ceid=CA:en"
    
    try:
        ssl_context = ssl._create_unverified_context()
        with urllib.request.urlopen(url, context=ssl_context) as response:
            raw_data = response.read()
        feed = feedparser.parse(raw_data)
    except:
        return []

    results = []
    # Increased limit to 40 to ensure we catch all sources
    for entry in feed.entries[:20]:
        headline = entry.title
        source_name = entry.source.get('title', 'Unknown')
        snippet = entry.get('summary', '').lower()
        
        # 2. VALIDATION (LOOSENED)
        # If it's a primary company, we skip validation and trust Google's relevance.
        # If it's a subsidiary, we check if the name is in the headline OR the snippet.
        if not is_primary:
            if clean_name.lower() not in headline.lower() and clean_name.lower() not in snippet:
                continue

        # 3. CATEGORIZATION
        category = "Other"
        source_lower = source_name.lower()
        
        # Check Brand Keywords (Yahoo, Globe, etc)
        is_premium = any(kw in source_lower for kw in CREDIBLE_KEYWORDS)
        
        # Check Corporate (Matches anything in our watchlist)
        is_corporate = any(name.lower() in source_lower for name in watchlist_names)
        
        if is_premium or is_corporate:
            category = "Credible"
        elif any(s in source_lower for s in SOCIAL_SOURCES):
            category = "Social"
            
        parsed_date = entry.get('published_parsed')
        sort_date = datetime(*parsed_date[:6]) if parsed_date else datetime(1900, 1, 1)
        
        results.append({
            "sort_key": sort_date,
            "Date": sort_date.strftime('%b %d, %Y'),
            "Company": company_name,
            "Source": source_name,
            "Category": category,
            "Headline": headline,
            "Link": entry.link
        })
    return results

# --- 4. MAIN UI ---
st.title("DivFin News Screener")
st.subheader(f"Current Watchlist: {selected_group}")

if st.button(f"Search {selected_group} List", use_container_width=True):
    all_hits = []
    current_watchlist = WATCHLIST_GROUPS[selected_group]
    
    with st.spinner('Gathering intelligence...'):
        for company in current_watchlist:
            all_hits.extend(get_google_news(company, current_watchlist))
    
    if all_hits:
        df_hits = pd.DataFrame(all_hits).drop_duplicates(subset=['Headline'])
        st.session_state.news_data = df_hits.to_dict('records')
    else:
        st.session_state.news_data = []

if st.session_state.news_data:
    df = pd.DataFrame(st.session_state.news_data).sort_values(by="sort_key", ascending=False)
    
    allowed = []
    if show_credible: allowed.append("Credible")
    if show_social: allowed.append("Social")
    if show_other: allowed.append("Other")
    
    df = df[df['Category'].isin(allowed)]
    
    if keyword_filter:
        df = df[df['Headline'].str.lower().str.contains(keyword_filter)]

    st.success(f"Curated {len(df)} headlines.")
    
    st.dataframe(
        df[["Date", "Company", "Source", "Category", "Headline", "Link"]], 
        column_config={
            "Link": st.column_config.LinkColumn("View"),
            "Category": st.column_config.TextColumn("Type")
        },
        use_container_width=True, 
        hide_index=True
    )
