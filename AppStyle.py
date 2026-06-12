import streamlit as st
import base64
import os

# --- DESIGN ICON REGISTRY ---
# Kept as emojis STRICTLY to keep st.set_page_config() from crashing at startup
ICONS = {
    "database": "🫥",
    "search": "😍",
    "filter": "😜",
    "visible": "😒",
    "download": "🤑",
    "file": "😎"
}

@st.cache_data(show_spinner=False)
def get_cached_base64(file_name):
    """Safely locates and reads local assets from your app directory."""
    if not file_name:
        return ""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    full_path = os.path.join(current_dir, file_name)
    
    if os.path.exists(full_path):
        try:
            with open(full_path, "rb") as f:
                return base64.b64encode(f.read()).decode()
        except Exception:
            return ""
    return ""

def get_icon_html(icon_name, size=32):
    """
    💡 THE ICON FIX: Call this function in SearchApp.py to display 
    your animated GIF files directly inline with your text headers!
    """
    file_map = {
        "database": "database.gif",
        "search": "search.gif",
        "filter": "filter.gif",
        "visible": "visible.gif",
        "download": "download.gif",
        "file": "file.gif"
    }
    
    target_file = file_map.get(icon_name, "")
    b64_str = get_cached_base64(target_file)
    
    if b64_str:
        return f'<img src="data:image/gif;base64,{b64_str}" width="{size}" style="vertical-align: middle; margin-right: 10px; margin-bottom: 4px;">'
    
    # Elegant emoji fallback if the .gif file isn't in the folder
    return f"<span style='font-size: {size}px; margin-right: 10px;'>{ICONS.get(icon_name, '')}</span>"

