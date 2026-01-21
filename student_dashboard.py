import streamlit as st
from config import fetch_details
import datetime
from ui_components import display_subject_card

def student_dashboard():
    # -------------------- SESSION VALIDATION --------------------
    if "username" not in st.session_state or not st.session_state.get("logged_in"):
        st.error("Please log in first.")
        st.stop()

    # -------------------- SIDEBAR STYLE --------------------
    st.sidebar.markdown("""
    <style>
    .stSidebar {
        background: linear-gradient(135deg, #0f172a, #1e293b);
    }
    </style>
    """, unsafe_allow_html=True)

    st.sidebar.title("🧭 Student Menu")
    if "username" in st.session_state:
        st.sidebar.markdown(f"**Welcome, {st.session_state.username}**")
        st.sidebar.markdown(f"*Role: Student*")
        st.sidebar.markdown("---")
    choice = st.sidebar.radio("Menu", ["Dashboard", "My Profile", "My Attendance", "My Grades", "My Fees", "Logout"])

    username = st.session_state["username"]
    st.title(f"🎓 Student Dashboard - Welcome {username}!")

    # Get student ID for queries
    student_info = fetch_details("""
        SELECT sd.id, sd.name 
        FROM student_details sd
        JOIN login_details ld ON sd.id = ld.user_id
        WHERE ld.uname=%s AND ld.typeOfUser='student'
    """, (username,))

    if not student_info:
        st.error("Student profile not found. Please contact administrator.")
        return

    student_id, student_name = student_info[0]

    # =====================================================================
    #                               DASHBOARD
    # =====================================================================
    if choice == "Dashboard":
        st.subheader("📊 My Academic Overview")

        # -------------------- Student Basic Info --------------------
        student_details = fetch_details("""
            SELECT sd.name, sd.age, sd.sex, sd.phoneno 
            FROM student_details sd
            WHERE sd.id=%s
        """, (student_id,))

        if student_details:
            name, age, gender, phone = student_details[0]
            col1, col2 = st.columns(2)
            with col1:
                st.info(f"**Name:** {name or 'N/A'}")
                st.info(f"**Age:** {age or 'N/A'}")
            with col2:
                st.info(f"**Gender:** {gender or 'N/A'}")
                st.info(f"**Phone:** {phone or 'N/A'}")
                
        # -------------------- QUICK STATISTICS --------------------
        st.subheader("📈 Quick Statistics")
        col1, col2, col3, col4 = st.columns(4)

        # Attendance Rate
        with col1:
            try:
                attendance_data = fetch_details("""
                    SELECT 
                        SUM(CASE WHEN status='Present' THEN 1 ELSE 0 END) as present_count,
                        COUNT(*) as total_count
                    FROM attendance 
                    WHERE student_name=%s
                """, (student_name,))
                if attendance_data and attendance_data[0][1] > 0:
                    present_count = attendance_data[0][0] or 0
                    total_count = attendance_data[0][1]
                    attendance_rate = (present_count / total_count) * 100
                    st.metric("Attendance Rate", f"{attendance_rate:.1f}%")
                else:
                    st.metric("Attendance Rate", "0%")
            except Exception as e:
                st.metric("Attendance Rate", "N/A")

        # Total Courses
        with col2:
            try:
                course_count = fetch_details("""
                    SELECT COUNT(DISTINCT course) 
                    FROM results 
                    WHERE student_id=%s
                """, (student_id,))
                st.metric("Total Courses", course_count[0][0] if course_count else 0)
            except Exception as e:
                st.metric("Courses", "Error")

        # Graded Courses
        with col3:
            try:
                graded_courses = fetch_details("""
                    SELECT COUNT(DISTINCT course) 
                    FROM results 
                    WHERE student_id=%s AND grade IS NOT NULL
                """, (student_id,))
                st.metric("Graded Courses", graded_courses[0][0] if graded_courses else 0)
            except Exception as e:
                st.metric("Graded", "Error")

        # Latest Fee Status
        with col4:
            try:
                fee_status = fetch_details("""
                    SELECT status FROM fees 
                    WHERE student_name=%s 
                    ORDER BY due_date DESC LIMIT 1
                """, (student_name,))
                status_text = fee_status[0][0] if fee_status else "No Fees"
                st.metric("Fee Status", status_text)
            except Exception as e:
                st.metric("Fee Status", "Error")

        # -------------------- COURSE INFORMATION --------------------
        st.subheader("📚 My Courses")

        courses_data = fetch_details("""
            SELECT DISTINCT 
                r.course,
                COALESCE(f.name, 'Not Assigned') as faculty_name,
                r.grade
            FROM results r
            LEFT JOIN faculty_details f ON r.faculty_id = f.id
            WHERE r.student_id = %s
            ORDER BY r.course
        """, (student_id,))

        if not courses_data:
            st.info("No courses assigned yet.")
        else:
            for course, faculty, grade in courses_data:
                display_subject_card(course, faculty, grade)

    # =====================================================================
    #                              MY PROFILE
    # =====================================================================
    elif choice == "My Profile":
        st.subheader("👤 My Personal Information")

        student_data = fetch_details("""
            SELECT sd.id, sd.name, sd.age, sd.sex, sd.phoneno 
            FROM student_details sd
            WHERE sd.id=%s
        """, (student_id,))

        if not student_data:
            st.error("No profile information found.")
            return

        student_id, name, age, sex, phoneno = student_data[0]

        st.markdown("""
        <div style='
            background: rgba(30,41,59,0.8);
            border-radius: 10px;
            padding: 20px;
            border: 1px solid #334155;
            margin-bottom: 20px;
        '>
        """, unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            st.write("##### 🆔 Student Information")
            st.write(f"**Student ID:** {student_id}")
            st.write(f"**Full Name:** {name}")
            st.write(f"**Age:** {age}")
        with col2:
            st.write("##### 👤 Personal Details")
            st.write(f"**Gender:** {sex}")
            st.write(f"**Phone Number:** {phoneno}")
            st.write(f"**Username:** {username}")

        st.markdown("</div>", unsafe_allow_html=True)

        # Academic Info
        st.write("##### 📚 Academic Information")
        academic_info = fetch_details("""
            SELECT DISTINCT course
            FROM results 
            WHERE student_id = %s
        """, (student_id,))

        if academic_info:
            courses = [row[0] for row in academic_info]
            st.write("**Enrolled Courses:**")
            for course in courses:
                st.write(f"- {course}")
        else:
            st.info("No academic information available.")

    # =====================================================================
    #                              MY ATTENDANCE
    # =====================================================================
    elif choice == "My Attendance":
        st.subheader("📅 My Attendance Records")

        attendance_data = fetch_details("""
            SELECT date, status 
            FROM attendance 
            WHERE student_name=%s 
            ORDER BY date DESC 
            LIMIT 30
        """, (student_name,))

        if not attendance_data:
            st.info("No attendance records found.")
            return

        present_count = len([d for d in attendance_data if d[1] == "Present"])
        total_count = len(attendance_data)
        percentage = (present_count / total_count * 100) if total_count > 0 else 0

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Present Days", present_count)
        with col2:
            st.metric("Absent Days", total_count - present_count)
        with col3:
            st.metric("Attendance %", f"{percentage:.1f}%")

        st.write("---")
        st.write("**Recent Attendance Records:**")
        for date, status in attendance_data[:15]:
            date_str = date.strftime("%Y-%m-%d") if hasattr(date, 'strftime') else str(date)
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"**{date_str}**")
            with col2:
                if status == "Present":
                    st.success("✅ Present")
                else:
                    st.error("❌ Absent")
            st.divider()

    # =====================================================================
    #                               MY GRADES
    # =====================================================================
    elif choice == "My Grades":
        st.subheader("📚 My Academic Grades")

        grades_data = fetch_details("""
            SELECT r.course, r.grade, COALESCE(f.name, 'Not Assigned') 
            FROM results r
            LEFT JOIN faculty_details f ON r.faculty_id = f.id
            WHERE r.student_id = %s
            ORDER BY r.course
        """, (student_id,))

        if not grades_data:
            st.info("No grade records found.")
            return

        # Display courses in a simple list
        for course, grade, faculty in grades_data:
            display_subject_card(course, faculty, grade, use_columns=True)

        # GPA Calculation
        st.subheader("🎓 GPA Calculation")
        grade_points = {
            'A+': 4.0, 'A': 4.0, 'A-': 3.7,
            'B+': 3.3, 'B': 3.0, 'B-': 2.7,
            'C+': 2.3, 'C': 2.0, 'C-': 1.7,
            'D+': 1.3, 'D': 1.0, 'F': 0.0
        }

        total_points = 0
        valid_count = 0

        for course, grade, faculty in grades_data:
            if grade in grade_points:
                total_points += grade_points[grade]
                valid_count += 1

        if valid_count > 0:
            gpa = total_points / valid_count
            st.metric("Current GPA", f"{gpa:.2f}")
            
            # Grade interpretation
            if gpa >= 3.7:
                st.success("Excellent Performance! 🎉")
            elif gpa >= 3.0:
                st.info("Good Performance! 👍")
            elif gpa >= 2.0:
                st.warning("Satisfactory Performance")
            else:
                st.error("Needs Improvement")
        else:
            st.info("GPA cannot be calculated. No valid grades.")

    # =====================================================================
    #                                 MY FEES
    # =====================================================================
    elif choice == "My Fees":
        st.subheader("💰 My Fee Details")

        fees_data = fetch_details("""
            SELECT amount, due_date, status
            FROM fees 
            WHERE student_name=%s 
            ORDER BY due_date DESC
        """, (student_name,))

        if not fees_data:
            st.info("No fee records found for you.")
            return

        total_fees = sum(x[0] for x in fees_data)
        total_paid = sum(x[0] for x in fees_data if x[2] == "Paid")
        total_pending = sum(x[0] for x in fees_data if x[2] == "Pending")

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Fees", f"₹{total_fees:,.2f}")
        with col2:
            st.metric("Total Paid", f"₹{total_paid:,.2f}")
        with col3:
            st.metric("Total Pending", f"₹{total_pending:,.2f}")

        st.write("---")
        st.write("### 📋 Fee Details")
        
        for amount, due_date, status in fees_data:
            due_date_str = due_date.strftime("%Y-%m-%d") if hasattr(due_date, 'strftime') else str(due_date)
            is_overdue = due_date < datetime.date.today() if hasattr(due_date, 'strftime') else False

            if status == "Paid":
                border = "#10b981"
                icon = "✅"
            elif status == "Pending" and is_overdue:
                border = "#ef4444"
                icon = "⚠️ OVERDUE"
            elif status == "Pending":
                border = "#f59e0b"
                icon = "⏳"
            else:
                border = "#60a5fa"
                icon = "🟡"

            st.markdown(f"""
            <div style='
                background: rgba(30,41,59,0.8);
                border-radius: 10px;
                padding: 15px;
                border-left: 4px solid {border};
                border: 1px solid #334155;
                margin: 10px 0;
            '>
                <div style='display:flex; justify-content:space-between;'>
                    <h4 style='color:#60a5fa;margin:0;'>Fee - ₹{amount:,.2f}</h4>
                    <span style='color:{border}; font-weight:bold;'>{icon} {status}</span>
                </div>
                <p style='color:#cbd5e1;margin:5px 0;'><strong>Due Date:</strong> {due_date_str}</p>
                <p style='color:#cbd5e1;margin:5px 0;'><strong>Status:</strong> {status}</p>
            </div>
            """, unsafe_allow_html=True)

        st.write("---")
        st.write("### 💳 Payment Instructions")
        st.info("""
        **Payment Methods:**
        - **Online Transfer:** Account No: 1234567890, IFSC: ABCD0123456
        - **UPI:** yourcollege@upi
        - **Cash:** College Accounts Office (Main Building, Room 101)
        - **Cheque:** Payable to "University College"
        
        **Office Hours:** 9:00 AM - 4:00 PM (Monday to Friday)
        
        **Contact:** accounts@university.edu | Phone: (555) 123-4567
        """)

    # =====================================================================
    #                                 LOGOUT
    # =====================================================================
    elif choice == "Logout":
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()