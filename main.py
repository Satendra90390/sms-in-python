# main.py - Complete app in one file
import streamlit as st
from config import fetch_details

# -------------------- PAGE CONFIG --------------------
st.set_page_config(
    page_title="Student Management System",
    page_icon="🎓",
    layout="wide"
)

# -------------------- LOGIN PAGE --------------------
def show_login():
    """Show login page"""
    
    # Login CSS
    st.markdown("""
    <style>
        .stApp {
            background: linear-gradient(135deg, #1a237e 0%, #311b92 100%);
            min-height: 100vh;
        }
        .login-container {
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            padding: 20px;
        }
        
        }
        header {visibility: showen
        ;}
        footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown('<div class="login-card">', unsafe_allow_html=True)
        
        # Logo and title
        st.markdown("""
        <div style="text-align: center; margin-bottom: 30px;">
            <div style="
                width: 70px;
                height: 70px;
                background: linear-gradient(135deg, #3d5afe, #7c4dff);
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                margin: 0 auto 20px;
            ">
                <span style="font-size: 35px; color: white;">🎓</span>
            </div>
            <h1 style="color: white; margin: 0; font-size: 26px;">
                Student Management System
            </h1>
            <p style="color: rgba(255, 255, 255, 0.8); margin-top: 10px;">
                Login to access your dashboard
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Login form
        username = st.text_input("👤 Username", placeholder="Enter username")
        password = st.text_input("🔒 Password", type="password", placeholder="Enter password")
        
        if st.button("🚀 Login", use_container_width=True):
            if not username or not password:
                st.warning("Please enter both username and password.")
            else:
                query = "SELECT typeOfUser FROM login_details WHERE uname=%s AND password=%s"
                user_role = fetch_details(query, (username, password))
                
                if user_role:
                    st.session_state.logged_in = True
                    st.session_state.username = username
                    st.session_state.role = user_role[0][0]
                    st.success("✅ Login Successful!")
                    st.rerun()
                else:
                    st.error("❌ Invalid credentials. Please try again.")
        
        st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

# -------------------- DASHBOARD --------------------
def show_dashboard():
    """Show dashboard based on user role"""
    
    # Dashboard CSS
    st.markdown("""
    <style>
        .stApp {
            background: linear-gradient(135deg, #0f172a, #1e293b);
            color: #f8fafc;
        }
        .header {
            background: rgba(30, 41, 59, 0.9);
            padding: 20px;
            border-radius: 12px;
            margin-bottom: 30px;
            border: 1px solid #334155;
        }
        .stButton button {
            background: linear-gradient(135deg, #dc2626, #b91c1c);
            color: white;
            border: none;
            border-radius: 8px;
            font-weight: 600;
        }
        .about-section {
            background: rgba(30, 41, 59, 0.8);
            padding: 20px;
            border-radius: 12px;
            border-left: 4px solid #3b82f6;
            margin: 20px 0;
        }
        .about-section h3 {
            color: #60a5fa;
            margin-top: 0;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Header
    username = st.session_state.get("username", "")
    role = st.session_state.get("role", "")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(f"""
        <div class="header">
            <h1 style="color: #60a5fa; margin: 0;">🎓 Student Management System</h1>
            <p style="color: #cbd5e1; margin: 10px 0 0 0;">
                Welcome, <strong>{username}</strong> • Role: <strong>{role.capitalize()}</strong>
            </p>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.write("")  # Spacer
        if st.button("🚪 Logout"):
            st.session_state.logged_in = False
            st.rerun()
    
    # Load appropriate dashboard
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
    except ImportError as e:
        st.error(f"Dashboard not found: {str(e)}")
        st.info("Make sure dashboard files exist in the same directory.")
    
    # About Section
    st.markdown("""
    <div class="about-section">
        <h3>📋 About This System</h3>
        <p>
            The Student Management System is a comprehensive platform designed to streamline academic operations 
            and manage student information efficiently. This system provides role-based access for administrators, 
            faculty members, and students to manage their respective tasks and data.
        </p>
        <p style="margin: 10px 0 0 0; font-size: 0.9em; color: #94a3b8;">
            <strong>Features:</strong> Student enrollment, grades management, course scheduling, attendance tracking, 
            and comprehensive reporting capabilities.
        </p>
    </div>
    """, unsafe_allow_html=True)

# -------------------- MAIN --------------------
def main_app():
    """Main application - shows dashboard based on user role"""
    
    # Initialize session
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if "username" not in st.session_state:
        st.session_state.username = ""
    if "role" not in st.session_state:
        st.session_state.role = ""
    
    # Show the dashboard
    show_dashboard()

def main():
    """Main application"""
    
    # Initialize session
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if "username" not in st.session_state:
        st.session_state.username = ""
    if "role" not in st.session_state:
        st.session_state.role = ""
    
    # Route based on login status
    if not st.session_state.logged_in:
        show_login()
    else:
        show_dashboard()

# Run the app
if __name__ == "__main__":

    main()

