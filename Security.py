import streamlit as st

def check_password():
    """Returns True if the user has entered the correct password."""

def password_entered():
    """Checks whether a password entered by the user is correct."""
    # 🔒 FIX: Read the password securely from Streamlit's secret manager
    if st.session_state["password"] == st.secrets["APP_PASSWORD"]:
        st.session_state["password_correct"] = True
        del st.session_state["password"]  
    else:
        st.session_state["password_correct"] = False

    # First run / baseline check
    if st.session_state.get("password_correct", False):
        return True

    # Show the login screen form
    st.markdown("### 🔐 App Security Access")
    st.write("Please enter the access password below to view the dataset.")
    
    st.text_input(
        "Enter Password", 
        type="password", 
        on_change=password_entered, 
        key="password"
    )

    # If they typed the wrong password, show an explicit error warning
    if "password_correct" in st.session_state and not st.session_state["password_correct"]:
        st.error("❌ Incorrect password. Please try again or ask your administrator.")
        return False

    return False