def inject_modern_css():
    """Injects layout overrides with a guaranteed web-safe background image fallback."""
    
    # Check if you have a local background file (supports jpg, png, or gif)
    bg_local = get_cached_base64("background.jpg") or get_cached_base64("background.gif")
    
    if bg_local:
        bg_url = f"data:image/jpeg;base64,{bg_local}"
        bg_url_1 = f"data:image/gif;base64,{bg_local}"
    else:
        bg_url = "https://plus.unsplash.com/premium_vector-1719816838907-8b4304af21e6?q=80&w=1316&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D"
        bg_url_1 = "https://media.istockphoto.com/id/1147249349/vector/beagle-in-action-seamless-pattern.jpg?s=612x612&w=0&k=20&c=vyFNQzFKxojRckU584PDEXLZIVNbDbQa0cUQRwXiaJA="
        
    st.markdown(f"""
        <style>
        /* 1. GLOBAL STREAMLIT NATIVE HEADER/FOOTER NUKE */
        header[data-testid="stHeader"] {{
            visibility: hidden !important;
            display: none !important;
            height: 0px !important;
        }}
        footer {{
            visibility: hidden !important;
            display: none !important;
        }}
        /* Strip the default forced top padding from the main wrapper container */
        [data-testid="stAppViewContainer"] {{
            padding-top: 0px !important;
        }}

        /* 2. GLOBAL SCROLLBAR OVERHAUL */
        ::-webkit-scrollbar {{
            width: 14px !important;      
            height: 14px !important;      
            display: block !important;
        }}
        ::-webkit-scrollbar-track {{
            background: #CBDCEB !important;       
            border: 2px solid #0A1931 !important;
            border-radius: 6px !important;
        }}
        ::-webkit-scrollbar-thumb {{
            background-color: #0A1931 !important;
            border-radius: 6px !important;
            border: 2px solid #CBDCEB !important; 
        }}
        ::-webkit-scrollbar-thumb:hover {{
            background-color: #7cb7f7 !important;
        }}

        /* 3. FIXED LAYOUT WITH BACKGROUND IMAGE */
        html, body, .stApp {{
            background-image: linear-gradient(rgba(230, 240, 250, 0.85), rgba(230, 240, 250, 0.85)), 
                              url('{bg_url}') !important;
            background-size: cover !important;
            background-position: center !important;
            background-repeat: no-repeat !important;
            background-attachment: fixed !important;
            color: #0A1931 !important;
            overflow-x: hidden !important;
        }}
        
        /* 4. TRUE EDGE-TO-EDGE & FIXED HEIGHT BLOCK WINDOW */
        .main .block-container {{
            max-width: 100% !important;      
            width: 100% !important;      
            margin: 0 !important;
            padding-top: 15px !important;
            padding-bottom: 0px !important;
            padding-left: 20px !important;    
            padding-right: 20px !important; 
            height: calc(100vh - 20px) !important;
            overflow: hidden !important;
            display: flex;
            flex-direction: column;
        }}

        [data-testid="stVerticalBlock"] {{
            width: 100% !important;
            flex-grow: 1;
            display: flex;
            flex-direction: column;
        }}
        
        /* 5. SIDEBAR COMPRESSION & UNIQUE BACKGROUND IMAGE WINDOW */
        [data-testid="stSidebar"] {{
            background-image: linear-gradient(rgba(203, 220, 235, 0.88), rgba(203, 220, 235, 0.88)), 
                              url('{bg_url_1}') !important;
            background-size: cover !important;
            background-position: center !important;
            background-repeat: no-repeat !important;
            background-attachment: fixed !important;
            border-right: 2px solid #0A1931 !important;
        }}

        [data-testid="stSidebarUserContent"] {{
            background-color: transparent !important; 
            padding-top: 0.25rem !important;  
        }}
        
        [data-testid="stSidebarHeader"] {{
            padding-top: 0px !important;
            padding-bottom: 0px !important;
            min-height: unset !important;     
            background-color: transparent !important;
        }}
        
        div[data-testid="stVerticalBlock"] {{
            gap: 0.35rem !important;
            row-gap: 0.35rem !important;
        }}
        [data-testid="stSidebarUserContent"] div[data-testid="stVerticalBlock"] {{
            gap: 0.4rem !important;
        }}
        
        h1 {{
            font-size: 1.8rem !important;    
            font-weight: 800 !important;
            margin-top: 0rem !important;
            margin-bottom: 0.2rem !important;
            display: flex;
            align-items: center;
        }}
        h3 {{
            font-size: 1.4rem !important;
            font-weight: 800 !important;
            color: #0A1931 !important;
            margin-top: 0rem !important;
            margin-bottom: 0.15rem !important;
            padding-top: 0rem !important;
            display: flex;
            align-items: center;
        }}
        
        hr {{
            margin-top: 0.4rem !important;
            margin-bottom: 0.4rem !important;
            border-color: #0A1931 !important;
        }}

        /* 6. BASELINE READABILITY */
        html, body, .stApp {{
            font-size: 18px !important;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
            color: #0A1931 !important;
        }}
        
        [data-testid="stWidgetLabel"] p, label p, .stMultiSelect span {{
            font-size: 1.15rem !important;
            font-weight: 700 !important;
            color: #0A1931 !important; 
        }}

        /* 7. SIDEBAR CARDS & DATA INPUTS */
        .stExpander {{
            background-color: #ceebe0 !important;
            border: 2px solid #0A1931 !important;
            border-radius: 0.5rem !important;
            margin-bottom: 0.2rem !important;
        }}
        
        .stExpander details summary p {{
            font-size: 1.15rem !important;
            font-weight: 700 !important;
            color: #0A1931 !important;
        }}

        .stTextInput input {{
            background-color: #ceebe0 !important;
            color: #021eba !important;
            font-size: 1.15rem !important;
            font-weight: 600 !important;
            padding: 0.5rem 0.8rem !important;
            border: 2px solid #0A1931 !important;
            border-radius: 0.4rem !important;
        }}
        
        .stMultiSelect div[role="combobox"] {{
            background-color: #ceebe0 !important;   
            border: 2px solid #0A1931 !important;
            border-radius: 0.4rem !important;
            min-height: 44px !important;
        }}
        
        div[data-testid="stSidebar"] .stTextInput {{
            margin-bottom: -0.6rem;
        }}
        
        /* 8. STATUS CONTROL BAR */
        .status-bar {{
            background-color: #CBDCEB !important;
            padding: 0.6rem 1rem;
            border-radius: 0.4rem;
            font-family: monospace;
            font-size: 1rem !important;
            font-weight: 700 !important;
            color: #0A1931 !important;
            margin-top: 0.4rem;
            border: 2px solid #0A1931 !important;
        }}
        
        /* 9. LIVELY DATA TABLE & SCROLL LOCK OVERRIDE */
        [data-testid="stDataFrame"] {{
            background-color: rgba(255, 255, 255, 0.3) !important;
            border-radius: 10px !important;
            border: 2px solid #0A1931 !important;
            width: 100% !important;
            flex-grow: 1 !important; 

        }}

        [data-testid="stDataFrame"] div {{
            background-color: transparent !important;
        }}

        [data-testid="stDataFrame"] thead {{
            background-color: #0A1931 !important;
            color: #CBDCEB !important;
        }}

        [data-testid="stDataFrame"] tbody tr:nth-of-type(even) {{
            background-color: #A3C1AD !important; /* High contrast mint or choose #CBDCEB for solid blue */
        }}
        </style>
    """, unsafe_allow_html=True)