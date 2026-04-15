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
        # Corporate & Leadership
        "Exchange Income Corp", "EIF.TO", "Mike Pyle", "Adam Terwin", "Jake Trainor",
        # Aviation Segment (Air Operators & Aerospace)
        "Canadian North", "PAL Aerospace", "PAL Airlines", "Perimeter Aviation", 
        "Calm Air", "Bearskin Airlines", "Keewatin Air", "Regional One", 
        "Custom Helicopters", "Moncton Flight College", "Newfoundland Helicopters", 
        "Air Borealis", "Mach2", "BC Medevac",
        # Manufacturing Segment
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
    
   "All": ["Alaris", "Alaris Equity Partners", "3E, LLC", "Accscient, LLC", "Amur Financial Group Inc.", "Berg Demo Holdings, LLC", "Body Contour Centers, LLC (SonoBello)", "Carey Electric Contracting, LLC", 
               "Cresa, LLC", "DNT Construction, LLC", "Edgewater Technical Associates, LLC", "Fleet Advantage, LLC", "Federal Management Partners, LLC (FMP)", "GWM Holdings, Inc. (GlobalWide Media)", 
               "Heritage Restoration, LLC", "Kubik, LP", "LMS Reinforcing Steel Group", "McCoy Roofing Holdings LLC", "Ohana Growth Partners, LLC", "Optimus SBR", 
               "Professional Electric Contractors of Connecticut, Inc. (PEC)", "Sagamore Plumbing and Heating LLC", "SCR Mining & Tunnelling L.P.", "The Shipyard, LLC", "Unify Consulting, LLC", 
               "Vehicle Leasing Holdings, LLC (D&M Leasing)", "3E", "Accscient", "Amur", "Berg Demo", "SonoBello", "Carey Electric", "Cresa", "DNT", "Edgewater", "Fleet Advantage", "FMP", "GlobalWide", 
               "Heritage", "Kubik", "LMS", "McCoy Roofing", "Ohana", "Optimus SBR", "PEC", "Sagamore", "SCR", "The Shipyard", "Unify", "D&M Leasing",
           "Bridgemarq Real Estate Services", "BRE.TO", "Royal LePage", "Proprio Direct", "Via Capitale", "Spencer Enright", "Phil Soper", "Johnston & Daniel",
           "Canaccord Genuity", "CF.TO", "Dan Daviau", "Canaccord Wealth Management", "Sawaya Partners", "Questrade partner", "Canaccord Genuity Group",
           "Diversified Royalty Corp", "DIV.TO", "Sean Morrison", "Mr. Lube", "Air Miles", "Sutton Group", "Nurse Next Door", "Oxford Learning", "BarBurrito", "Cheba Hut", "Mr. Mikes",
           "Dominion Lending Centres", "DLCG.TO", "Gary Mauris", "Mortgage Architects", "MCC Mortgage Centre", "Newton Connectivity", "Chris Kayat",
           "Exchange Income Corp", "EIF.TO", "Mike Pyle", "Adam Terwin", "Jake Trainor",
               "Canadian North", "PAL Aerospace", "PAL Airlines", "Perimeter Aviation", 
                "Calm Air", "Bearskin Airlines", "Keewatin Air", "Regional One", 
                "Custom Helicopters", "Moncton Flight College", "Newfoundland Helicopters", 
                "Air Borealis", "Mach2", "BC Medevac",
                "Northern Mat and Bridge", "Spartan Mat", "Spartan Composites", 
                "WesTower Communications", "Quest Window Systems", "BVGlazing Systems", 
                "Ben Machine Products", "Stainless Fabrication", "DryAir Manufacturing", 
                "Hansen Industries", "Overlanders Manufacturing", "LV Control Mfg", 
                "Water Blast Manufacturing", "Duhamel Sawmill",
           "Fairfax Financial Holdings", "FFH.TO", "Prem Watsa", "Odyssey Group", "Allied World", "Northbridge Financial", "Crum & Forster", "Brit Insurance",
           "goeasy Ltd", "GSY.TO", "Jason Mullins", "easyfinancial", "easyhome", "LendCare",
           "Propel Holdings", "PRL.TO", "Clive Kinross", "CreditFresh", "MoneyKey", "Fora Credit", "QuidMarket", "FreshLine",
           "RFA Financial Inc", "RFA.TO", "RFA Bank of Canada", "RFA Mortgage", "RFA REIT", "Holloway Lodging",
           "Trisura Group", "TSU.TO", "David Clare", "Trisura Guarantee Insurance", "Trisura Specialty", "Chris Sekine",
           "VersaBank", "VSB.TO", "David Taylor", "DRT Cyber", "Structured Receivable",
           "Westaim Corporation", "WED.TO", "Cameron MacDonald", "Skyward Specialty", "Arena Investors", "Arena Wealth Management",
           ],
}

# --- SOURCE CATEGORIES ---
# 1. Credible/White Label Sources
CREDIBLE_SOURCES = [
    "The Globe and Mail", "Bloomberg", "Reuters", "Financial Post", "CNBC", 
    "Yahoo Finance", "The Wall Street Journal", "WSJ", "Barron's", "Forbes", 
    "Financial Times", "MarketWatch", "GlobeNewswire", "PR Newswire", "Business Wire",
    "Canada Newswire", "Cision"]

