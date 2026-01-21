import streamlit as st
from config import fetch_details
from main import main_app

# -------------------- PAGE CONFIG --------------------
st.set_page_config(
    page_title="Student Management System",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# -------------------- SIMPLE CSS --------------------
st.markdown("""
<style>
    html, body, [class*="css"] {
        font-family: 'Segoe UI', 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        margin: 0;
        padding: 0;
    }
    
    .stApp {
        background: linear-gradient(135deg, #1a237e 0%, #311b92 100%);
        min-height: 100vh;
    }
    
    .main .block-container {
        padding: 0 !important;
        max-width: 100% !important;
        display: flex;
        align-items: center;
        justify-content: center;
        min-height: 100vh;
    }
    
   
    
    .login-title {
        text-align: center;
        margin-bottom: 30px;
    }
    
    .logo-circle {
        width: 70px;
        height: 70px;
        background: linear-gradient(135deg, #3d5afe, #7c4dff);
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        margin: 0 auto 20px;
    }
    
    .logo-circle span {
        font-size: 35px;
        color: white;
    }
    
    .system-name {
        color: white;
        font-size: 26px;
        font-weight: 700;
        margin-bottom: 8px;
        text-align: center;
    }
    
    .tagline {
        color: rgba(255, 255, 255, 0.8);
        font-size: 15px;
        text-align: center;
        margin-bottom: 30px;
    }
    
    .stTextInput input {
        background: rgba(255, 255, 255, 0.1) !important;
        border: 1px solid rgba(255, 255, 255, 0.3) !important;
        border-radius: 10px !important;
        color: white !important;
        padding: 12px 15px !important;
        font-size: 15px !important;
    }
    
    .stTextInput input:focus {
        border-color: #3d5afe !important;
        box-shadow: 0 0 0 2px rgba(61, 90, 254, 0.2) !important;
    }
    
    .stTextInput input::placeholder {
        color: rgba(255, 255, 255, 0.5) !important;
    }
    
    .stButton > button {
        background: linear-gradient(135deg, #3d5afe, #7c4dff) !important;
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 14px !important;
        font-size: 16px !important;
        font-weight: 600 !important;
        width: 100% !important;
        margin-top: 10px !important;
    }
    
    .stButton > button:hover {
        background: linear-gradient(135deg, #304ffe, #651fff) !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 25px rgba(61, 90, 254, 0.4) !important;
    }
    
    header {visibility: showen !important; height: 0 !important;}
    footer {visibility: hidden !important;}
    
    @media (max-width: 768px) {
        .login-card {
            margin: 20px;
            padding: 30px;
        }
        .system-name {
            font-size: 22px;
        }
    }
</style>
""", unsafe_allow_html=True)

# -------------------- SESSION STATE --------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "role" not in st.session_state:
    st.session_state.role = ""

# -------------------- MAIN LOGIN PAGE --------------------
def show_login():
    """Simple login page without footer"""
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown('<div class="login-card">', unsafe_allow_html=True)
        
        # Header
        st.markdown("""
        <div class="login-title">
            <div class="logo-circle">
                <span>🎓</span>
            </div>
            <h1 class="system-name">Student Management System</h1>
            <p class="tagline">Login to access your dashboard</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Login Form
        username = st.text_input("Username", placeholder="Enter username")
        password = st.text_input("Password", type="password", placeholder="Enter password")
        
        # Login Button
        if st.button("Login", key="login_btn", use_container_width=True):
            if not username or not password:
                st.warning("Please enter both username and password.")
            else:
                # Use the correct query for the login_details table schema
                query = "SELECT typeOfUser FROM login_details WHERE uname=%s AND password=%s"
                user_role = None
                user_role = fetch_details(query, (username, password))

                if user_role:
                    st.session_state.logged_in = True
                    st.session_state.username = username
                    st.session_state.role = user_role[0][0]
                    st.success("Login Successful!")
                    st.rerun()
                else:
                    # Debug: Show what's in the database
                    st.error("Invalid credentials.")
                    
                    # Show debug info in expander
                    with st.expander("Debug Info"):
                        all_users = fetch_details("SELECT * FROM login_details LIMIT 10")
                        if all_users:
                            st.write("First 10 users in database:")
                            for user in all_users:
                                st.write(user)
                        else:
                            st.write("No users found in login_details table")
        
        st.markdown("</div>", unsafe_allow_html=True)

# -------------------- DASHBOARD ROUTER --------------------
def show_dashboard():
    """Show appropriate dashboard based on user role"""
    
    username = st.session_state.get("username", "")
    role = st.session_state.get("role", "")
    
    # Simple header
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, #1a237e, #311b92);
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 20px;
        color: white;
    ">
        <h1 style="margin: 0; color: white;">🎓 Student Management System</h1>
        <p style="margin: 5px 0 0 0;">Welcome, <strong>{username}</strong> • Role: <strong>{role.capitalize()}</strong></p>
    </div>
    """, unsafe_allow_html=True)
    
    # Import and show appropriate dashboard
    try:
        if role == "admin":
            from admin_dashboard import admin_dashboard
            admin_dashboard()
        elif role == "faculty":
            from faculty_dashboard import faculty_dashboard
            faculty_dashboard()
        elif role == "student":
            from student_dashboard import student_dashboard
            student_dashboard()
        else:
            st.error(f"Unknown role: {role}")
            if st.button("Logout"):
                st.session_state.logged_in = False
                st.rerun()
    except Exception as e:
        st.error(f"Error loading dashboard: {str(e)}")
        if st.button("Return to Login"):
            st.session_state.logged_in = False
            st.rerun()

# -------------------- MAIN CONTROLLER --------------------
def main():
    """Main application controller"""
    
    if st.session_state.logged_in:
        # User is logged in, show main app
        main_app()
    else:
        # Show login page
        show_login()

if __name__ == "__main__":
    main()