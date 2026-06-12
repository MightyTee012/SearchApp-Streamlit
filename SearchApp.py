import os
import sys
import asyncio
import warnings
import re
from io import BytesIO
import pandas as pd
import streamlit as st
from AppStyle import inject_modern_css
from Security import check_password

inject_modern_css()

if not check_password():
    st.stop()  # 🛑 HALT! Don't run anything below this line if login fails

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
    initial_sidebar_state="collapsed" 
)

# Apply central design rules
style.inject_modern_css()

# --- HIGH-DENSITY SCREEN OPTIMIZER ---
st.markdown("""
    <style>
        .block-container {
            max-width: 100% !important;
            padding-left: 1.5rem !important;
            padding-right: 1.5rem !important;
            padding-top: 1.5rem !important;
            padding-bottom: 1rem !important;
        }
        div[data-testid="stVerticalBlock"] {
            gap: 0.6rem !important;
        }
        body {
            overflow: hidden;
        }
    </style>
""", unsafe_allow_html=True)

# --- THE STABLE CAPSULE STORAGE LAYER ---
if "file_capsule" not in st.session_state:
    st.session_state.file_capsule = None

# --- HELPER UTILITIES ---
def clear_all_searches_and_filters():
    st.session_state.global_search_input = ""
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
            # 🌟 FIX 1: If Pandas natively auto-detects an Excel date column, format it immediately and lock it as text
            if pd.api.types.is_datetime64_any_dtype(df[col]):
                df[col] = df[col].dt.strftime('%B %d, %Y').fillna('').astype(str)
                continue

            raw_series = df[col].astype(str).str.strip().str.replace(r'\.0$', '', regex=True)
            if raw_series.replace(['nan', '', '<NA>'], pd.NA).dropna().empty:
                df[col] = ""
                continue

            parsed_dates = pd.Series(pd.NaT, index=df.index)
            col_lower = col.lower()
            is_target_date_column = any(k in col_lower for k in ['date', 'time', 'prepared', 'validity', 'valid'])

            with warnings.catch_warnings():
                warnings.filterwarnings("ignore", category=UserWarning)
                non_numeric_mask = ~raw_series.str.isnumeric() & (raw_series != 'nan') & (raw_series != '')
                if non_numeric_mask.any():
                    parsed_dates[non_numeric_mask] = pd.to_datetime(raw_series[non_numeric_mask], errors='coerce')

                numeric_mask = raw_series.str.isnumeric() & (raw_series != '')
                if numeric_mask.any():
                    numeric_days = pd.to_numeric(raw_series[numeric_mask], errors='coerce')
                    lower_bound = 1 if is_target_date_column else 36526
                    valid_serial_mask = numeric_days.between(lower_bound, 100000)
                    if valid_serial_mask.any():
                        parsed_dates[numeric_mask & valid_serial_mask] = pd.to_datetime(
                            numeric_days[valid_serial_mask], unit='D', origin='1899-12-30', errors='coerce'
                        )

            valid_dates_count = parsed_dates.notna().sum()
            if valid_dates_count > 0 or is_target_date_column:
                valid_dates_mask = parsed_dates.notna()
                fallback_series = df[col].astype(str)
                
                # 🌟 FIX 2: Explicitly force the column to plain text format before converting mixed text dates
                df[col] = df[col].astype(str)
                if valid_dates_mask.any():
                    df.loc[valid_dates_mask, col] = parsed_dates[valid_dates_mask].dt.strftime('%B %d, %Y')
                df.loc[~valid_dates_mask, col] = fallback_series[~valid_dates_mask]
                df[col] = df[col].astype(str).replace(['nan', 'NaT', '<NA>', 'NaT/NaT'], '')
            else:
                df[col] = df[col].astype(str).replace(['nan', '<NA>'], '')
        return df
    except Exception as e:
        st.error(f"Error loading file: {e}")
        return None

# --- MAIN BRANDING HEADER ---
st.markdown(
    f"""
    <div style="display: flex; align-items: center; gap: 12px; height: 65px; margin-bottom: 5px; margin-top: -15px;">
        <img src="https://i.pinimg.com/originals/15/c1/44/15c144e8dc552a100b3292d268854499.gif" style="height: 60px; width: auto; image-rendering: pixelated; mix-blend-mode: multiply;">
        <span style="font-size: 24px; font-weight: 800; color: #0A1931; font-family: 'Source Sans Pro', sans-serif;">GAWA NI NONOY 👌</span>
    </div>
    """, 
    unsafe_allow_html=True
)

# Outer Layout Setup
side_control_panel, main_data_window = st.columns([0.20, 0.80], gap="medium")
active_file = st.session_state.file_capsule

with side_control_panel:
    tab_setup, tab_search, tab_download = st.tabs([
        "⚙️ 1. SETUP", 
        "🔍 2. SEARCH", 
        "💾 3. EXPORT"
    ])
    
    with tab_setup:
        st.markdown(f"### {style.ICONS['file']} Setup Deck")
        raw_upload = st.file_uploader(
            "Drop workbook matrix:", 
            type=["csv", "xlsx"],
            key="file_uploader_widget"
        )
        if raw_upload is not None:
            st.session_state.file_capsule = raw_upload
            active_file = raw_upload

        if st.session_state.file_capsule is not None:
            st.markdown("---")
            if st.button("🗑️ Unload Current File", use_container_width=True):
                st.session_state.file_capsule = None
                if "visible_cols_widget" in st.session_state:
                    del st.session_state["visible_cols_widget"]
                st.cache_data.clear()
                st.rerun()