# 2. Social Media & Blogs
SOCIAL_SOURCES = [
    "Twitter", "X.com", "LinkedIn", "Facebook", "Truth Social", "Reddit", 
    "Substack", "Medium", "StockTwits", "Instagram"]

LOGO_URL = "https://cormark.com/Portals/_default/Skins/Cormark/Images/Cormark_4C_183x42px.png"

st.set_page_config(page_title="DivFin News Screener", page_icon=LOGO_URL, layout="wide")
st.logo(LOGO_URL, link="https://cormark.com/")

if 'news_data' not in st.session_state:
    st.session_state.news_data = []

# --- 2. SIDEBAR: CATEGORY-BASED FILTERING ---
with st.sidebar:
    st.title("DivFin Settings")
    selected_group = st.selectbox("Watchlist Category", options=list(WATCHLIST_GROUPS.keys()))
    
    st.divider()
    st.header("Source Filters")
    
    # Toggle Categories
    show_credible = st.checkbox("⭐ Show Credible Sources", value=True, help="Bloomberg, Reuters, Globe & Mail, etc.")
    show_social = st.checkbox("📱 Show Social Media & Blogs", value=False, help="Twitter/X, LinkedIn, Substack, etc.")
    show_other = st.checkbox("🌑 Show All Other Sources", value=False, help="Automatically filtered/unverified sources.")

    st.divider()
    keyword_filter = st.text_input("🔍 Search Headlines", "").strip().lower()

# --- 3. THE SCANNER ---
def get_google_news(company_name, watchlist_names):
    # 1. Prepare search terms
    # We want "Alaris Equity Partners" -> "Alaris" for the validation check
    core_name = company_name.split(',')[0].split(' Inc')[0].split(' LLC')[0].strip()
    # If the name is long, take the first two words (e.g., "Heritage Restoration")
    short_name = " ".join(core_name.split()[:2]) 

    # Search query: We'll use the short name to get more results
    query = quote(f'"{short_name}" when:7d')
    url = f"https://news.google.com/rss/search?q={query}&hl=en-CA&gl=CA&ceid=CA:en"
    
    # 2. TECHNICAL FIX: Properly handle SSL for Streamlit/Linux servers
    try:
        ssl_context = ssl._create_unverified_context()
        with urllib.request.urlopen(url, context=ssl_context) as response:
            raw_data = response.read()
        feed = feedparser.parse(raw_data)
    except Exception as e:
        st.error(f"Error fetching feed for {company_name}: {e}")
        return []

    results = []
    
    for entry in feed.entries[:15]: # Increased limit to 15 to account for filtering
        headline = entry.title
        source_name = entry.source.get('title', 'Unknown')
        
        # 3. SMARTER VALIDATION: 
        # We check if the 'short_name' (e.g., Alaris) is in the headline.
        # This prevents skipping "Alaris" news just because "Equity Partners" wasn't written.
        if short_name.lower() not in headline.lower():
            continue

        # 4. CATEGORIZATION
        category = "Other"
        
        # Check premium list
        is_premium = any(s.lower() in source_name.lower() for s in CREDIBLE_SOURCES)
        
        # Check if the source name matches any part of our watchlist companies
        is_corporate_site = any(short_name.lower() in source_name.lower() for c in watchlist_names)
        
        # Extra check: If it's a major .com news source, it's likely credible
        if is_premium or is_corporate_site:
            category = "Credible"
        elif any(s.lower() in source_name.lower() for s in SOCIAL_SOURCES):
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
    
# --- 4. MAIN UI & LOGIC ---
st.title("DivFin News Screener")
st.subheader(f"Current Watchlist: {selected_group}")

if st.button(f"Search {selected_group} List", use_container_width=True):
    all_hits = []
    # Use a set to avoid searching duplicate names (like "Alaris" and "Alaris Equity Partners")
    # We filter out very short strings to avoid "noise"
    search_list = sorted(list(set(WATCHLIST_GROUPS[selected_group])))
    
    with st.spinner('Gathering intelligence...'):
        for company in search_list:
            hits = get_google_news(company, search_list)
            all_hits.extend(hits)
            
    if not all_hits:
        st.warning("No news found for this timeframe. Try a broader category.")
    else:
        st.session_state.news_data = all_hits
    
if st.session_state.news_data:
    df = pd.DataFrame(st.session_state.news_data).sort_values(by="sort_key", ascending=False)
    
    # --- APPLY CATEGORY FILTERS ---
    allowed_categories = []
    if show_credible: allowed_categories.append("Credible")
    if show_social: allowed_categories.append("Social")
    if show_other: allowed_categories.append("Other")
    
    df = df[df['Category'].isin(allowed_categories)]
    
    # Keyword filter
    if keyword_filter:
        df = df[df['Headline'].str.lower().str.contains(keyword_filter)]

    st.success(f"Showing {len(df)} curated headlines.")
    
    # Color-coding the category for better UX
    def color_category(val):
        color = '#2ecc71' if val == 'Credible' else '#e67e22' if val == 'Social' else '#95a5a6'
        return f'color: {color}; font-weight: bold'

    st.dataframe(
        df[["Date", "Company", "Source", "Category", "Headline", "Link"]], 
        column_config={
            "Link": st.column_config.LinkColumn("View Article"),
            "Category": st.column_config.TextColumn("Type")
        },
        use_container_width=True, 
        hide_index=True
    )
