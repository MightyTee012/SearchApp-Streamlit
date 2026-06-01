import os
import sys
import asyncio
import warnings
import re
from io import BytesIO
import pandas as pd
import streamlit as st

# Force Windows to use the Selector Event Loop to prevent Proactor crashes
if sys.platform == 'win32':
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# --- ABSOLUTE PATH FORCE ENGINE ---
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Import style file module safely
import AppStyle as style

# --- INIT PAGE CONFIG ---
st.set_page_config(
    page_title="Team Permitting",
    page_icon=style.ICONS["database"],
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply central design rules
style.inject_modern_css()

# --- FUNCTION REVISIONS (BUTTON & UTILITIES) ---
def clear_global_search():
    """Wipes the text bar back to empty safely from the global state layer."""
    st.session_state.global_search_input = ""

def clear_all_column_filters():
    """Loops through and clears every single dynamic column filter in session state."""
    for key in list(st.session_state.keys()):
        if key.startswith("sidebar_filter_"):
            st.session_state[key] = ""

def normalize_text(text):
    if pd.isna(text):
        return ""
    return re.sub(r'[^a-zA-Z0-9]', '', str(text)).lower()

def fuzzy_contains(series, query):
    normalized_query = normalize_text(query)
    if not normalized_query:
        return pd.Series(True, index=series.index)
    normalized_series = series.astype(str).str.replace(r'[^a-zA-Z0-9]', '', regex=True).str.lower()
    return normalized_series.str.contains(normalized_query, regex=False)

# --- DATA PROCESSING ENGINE ---
@st.cache_data(ttl=60)
def load_large_data(file):
    try:
        if file.name.endswith('.csv'):
            df = pd.read_csv(file, dtype=str)
        else:
            df = pd.read_excel(file, engine='openpyxl')

        for col in df.columns:
            # 1. Clean the incoming data row into clean strings
            raw_series = df[col].astype(str).str.strip().str.replace(r'\.0$', '', regex=True)
            
            if raw_series.replace(['nan', '', '<NA>'], pd.NA).dropna().empty:
                df[col] = ""
                continue

            # Create a blank array to test parsing on this column
            parsed_dates = pd.Series(pd.NaT, index=df.index)
            col_lower = col.lower()
            
            # 🚀 NEW DIRECT BYPASS HOOK: Detect core target column keywords explicitly
            is_target_date_column = any(k in col_lower for k in ['date', 'time', 'prepared', 'validity', 'valid'])

            with warnings.catch_warnings():
                warnings.filterwarnings("ignore", category=UserWarning)
                
                # STEP A: Try parsing as standard string dates
                non_numeric_mask = ~raw_series.str.isnumeric() & (raw_series != 'nan') & (raw_series != '')
                if non_numeric_mask.any():
                    # dayfirst=False keeps standard MM/DD/YYYY or YYYY/MM/DD routing intact
                    parsed_dates[non_numeric_mask] = pd.to_datetime(raw_series[non_numeric_mask], errors='coerce')

                # STEP B: Try parsing as Excel numeric date serials
                numeric_mask = raw_series.str.isnumeric() & (raw_series != '')
                if numeric_mask.any():
                    numeric_days = pd.to_numeric(raw_series[numeric_mask], errors='coerce')
                    
                    # 💡 TRACKING PROTECTION WIDENED: 
                    # If it's a known date column title, we open the safety bounds wide open (1 to 100,000)
                    lower_bound = 1 if is_target_date_column else 36526
                    valid_serial_mask = numeric_days.between(lower_bound, 100000)
                    
                    if valid_serial_mask.any():
                        parsed_dates[numeric_mask & valid_serial_mask] = pd.to_datetime(
                            numeric_days[valid_serial_mask], 
                            unit='D', 
                            origin='1899-12-30',
                            errors='coerce'
                        )

            # 🎯 THE DECISION LAYER:
            valid_dates_count = parsed_dates.notna().sum()
            
            # Force conversion if it contains dates OR if it's explicitly named as a target date column
            if valid_dates_count > 0 or is_target_date_column:
                valid_dates_mask = parsed_dates.notna()
                fallback_series = df[col].astype(str)
                
                # Format successfully parsed fields
                if valid_dates_mask.any():
                    df.loc[valid_dates_mask, col] = parsed_dates[valid_dates_mask].dt.strftime('%B %d, %Y')
                
                # Keep original string states if parsing completely failed on a weird text row
                df.loc[~valid_dates_mask, col] = fallback_series[~valid_dates_mask]
                
                # Final system cleanups
                df[col] = df[col].astype(str).replace(['nan', 'NaT', '<NA>', 'NaT/NaT'], '')
            else:
                df[col] = df[col].astype(str).replace(['nan', '<NA>'], '')
                
        return df
    except Exception as e:
        st.error(f"Error loading file: {e}")
        return None    
    
# --- SIDEBAR CONTROL PANEL ---
with st.sidebar:
# 🌟 NEW ANIMATED SIDEBAR TITLE WITH TRANSPARENCY FIX 🌟
    st.markdown(
        f"""
        <h1 style="display: flex; align-items: center; gap: 10px; margin-top: 0px; margin-bottom: 15px;">
            <span>{style.ICONS['database']} GAWA NI NONOY</span>
            <img src="https://i.pinimg.com/originals/15/c1/44/15c144e8dc552a100b3292d268854499.gif" 
                 style="height: 100px; width: auto; image-rendering: pixelated; mix-blend-mode: multiply; display: block;
                        transform: scaleX(-1)">
        </h1>
        """, 
        unsafe_allow_html=True
    )
    # 1. Collapsible File Manager
    with st.expander(f"{style.ICONS['file']} 1. UPLOADAN", expanded=True):
        uploaded_file = st.file_uploader(
            "DITO KA PO MAG UPLOAD! (Excel or CSV)", 
            type=["csv", "xlsx"],
            label_visibility="collapsed",
            key="persistent_uploader"
        )
        if uploaded_file is not None:
            st.success(f"Loaded: {uploaded_file.name}")

    st.markdown("---")
    
    global_search = ""
    col_filters = {}
    visible_columns = []

    if uploaded_file is not None:
        df = load_large_data(uploaded_file)
        
        if df is not None:
            # Initialize the multiselect session state if it doesn't exist yet
            if "visible_cols_key" not in st.session_state:
                st.session_state.visible_cols_key = df.columns.tolist()

            # 2. Collapsible Column Picker
            with st.expander(f"{style.ICONS['visible']} 2. SARAHAN NG COLUMNS ", expanded=False):
                col_opt_buttons = st.columns(2)
                with col_opt_buttons[0]:
                    if st.button("Select All", use_container_width=True):
                        st.session_state.visible_cols_key = df.columns.tolist()
                        st.rerun() 
                with col_opt_buttons[1]:
                    if st.button("Clear All", use_container_width=True):
                        st.session_state.visible_cols_key = [df.columns.tolist()[0]]
                        st.rerun() 
                
                visible_columns = st.multiselect(
                    "Display Columns:",
                    options=df.columns.tolist(),
                    key="visible_cols_key"
                )
            
            # Safety fallback to prevent a completely empty dataframe view
            if not visible_columns:
                visible_columns = [df.columns.tolist()[0]]
            
            st.markdown("---")

            # 3. Fuzzy Global Search
            with st.expander(f"{style.ICONS['search']} 3. HANAPAN", expanded=True):    
                global_search = st.text_input(
                    "Global Filter (Ignores Symbols/Spaces)", 
                    placeholder="🔍 Type to search everything...",
                    key="global_search_input"
                )
                
                # Clear button nested cleanly inside the expander shell
                st.button(
                    "❌ Clear Search", 
                    on_click=clear_global_search,
                    use_container_width=True  
                )    
            
            st.markdown("---")
            
        # 4. Dynamic Column Sub-Filters
            with st.expander(f"{style.ICONS['filter']} 4. HANAPAN (FILTER)", expanded=True):
                st.button(
                    "❌ Clear All Filters",
                    on_click=clear_all_column_filters,
                    use_container_width=True)
                # This loop creates the text input boxes
                for col_name in visible_columns:
                    col_filters[col_name] = st.text_input(
                        f"Filter: {col_name}", 
                        key=f"sidebar_filter_{col_name}",
                        placeholder=f"Filter {col_name}..."
                    )


if uploaded_file is not None and 'df' in locals() and df is not None:
    
    filtered_df = df[visible_columns].copy()

    # Apply Filters
    if global_search:
        masks = [fuzzy_contains(filtered_df[col], global_search) for col in visible_columns]
        global_mask = pd.concat(masks, axis=1).any(axis=1)
        filtered_df = filtered_df[global_mask]

    for col_name, search_val in col_filters.items():
        if search_val:
            col_mask = fuzzy_contains(filtered_df[col_name], search_val)
            filtered_df = filtered_df[col_mask]

          # 🚀 1. EXTRACTION FIX: Get the uploaded file name
    import os
    clean_title = os.path.splitext(uploaded_file.name)[0]

    st.markdown(f'<div style="display: flex; align-items: center; gap: 15px; height: 100px; margin-bottom: 15px; margin-top: -20px;"><img src="https://i.pinimg.com/originals/c5/ee/51/c5ee5152fd8575cd966fa258addca1a1.gif" style="height: 100px; width: auto; image-rendering: pixelated; mix-blend-mode: multiply; display: block;"><span style="font-size: 28px; font-weight: 700; color: #0A1931; font-family: \'Source Sans Pro\', sans-serif;">{clean_title}</span></div>', unsafe_allow_html=True)
    
         # 2. Your Locked Layout CSS Stylesheet Injection
    st.markdown("""
            <style>
                /* Force the main container block to span edge-to-edge */
                .block-container {
                    max-width: 100% !important;
                    padding-left: 2rem !important;
                    padding-right: 2rem !important;
                    padding-top: 5rem !important;
                }
                /* Hide web page scrollbars completely so the window stays frozen */
                html, body {
                    overflow: hidden !important;
                    height: 150vh !important;
                }
            </style>
        """, unsafe_allow_html=True)
    # 3. THE CONTAINER FIXED WRAPPER

    with st.container():
        st.dataframe(
            filtered_df,
            width="stretch", 
            height=600,       # Set this to a height that fits your exact monitor screen
            hide_index=True,
            column_config={
                col: st.column_config.TextColumn(
                    col, 
                    width="large",     
                    disabled=True      
                ) 
                for col in visible_columns
            }
        )
    # Status Notification Ribbon
    st.markdown(
            f"""
            <div class="status-bar" style="display: flex; justify-content: space-between; align-items: center; padding: 0.4rem 1rem;">
                <div>
                    📊 <b>Rows Displayed:</b> {len(filtered_df):,} of {len(df):,} total records | 
                    📋 <b>Visible Columns:</b> {len(visible_columns)} of {len(df.columns)} active
                </div>
                <div>
                    <img src="https://dl.glitter-graphics.com/pub/3709/3709531e18qrw4sle.gif" 
                        style="height: 100px; width: auto; image-rendering: pixelated; margin-bottom: -4px;mix-blend-mode: multiply;">
                </div>
            </div>
            """, 
            unsafe_allow_html=True
        )
        
    # Workbook Downloader Panel
    with st.sidebar:
        st.markdown("---")
        
        with st.expander(f"{style.ICONS['download']} 5. DOWNLOADAN", expanded=True):
            
            def convert_df_to_excel(df_to_save):
                output = BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df_to_save.to_excel(writer, index=False, sheet_name='Filtered_View')
                return output.getvalue()
            
            if not filtered_df.empty:
                excel_file = convert_df_to_excel(filtered_df)
                
                st.download_button(
                    label="👌 Export & Download Excel",
                    data=excel_file,
                    file_name="db_browser_export.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True 
                )
            else:
                st.warning("No data rows available to export.")
else:
    st.info("🐶 System Idle. Use the control pane on the left to drop in your source data matrix file.🐶")