if active_file is not None:
    df = load_large_data(active_file)
    if df is not None:
        
        if "visible_cols_widget" not in st.session_state:
            st.session_state.visible_cols_widget = df.columns.tolist()
            
        if not st.session_state.visible_cols_widget:
            st.session_state.visible_cols_widget = [df.columns.tolist()[0]]

        with side_control_panel:
            with tab_setup:
                st.markdown(f"### {style.ICONS['visible']} Display Columns")
                c_b1, c_b2 = st.columns(2)
                with c_b1:
                    if st.button("All", key="all_t1", use_container_width=True):
                        st.session_state.visible_cols_widget = df.columns.tolist()
                        st.rerun()
                with c_b2:
                    if st.button("None", key="none_t1", use_container_width=True):
                        st.session_state.visible_cols_widget = [df.columns.tolist()[0]]
                        st.rerun()
                
                st.multiselect(
                    "Toggle view headers:",
                    options=df.columns.tolist(),
                    key="visible_cols_widget",
                    label_visibility="collapsed"
                )

            visible_columns = st.session_state.visible_cols_widget
            filtered_df = df[visible_columns].copy()

            # 🛠️ SPEED OPTIMIZATION: Wrapped inputs inside a unified processing form
            with tab_search:
                st.markdown(f"### {style.ICONS['search']} Master Filters")
                st.button("❌ CLEAR ", on_click=clear_all_searches_and_filters, key="reset_search_deck_btn", use_container_width=True)
                st.markdown("<div style='margin-bottom: 2px;'></div>", unsafe_allow_html=True)
                
                # Form Container locks the entry state until you submit
                with st.form(key="optimized_search_form", border=False):
                    
                    st.text_input(
                        "Main Search Bar:", 
                        placeholder="🔍 Search...",
                        key="global_search_input"
                    )
                    st.markdown("---")
                    st.markdown(f"### {style.ICONS['filter']} Column Sub-Filters")
                    
                    with st.container(height=360, border=False):
                        for col_name in visible_columns:
                            st.text_input(
                                f"{col_name}", 
                                key=f"sidebar_filter_{col_name}",
                                placeholder=f"🔎 {col_name}..."
                            )
                    
                    # The execution lock switch button
                    st.form_submit_button(label="⚡ RUN SEARCH FILTERS", use_container_width=True)

            with tab_download:
                st.markdown(f"### {style.ICONS['download']} Export Deck")
                def convert_df_to_excel(df_to_save):
                    output = BytesIO()
                    with pd.ExcelWriter(output, engine='openpyxl') as writer:
                        df_to_save.to_excel(writer, index=False, sheet_name='Filtered_View')
                    return output.getvalue()

        # --- DATA MUTATION EXECUTION ---
        if st.session_state.get("global_search_input", ""):
            search_query = st.session_state.global_search_input
            masks = [fuzzy_contains(filtered_df[col], search_query) for col in visible_columns]
            global_mask = pd.concat(masks, axis=1).any(axis=1)
            filtered_df = filtered_df[global_mask]

        for col_name in visible_columns:
            search_val = st.session_state.get(f"sidebar_filter_{col_name}", "")
            if search_val:
                col_mask = fuzzy_contains(filtered_df[col_name], search_val)
                filtered_df = filtered_df[col_mask]

        with side_control_panel:
            with tab_download:
                if not filtered_df.empty:
                    excel_file = convert_df_to_excel(filtered_df)
                    st.download_button(
                        label="👌 Export Excel File",
                        data=excel_file,
                        file_name="db_browser_export.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True 
                    )
                else:
                    st.warning("No metrics match your search parameters to compile.")

        # Stable Display Table Output Window
        with main_data_window:
            clean_title = os.path.splitext(active_file.name)[0]
            st.markdown(f'<div style="display: flex; align-items: center; gap: 5px; margin-top: -15px; margin-bottom: 2px;"><img src="https://i.pinimg.com/originals/c5/ee/51/c5ee5152fd8575cd966fa258addca1a1.gif" style="height: 100px; width: auto; image-rendering: pixelated; mix-blend-mode: multiply;"><span style="font-size: 30px; font-weight: 700; color: #0A1931;">{clean_title}</span></div>', unsafe_allow_html=True)
            st.dataframe(
                filtered_df,
                width="stretch", 
                height=650, 
                hide_index=True,
                column_config={col: st.column_config.TextColumn(col, width="large", disabled=True) for col in visible_columns}
            )
            st.markdown(f"""<div style="display: flex; justify-content: space-between; align-items: center; padding: 0.1rem 0.5rem; background:#f8f9fa; border-radius:6px; font-size:20px; margin-top: 2px;"><div>📊 <b>Rows Viewable:</b> {len(filtered_df):,} of {len(df):,} records | 📋 <b>Columns Visible:</b> {len(visible_columns)} of {len(df.columns)}</div><div><img src="https://dl.glitter-graphics.com/pub/3709/3709531e18qrw4sle.gif" style="height: 100px; width: auto; image-rendering: pixelated; mix-blend-mode: multiply;"></div></div>""", unsafe_allow_html=True)
else:
    with side_control_panel:
        with tab_search:
            st.warning("⚠️ Setup required.")
        with tab_download:
            st.warning("⚠️ Setup required.")
    with main_data_window:
        st.info(" Workspace Idle. Drop a source data file into the Setup panel on the left to begin.")