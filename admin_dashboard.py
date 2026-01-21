import streamlit as st
from config import fetch_details, execute_query
import pandas as pd
import datetime
import subject_config  # Core subject engine


# -------------------------------------------------------------
# Authentication Helper
# -------------------------------------------------------------
def require_admin_access(func):
    """Decorator to require admin access for functions"""
    def wrapper(*args, **kwargs):
        if "username" not in st.session_state:
            st.error("⚠️ Please log in to access this page")
            st.stop()
        
        user_type = st.session_state.get("user_type", "")
        if user_type != "admin":
            st.error("⛔ Access Denied: Admin privileges required.")
            st.info("Please contact system administrator for access.")
            st.stop()
        
        return func(*args, **kwargs)
    return wrapper


# -------------------------------------------------------------
# Admin Dashboard
# -------------------------------------------------------------
def admin_dashboard():
    st.sidebar.title("🧭 Admin Panel")
    
    # Check if user is logged in
    if "username" not in st.session_state:
        st.error("⚠️ Please log in to access the admin dashboard")
        if st.button("Go to Login"):
            st.switch_page("app.py")  # Adjust to your main app file
        st.stop()
    
    # Ensure user_type is set (for backward compatibility)
    if "user_type" not in st.session_state:
        st.session_state.user_type = "admin"
    
    st.sidebar.markdown(f"**Welcome, {st.session_state.username}**")
    st.sidebar.markdown(f"*Role: Administrator*")
    st.sidebar.markdown("---")
    
    choice = st.sidebar.radio("Menu", [
        "Dashboard", "Manage Students", "Add Student", "Manage Faculty", 
        "Add Faculty", "Manage Subjects", "Student Reports", "Faculty Reports", 
        "Fees Management", "System Analytics", "Fix Broken Links", "Logout"
    ])

    st.title("🧑‍💼 Admin Dashboard")

    if choice == "Dashboard":
        show_admin_dashboard()
    elif choice == "Manage Students":
        manage_students()
    elif choice == "Add Student":
        add_student()
    elif choice == "Manage Faculty":
        manage_faculty()
    elif choice == "Add Faculty":
        add_faculty()
    elif choice == "Manage Subjects":
        manage_student_subjects()
    elif choice == "Student Reports":
        student_reports()
    elif choice == "Faculty Reports":
        faculty_reports()
    elif choice == "System Analytics":
        system_analytics()
    elif choice == "Fees Management":
        manage_fees()
    elif choice == "Fix Broken Links":
        fix_broken_links()
    elif choice == "Logout":
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()


# -------------------------------------------------------------
# Dashboard Overview
# -------------------------------------------------------------
def show_admin_dashboard():
    st.subheader("📊 System Overview")
    
    try:
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            student_count = fetch_details("SELECT COUNT(*) FROM student_details")
            st.metric("Total Students", student_count[0][0] if student_count else 0)
        
        with col2:
            faculty_count = fetch_details("SELECT COUNT(*) FROM faculty_details")
            st.metric("Total Faculty", faculty_count[0][0] if faculty_count else 0)
        
        with col3:
            total_attendance = fetch_details("SELECT COUNT(*) FROM attendance")
            st.metric("Attendance Records", total_attendance[0][0] if total_attendance else 0)
        
        with col4:
            total_fees = fetch_details("SELECT SUM(amount) FROM fees WHERE status='Paid'")
            amount = total_fees[0][0] if total_fees and total_fees[0][0] else 0
            st.metric("Total Fees Collected", f"₹{amount:,.2f}")
    
    except Exception as e:
        st.error(f"Error loading dashboard stats: {str(e)}")

    st.write("---")
    st.subheader("🚀 Quick Actions")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📋 View All Students"):
            st.session_state.admin_choice = "Manage Students"
            st.rerun()
        if st.button("👨‍🏫 View All Faculty"):
            st.session_state.admin_choice = "Manage Faculty"
            st.rerun()
    
    with col2:
        if st.button("📚 Manage Subjects"):
            st.session_state.admin_choice = "Manage Subjects"
            st.rerun()
        if st.button("📊 Student Reports"):
            st.session_state.admin_choice = "Student Reports"
            st.rerun()


# -------------------------------------------------------------
# Manage Students
# -------------------------------------------------------------
def manage_students():
    st.subheader("📋 Student Management")
    
    try:
        students = fetch_details("SELECT id, name, age, sex, phoneno FROM student_details ORDER BY name")
        if not students:
            st.info("No student records found.")
            return

        st.write(f"**Total Students: {len(students)}**")
        search_term = st.text_input("🔍 Search students by name:")
        
        filtered_students = [s for s in students if search_term.lower() in s[1].lower()] if search_term else students
        
        if search_term:
            st.write(f"**Found {len(filtered_students)} students matching '{search_term}'**")
        
        for student in filtered_students:
            with st.container():
                col1, col2, col3, col4, col5 = st.columns([3, 2, 2, 2, 1])
                with col1: st.write(f"**{student[1]}** (ID: {student[0]})")
                with col2: st.write(f"Age: {student[2]}")
                with col3: st.write(f"Gender: {student[3]}")
                with col4: st.write(f"📞 {student[4]}")
                with col5:
                    if st.button("🗑️", key=f"del_stu_{student[0]}"):
                        delete_student(student[0], student[1])
                st.divider()
                
    except Exception as e:
        st.error(f"Error loading student management: {str(e)}")


# -------------------------------------------------------------
# Add New Student
# -------------------------------------------------------------
def add_student():
    st.subheader("➕ Add New Student")
    
    with st.form("add_student_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input("Full Name*")
            age = st.number_input("Age*", min_value=5, max_value=60, value=18)
            phone = st.text_input("Phone Number*")
        
        with col2:
            gender = st.selectbox("Gender*", ["Male", "Female", "Other"])
            username = st.text_input("Username*")
            password = st.text_input("Password*", type="password")
            email = st.text_input("Email Address")
        
        submitted = st.form_submit_button("Add Student")
        
        if submitted and all([name, age, phone, gender, username, password]):
            try:
                # Check if username exists
                existing_user = fetch_details(
                    "SELECT * FROM login_details WHERE uname=%s", (username,)
                )
                if existing_user:
                    st.error(f"❌ Username '{username}' already exists.")
                    return
                
                # Check if phone exists
                existing_phone = fetch_details(
                    "SELECT * FROM student_details WHERE phoneno=%s", (phone,)
                )
                if existing_phone:
                    st.error(f"❌ Phone number '{phone}' already registered.")
                    return
                
                student_success = execute_query(
                    "INSERT INTO student_details (name, age, sex, phoneno) VALUES (%s, %s, %s, %s)",
                    (name, age, gender, phone)
                )
                
                if student_success:
                    student_id_result = fetch_details(
                        "SELECT id FROM student_details WHERE name=%s AND phoneno=%s", 
                        (name, phone)
                    )
                    
                    if student_id_result:
                        student_id = student_id_result[0][0]
                        login_success = execute_query(
                            """INSERT INTO login_details 
                               (uname, password, typeOfUser, email, phoneno, user_id) 
                               VALUES (%s, %s, %s, %s, %s, %s)""",
                            (username, password, "student", email, phone, student_id)
                        )
                        
                        if login_success:
                            st.success(f"✅ Student '{name}' added successfully!")
                            st.info(f"**Username:** {username} | **Password:** {password}")
                            st.balloons()
                        else:
                            # Rollback student addition
                            execute_query("DELETE FROM student_details WHERE id=%s", (student_id,))
                            st.error("❌ Failed to create login credentials")
                    else:
                        st.error("❌ Failed to retrieve student ID")
                else:
                    st.error("❌ Failed to add student to database")
                    
            except Exception as e:
                st.error(f"Error adding student: {str(e)}")
        elif submitted:
            st.error("Please fill all required fields (*)")


# -------------------------------------------------------------
# Add New Faculty - FIXED VERSION
# -------------------------------------------------------------
@require_admin_access
def add_faculty():
    st.subheader("➕ Add New Faculty")
    
    with st.form("add_faculty_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            # Personal Information
            st.write("### 👤 Personal Information")
            name = st.text_input("Full Name*")
            
            # Department selection
            try:
                departments = subject_config.get_all_departments()
                if not departments:
                    departments = ["B.Tech", "MBA", "Pharmacy", "Other"]
            except:
                departments = ["B.Tech", "MBA", "Pharmacy", "Other"]
            
            department = st.selectbox("Department*", departments, key="add_fac_dept")
            
            # Course selection based on department
            course_options = ["-- Select Course --"]
            if department and department != "Other":
                try:
                    # Try to get courses from subject_config
                    if hasattr(subject_config, 'DEPARTMENT_COURSES') and department in subject_config.DEPARTMENT_COURSES:
                        course_options = list(subject_config.DEPARTMENT_COURSES[department].keys())
                    elif hasattr(subject_config, 'get_courses_for_department'):
                        course_options = subject_config.get_courses_for_department(department)
                except Exception as e:
                    st.warning(f"Could not load courses: {str(e)}")
                    
                    # Fallback courses
                    if department == "B.Tech":
                        course_options = ["Computer Science (CS)", "Mechanical Engineering (ME)", 
                                        "Civil Engineering (CE)", "Electrical Engineering (EE)", 
                                        "Electronics & Communication (EC)"]
                    elif department == "MBA":
                        course_options = ["Finance", "Marketing", "HR"]
                    elif department == "Pharmacy":
                        course_options = ["Pharmaceutics", "Pharmacology"]
            elif department == "Other":
                course_options = ["General", "Other"]
            
            course = st.selectbox(
                "Course*", 
                course_options, 
                key=f"faculty_course_select",
                help="Select the course/program the faculty will teach in"
            )
            
            # Teaching Assignment
            st.write("### 📚 Teaching Assignment")
            
            # Year selection
            year = st.selectbox(
                "Academic Year",
                ["Not Specified", "1st Year", "2nd Year", "3rd Year", "4th Year", "5th Year"],
                help="Select which year(s) the faculty will teach"
            )
            
            # Semester selection
            semester = st.selectbox(
                "Semester",
                ["Not Specified", "1st Semester", "2nd Semester", "3rd Semester", "4th Semester", 
                 "5th Semester", "6th Semester", "7th Semester", "8th Semester"],
                help="Select which semester(s) the faculty will teach"
            )
            
            # Subject selection based on course
            subject_suggestions = []
            if course and course != "-- Select Course --" and department and department != "Other":
                try:
                    # Get subjects from subject_config
                    if hasattr(subject_config, 'DEPARTMENT_COURSES'):
                        if department in subject_config.DEPARTMENT_COURSES:
                            if course in subject_config.DEPARTMENT_COURSES[department]:
                                subject_suggestions = subject_config.DEPARTMENT_COURSES[department][course]
                    elif hasattr(subject_config, 'get_subjects_for_course'):
                        subject_suggestions = subject_config.get_subjects_for_course(department, course)
                except:
                    subject_suggestions = []
            
            # Subject input
            if subject_suggestions:
                st.write("**Suggested Subjects:**")
                for i, subj in enumerate(subject_suggestions[:5]):  # Show first 5 suggestions
                    st.caption(f"• {subj}")
                
                subject = st.text_input(
                    "Primary Subject*",
                    placeholder="e.g., Data Structures, Thermodynamics, Pharmacology",
                    help="Enter the main subject this faculty specializes in"
                )
            else:
                subject = st.text_input(
                    "Primary Subject*",
                    placeholder="e.g., Data Structures, Thermodynamics, Pharmacology",
                    help="Main subject this faculty specializes in"
                )
        
        with col2:
            # Contact Information
            st.write("### 📞 Contact Information")
            phone = st.text_input("Phone Number*", max_chars=15)
            email = st.text_input("Email Address")
            
            # Login Credentials
            st.write("### 🔐 Login Credentials")
            username = st.text_input("Username*")
            password = st.text_input("Password*", type="password")
            confirm_password = st.text_input("Confirm Password*", type="password")
            
            # Optional fields
            st.write("### 🎓 Professional Details (Optional)")
            qualification = st.text_input("Highest Qualification", 
                                         placeholder="e.g., Ph.D, M.Tech, M.Pharm")
            designation = st.selectbox(
                "Designation",
                ["Not Specified", "Professor", "Associate Professor", "Assistant Professor", "Lecturer"]
            )
        
        # Submit button
        col_submit1, col_submit2, col_submit3 = st.columns([2, 1, 2])
        with col_submit2:
            submitted = st.form_submit_button("➕ Add Faculty", use_container_width=True)
        
        if submitted:
            # Validation
            required_fields = [name, department, phone, username, password, confirm_password, subject]
            
            if course == "-- Select Course --":
                st.error("❌ Please select a valid course")
                return
                
            if any(not field for field in required_fields):
                st.error("❌ Please fill all required fields (*)")
                return
            
            if password != confirm_password:
                st.error("❌ Passwords do not match!")
                return
            
            if len(password) < 6:
                st.error("❌ Password must be at least 6 characters long")
                return
            
            try:
                # Step 1: Check if username already exists
                existing_user = fetch_details(
                    "SELECT * FROM login_details WHERE uname = %s", (username,)
                )
                if existing_user:
                    st.error(f"❌ Username '{username}' already exists. Please choose a different one.")
                    return
                
                # Step 2: Check if phone already exists
                existing_phone = fetch_details(
                    "SELECT * FROM faculty_details WHERE phoneno = %s", (phone,)
                )
                if existing_phone:
                    st.error(f"❌ Phone number '{phone}' is already registered.")
                    return
                
                # Step 3: Add faculty to faculty_details table
                faculty_success = execute_query(
                    "INSERT INTO faculty_details (name, department, phoneno, qualification) VALUES (%s, %s, %s, %s)",
                    (name, department, phone, qualification or "")
                )
                
                if not faculty_success:
                    st.error("❌ Failed to add faculty to faculty_details table.")
                    return
                
                # Step 4: Get the inserted faculty ID
                faculty_id_result = fetch_details("SELECT LAST_INSERT_ID()")
                
                if not faculty_id_result:
                    st.error("❌ Could not retrieve faculty ID.")
                    return
                
                faculty_id = faculty_id_result[0][0]
                
                # Step 5: Add teaching details to faculty_teaching table
                try:
                    teaching_success = execute_query(
                        """INSERT INTO faculty_teaching 
                           (faculty_id, course, subject, year, semester, designation) 
                           VALUES (%s, %s, %s, %s, %s, %s)""",
                        (faculty_id, course, subject, 
                         year if year != "Not Specified" else "", 
                         semester if semester != "Not Specified" else "",
                         designation if designation != "Not Specified" else "")
                    )
                    
                    if not teaching_success:
                        st.warning("⚠️ Faculty added but could not save teaching details.")
                except Exception as e:
                    st.warning(f"⚠️ Could not save teaching details: {str(e)}")
                
                # Step 6: Add login credentials
                login_success = execute_query(
                    """INSERT INTO login_details 
                       (uname, password, typeOfUser, email, phoneno, user_id) 
                       VALUES (%s, %s, %s, %s, %s, %s)""",
                    (username, password, "faculty", email or "", phone, faculty_id)
                )
                
                # Step 7: Verify the link was created
                if login_success:
                    # Verify the link
                    verify_link = fetch_details(
                        "SELECT user_id FROM login_details WHERE uname = %s", 
                        (username,)
                    )
                    
                    if verify_link and verify_link[0][0] == faculty_id:
                        st.success(f"✅ Faculty '{name}' added successfully!")
                        st.balloons()
                        
                        # Display success summary
                        st.write("---")
                        st.write("### ✅ Faculty Details")
                        
                        cols = st.columns(3)
                        with cols[0]:
                            st.info(f"**Name:** {name}")
                            st.info(f"**Department:** {department}")
                        with cols[1]:
                            st.info(f"**Course:** {course}")
                            st.info(f"**Username:** {username}")
                        with cols[2]:
                            st.info(f"**Subject:** {subject}")
                            if designation != "Not Specified":
                                st.info(f"**Designation:** {designation}")
                        
                        # Show faculty ID
                        st.warning(f"**Important:** Faculty ID `{faculty_id}` has been linked to username `{username}`")
                        
                    else:
                        # Fix the broken link
                        execute_query(
                            "UPDATE login_details SET user_id = %s WHERE uname = %s",
                            (faculty_id, username)
                        )
                        st.success(f"✅ Faculty '{name}' added (link fixed)!")
                        
                    # Add a button to refresh the form
                    if st.button("🔄 Add Another Faculty"):
                        st.rerun()
                        
                else:
                    # Rollback: Remove faculty if login creation fails
                    execute_query("DELETE FROM faculty_details WHERE id = %s", (faculty_id,))
                    execute_query("DELETE FROM faculty_teaching WHERE faculty_id = %s", (faculty_id,))
                    st.error("❌ Failed to create login credentials. Faculty record rolled back.")
                    
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
                import traceback
                st.error(f"**Debug Info:** {traceback.format_exc()}")
    
    # Show recently added faculty
    with st.expander("📋 Recently Added Faculty"):
        try:
            recent_faculty = fetch_details("""
                SELECT f.id, f.name, f.department, ft.course, ft.subject 
                FROM faculty_details f
                LEFT JOIN faculty_teaching ft ON f.id = ft.faculty_id
                ORDER BY f.id DESC 
                LIMIT 5
            """)
            
            if recent_faculty:
                for fac_id, name, dept, course, subject in recent_faculty:
                    st.write(f"👨‍🏫 **{name}** (ID: {fac_id}) - {dept}")
                    if course:
                        st.write(f"   📚 {course}")
                    if subject:
                        st.write(f"   📖 {subject}")
                    st.divider()
            else:
                st.info("No faculty added yet.")
        except Exception as e:
            st.warning(f"Could not load recent faculty: {str(e)}")

# -------------------------------------------------------------
# Manage Faculty
# -------------------------------------------------------------
def manage_faculty():
    st.subheader("👨‍🏫 Faculty Management")
    
    try:
        faculty = fetch_details("""
            SELECT 
                f.id, f.name, f.department, f.phoneno,
                ft.course, ft.subject, ft.year, ft.semester
            FROM faculty_details f
            LEFT JOIN faculty_teaching ft ON f.id = ft.faculty_id
            ORDER BY f.name
        """)
        
        if not faculty:
            st.info("No faculty records found.")
            return

        faculty_dict = {}
        for row in faculty:
            fac_id = row[0]
            if fac_id not in faculty_dict:
                faculty_dict[fac_id] = {
                    'id': fac_id,
                    'name': row[1],
                    'department': row[2],
                    'phone': row[3],
                    'teaching': []
                }
            if row[4]:  # course
                faculty_dict[fac_id]['teaching'].append({
                    'course': row[4],
                    'subject': row[5],
                    'year': row[6],
                    'semester': row[7]
                })

        st.write(f"**Total Faculty: {len(faculty_dict)}**")
        search_term = st.text_input("🔍 Search faculty by name:")
        
        if search_term:
            filtered_faculty = {k: v for k, v in faculty_dict.items() 
                              if search_term.lower() in v['name'].lower()}
        else:
            filtered_faculty = faculty_dict
        
        if search_term:
            st.write(f"**Found {len(filtered_faculty)} faculty matching '{search_term}'**")
        
        for fac_id, info in filtered_faculty.items():
            with st.container():
                col1, col2, col3, col4, col5, col6 = st.columns([3, 2, 2, 2, 1, 1])
                with col1: 
                    st.write(f"**{info['name']}** (ID: {info['id']})")
                with col2: 
                    st.write(f"Dept: {info['department']}")
                with col3: 
                    st.write(f"📞 {info['phone']}")
                with col4:
                    if info['teaching']:
                        primary_subject = info['teaching'][0]['subject']
                        st.write(f"Subject: {primary_subject[:20]}..." if len(primary_subject) > 20 else f"Subject: {primary_subject}")
                    else:
                        st.write("No subjects")
                with col5:
                    if st.button("🛠️ Fix", key=f"fix_fac_{info['id']}"):
                        fix_faculty_link_manual(info['id'], info['name'])
                with col6:
                    if st.button("🗑️", key=f"del_fac_{info['id']}"):
                        delete_faculty(info['id'], info['name'])
                
                if info['teaching']:
                    with st.expander("📋 View Teaching Details"):
                        for teach in info['teaching']:
                            col_a, col_b, col_c = st.columns(3)
                            with col_a:
                                st.write(f"**Course:** {teach['course']}")
                            with col_b:
                                st.write(f"**Subject:** {teach['subject']}")
                            with col_c:
                                if teach['year']:
                                    st.write(f"**Year:** {teach['year']}")
                                if teach['semester']:
                                    st.write(f"**Semester:** {teach['semester']}")
                            st.divider()
                
                try:
                    # Check login link
                    login_info = fetch_details("""
                        SELECT uname, user_id FROM login_details 
                        WHERE user_id=%s AND typeOfUser='faculty'
                    """, (fac_id,))
                    
                    if login_info:
                        login_name, login_user_id = login_info[0]
                        if login_user_id == fac_id:
                            st.success(f"✅ Linked to login: {login_name}")
                        else:
                            st.error(f"❌ Broken link: Login {login_name} has wrong user_id {login_user_id}")
                    else:
                        st.warning("⚠️ No login account linked")
                        
                except:
                    pass
                
                st.divider()
                
    except Exception as e:
        st.error(f"Error loading faculty management: {str(e)}")
        import traceback
        st.error(f"Debug: {traceback.format_exc()}")


# -------------------------------------------------------------
# Manage Student Subjects
# -------------------------------------------------------------
def manage_student_subjects():
    st.subheader("📚 Manage Student Subjects")
    
    tab1, tab2, tab3 = st.tabs(["➕ Assign Courses", "📋 View Assignments", "🗑️ Remove Assignments"])
    
    try:
        students = fetch_details("SELECT id, name FROM student_details ORDER BY name")
        faculty = fetch_details("SELECT id, name, department FROM faculty_details ORDER BY name")
        
        if not students or not faculty:
            st.error("No students or faculty found.")
            return
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        return

    # =========================================================
    # TAB 1: ASSIGN COURSES
    # =========================================================
    with tab1:
        st.write("### Assign Courses to Students")
        
        with st.form("assign_course_form"):
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                # Department selection
                departments = subject_config.get_all_departments()
                selected_dept = st.selectbox("Department*", departments, key="admin_dept")
                
                # Display department info
                if selected_dept:
                    dept_courses = subject_config.get_courses_for_department(selected_dept)
                    st.caption(f"{len(dept_courses)} courses available")
            
            with col2:
                # Course selection based on department
                if selected_dept:
                    courses = subject_config.get_courses_for_department(selected_dept)
                    selected_course = st.selectbox("Select Course*", courses, key="admin_course")
                else:
                    selected_course = st.selectbox("Select Course*", ["Select department first"], disabled=True)
                
                # Show course info
                if selected_course and selected_course != "Select department first":
                    st.caption(f"Course selected")
            
            with col3:
                # Filter faculty by selected department
                if selected_dept:
                    dept_faculty = [f for f in faculty if f[2] == selected_dept]
                else:
                    dept_faculty = faculty
                
                if dept_faculty:
                    faculty_options = [f"{f[1]} (ID: {f[0]})" for f in dept_faculty]
                    selected_faculty_display = st.selectbox("Assign Faculty*", faculty_options, key="admin_faculty")
                    
                    # Extract faculty ID
                    if selected_faculty_display:
                        try:
                            faculty_id = int(selected_faculty_display.split("(ID: ")[1].replace(")", ""))
                        except:
                            faculty_id = None
                            st.error("Could not parse faculty ID")
                    else:
                        faculty_id = None
                else:
                    st.warning(f"No faculty found for {selected_dept}")
                    faculty_id = None
            
            with col4:
                # Display summary
                st.write("**Summary:**")
                if selected_dept:
                    st.caption(f"Dept: {selected_dept}")
                if selected_course and selected_course != "Select department first":
                    st.caption(f"Course: {selected_course}")
                if faculty_id:
                    st.caption("Faculty: Selected")
            
            st.divider()
            
            # Student selection
            student_options = [f"{s[1]} (ID: {s[0]})" for s in students]
            selected_student = st.selectbox("Select Student*", student_options, key="admin_student")
            
            # Extract student ID
            student_id = None
            if selected_student and "(ID:" in selected_student:
                try:
                    student_id = int(selected_student.split("(ID: ")[1].replace(")", ""))
                except:
                    student_id = None

            # Submit button
            submit_col1, submit_col2 = st.columns([3, 1])
            with submit_col2:
                submitted = st.form_submit_button("🎯 Assign Course", use_container_width=True)

            if submitted:
                # Validate all fields
                if not all([student_id, selected_course, faculty_id]):
                    st.error("Please fill all required fields (*)")
                    return
                
                if selected_course == "Select department first":
                    st.error("Please select a valid course")
                    return

                try:
                    # Check if already assigned
                    existing = fetch_details("""
                        SELECT * FROM results 
                        WHERE student_id=%s AND course=%s AND faculty_id=%s
                    """, (student_id, selected_course, faculty_id))

                    if existing:
                        st.warning(f"⚠️ '{selected_course}' already assigned to this student with this faculty.")
                    else:
                        success = execute_query("""
                            INSERT INTO results (student_id, course, faculty_id, grade) 
                            VALUES (%s, %s, %s, NULL)
                        """, (student_id, selected_course, faculty_id))

                        if success:
                            st.success(f"✅ Course '{selected_course}' assigned!")
                            st.balloons()
                        else:
                            st.error("❌ Failed to assign course")
                            
                except Exception as e:
                    st.error(f"Error assigning course: {str(e)}")

        # Department-course mapping display
        with st.expander("📋 Department-Course Mapping"):
            summary = subject_config.get_course_summary()
            
            for dept in summary["departments"]:
                dept_info = summary["courses_by_dept"][dept]
                st.write(f"**{dept}** ({dept_info['count']} courses):")
                for course in dept_info["courses"]:
                    st.write(f"- {course}")
                st.write("")

    # =========================================================
    # TAB 2: VIEW ASSIGNMENTS
    # =========================================================
    with tab2:
        st.write("### Current Course Assignments")
        
        try:
            assignments = fetch_details("""
                SELECT s.name, r.course, f.name, r.grade, s.id as student_id
                FROM results r
                JOIN student_details s ON r.student_id = s.id
                JOIN faculty_details f ON r.faculty_id = f.id
                ORDER BY s.name, r.course
            """)
            
            if not assignments:
                st.info("No assignments found.")
                return

            # Group by student
            students_dict = {}
            for student, course, faculty, grade, student_id in assignments:
                if student not in students_dict:
                    students_dict[student] = []
                students_dict[student].append({
                    'course': course, 
                    'faculty': faculty, 
                    'grade': grade,
                    'student_id': student_id
                })
            
            # Search filter
            search_term = st.text_input("🔍 Search students:", key="search_assignments")
            
            filtered_students = {}
            if search_term:
                for student, subjects in students_dict.items():
                    if search_term.lower() in student.lower():
                        filtered_students[student] = subjects
                    else:
                        # Check if search term matches any course
                        for subject_info in subjects:
                            if search_term.lower() in subject_info['course'].lower():
                                filtered_students[student] = subjects
                                break
            else:
                filtered_students = students_dict
            
            st.write(f"**Showing {len(filtered_students)} students**")
            
            for student, subjects in filtered_students.items():
                with st.expander(f"🎓 {student} - {len(subjects)} courses"):
                    # Display courses
                    for subject in subjects:
                        col1, col2, col3 = st.columns([3, 2, 1])
                        with col1: 
                            st.write(f"📚 {subject['course']}")
                        with col2: 
                            st.write(f"👨‍🏫 {subject['faculty']}")
                        with col3:
                            grade = subject['grade']
                            if not grade: 
                                st.info("No Grade")
                            elif grade.startswith("A"): 
                                st.success(f"**{grade}**")
                            elif grade.startswith("B"): 
                                st.info(f"**{grade}**")
                            elif grade.startswith("C"): 
                                st.warning(f"**{grade}**")
                            else: 
                                st.error(f"**{grade}**")
                        st.divider()
        except Exception as e:
            st.error(f"Error loading assignments: {str(e)}")

    # =========================================================
    # TAB 3: REMOVE ASSIGNMENTS
    # =========================================================
    with tab3:
        st.write("### Remove Course Assignment")
    
        try:
            assignments = fetch_details("""
                SELECT r.id, s.name, r.course, f.name, f.department
                FROM results r
                JOIN student_details s ON r.student_id = s.id
                JOIN faculty_details f ON r.faculty_id = f.id
                ORDER BY s.name, r.course
            """)
            
            if not assignments:
                st.info("No assignments to remove.")
                return
            
            # Search filter
            search_term = st.text_input("🔍 Search:", key="search_remove")
            
            filtered_assignments = assignments
            if search_term:
                filtered_assignments = [
                    a for a in assignments 
                    if search_term.lower() in a[1].lower() or search_term.lower() in a[2].lower()
                ]
            
            st.write(f"**Found {len(filtered_assignments)} assignments**")
            
            for assignment_id, student, course, faculty, dept in filtered_assignments:
                col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
                with col1: 
                    st.write(f"**{student}**")
                with col2: 
                    st.write(f"**{course}**")
                with col3: 
                    st.write(f"👨‍🏫 {faculty}")
                with col4:
                    if st.button("🗑️", key=f"remove_{assignment_id}"):
                       try:
                           if execute_query("DELETE FROM results WHERE id=%s", (assignment_id,)):
                               st.success(f"✅ Removed '{course}' from {student}!")
                               st.rerun()
                           else:
                               st.error("❌ Failed to remove")
                       except Exception as e:
                           st.error(f"Error: {str(e)}")
                st.divider()
        except Exception as e:
            st.error(f"Error loading removal data: {str(e)}")


# -------------------------------------------------------------
# STUDENT REPORTS
# -------------------------------------------------------------
def student_reports():
    st.subheader("📊 Student Comprehensive Reports")
    
    tab1, tab2, tab3, tab4 = st.tabs(["🎯 Grades", "📅 Attendance", "💰 Fees", "📈 Performance"])

    with tab1:
        try:
            grades_data = fetch_details("""
                SELECT s.name, r.course, r.grade, f.name
                FROM results r
                JOIN student_details s ON r.student_id = s.id
                JOIN faculty_details f ON r.faculty_id = f.id
                WHERE r.course IS NOT NULL AND TRIM(r.course) != ''
                ORDER BY s.name, r.course
            """)
            if grades_data:
                df = pd.DataFrame(grades_data, columns=["Student", "Course", "Grade", "Faculty"])
                st.dataframe(df, use_container_width=True)
                
                # Summary statistics
                col1, col2, col3 = st.columns(3)
                with col1:
                    total_students = df['Student'].nunique()
                    st.metric("Total Students", total_students)
                with col2:
                    total_subjects = len(df)
                    st.metric("Total Subjects", total_subjects)
                with col3:
                    graded = df['Grade'].notna().sum()
                    st.metric("Graded Subjects", graded)
            else:
                st.info("No grade records found.")
        except Exception as e:
            st.error(f"Error loading grades: {str(e)}")

    with tab2:
        try:
            attendance = fetch_details("SELECT student_name, date, status FROM attendance ORDER BY date DESC LIMIT 100")
            if attendance:
                df = pd.DataFrame(attendance, columns=["Student", "Date", "Status"])
                st.dataframe(df, use_container_width=True)
                
                # Attendance summary
                present = df[df['Status'] == 'Present'].shape[0]
                absent = df[df['Status'] == 'Absent'].shape[0]
                total = len(df)
                
                if total > 0:
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Present", present)
                    with col2:
                        st.metric("Absent", absent)
                    with col3:
                        percentage = (present / total) * 100
                        st.metric("Attendance %", f"{percentage:.1f}%")
            else:
                st.info("No attendance records.")
        except Exception as e:
            st.error(f"Error loading attendance: {str(e)}")

    with tab3:
        try:
            fees = fetch_details("SELECT student_name, amount, due_date, status FROM fees ORDER BY due_date DESC")
            if fees:
                df = pd.DataFrame(fees, columns=["Student", "Amount", "Due Date", "Status"])
                st.dataframe(df, use_container_width=True)
                
                # Fee summary
                total_fees = df['Amount'].sum()
                paid = df[df['Status'] == 'Paid']['Amount'].sum()
                pending = df[df['Status'] == 'Pending']['Amount'].sum()
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Fees", f"₹{total_fees:,.2f}")
                with col2:
                    st.metric("Paid", f"₹{paid:,.2f}")
                with col3:
                    st.metric("Pending", f"₹{pending:,.2f}")
            else:
                st.info("No fee records.")
        except Exception as e:
            st.error(f"Error loading fees: {str(e)}")

    with tab4:
        try:
            gpa_data = fetch_details("""
                SELECT s.name,
                       AVG(CASE 
                           WHEN r.grade IN ('A+', 'A') THEN 4.0
                           WHEN r.grade = 'A-' THEN 3.7
                           WHEN r.grade = 'B+' THEN 3.3
                           WHEN r.grade = 'B' THEN 3.0
                           WHEN r.grade = 'B-' THEN 2.7
                           WHEN r.grade = 'C+' THEN 2.3
                           WHEN r.grade = 'C' THEN 2.0
                           WHEN r.grade = 'C-' THEN 1.7
                           WHEN r.grade = 'D' THEN 1.0
                           WHEN r.grade = 'F' THEN 0.0
                           ELSE NULL END) as gpa
                FROM student_details s
                JOIN results r ON s.id = r.student_id
                WHERE r.grade IS NOT NULL
                GROUP BY s.id, s.name
                HAVING gpa IS NOT NULL
                ORDER BY gpa DESC
            """)
            if gpa_data:
                df = pd.DataFrame(gpa_data, columns=["Student", "GPA"])
                st.dataframe(df.round(2), use_container_width=True)
                
                # GPA statistics
                if not df.empty:
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        avg_gpa = df['GPA'].mean()
                        st.metric("Average GPA", f"{avg_gpa:.2f}")
                    with col2:
                        max_gpa = df['GPA'].max()
                        st.metric("Highest GPA", f"{max_gpa:.2f}")
                    with col3:
                        min_gpa = df['GPA'].min()
                        st.metric("Lowest GPA", f"{min_gpa:.2f}")
            else:
                st.info("No GPA data available.")
        except Exception as e:
            st.error(f"Error loading performance: {str(e)}")


# -------------------------------------------------------------
# FACULTY REPORTS — FULL IMPLEMENTATION
# -------------------------------------------------------------
def faculty_reports():
    st.subheader("👨‍🏫 Faculty Performance Reports")
    
    try:
        data = fetch_details("""
            SELECT f.name, f.department,
                   COUNT(DISTINCT r.student_id) as students,
                   COUNT(DISTINCT r.course) as courses,
                   AVG(CASE 
                       WHEN r.grade IN ('A+', 'A') THEN 4.0
                       WHEN r.grade = 'A-' THEN 3.7
                       WHEN r.grade = 'B+' THEN 3.3
                       WHEN r.grade = 'B' THEN 3.0
                       WHEN r.grade = 'B-' THEN 2.7
                       WHEN r.grade = 'C+' THEN 2.3
                       WHEN r.grade = 'C' THEN 2.0
                       WHEN r.grade = 'C-' THEN 1.7
                       WHEN r.grade = 'D' THEN 1.0
                       WHEN r.grade = 'F' THEN 0.0
                       ELSE NULL END) as avg_gpa
            FROM faculty_details f
            LEFT JOIN results r ON f.id = r.faculty_id
            WHERE f.department = 'B.Tech'
            GROUP BY f.id, f.name, f.department
            ORDER BY avg_gpa DESC NULLS LAST, students DESC
        """)
        if data:
            df = pd.DataFrame(data, columns=["Faculty", "Department", "Students", "Courses", "Avg GPA"])
            st.dataframe(df.round(2), use_container_width=True)
            
            # Summary
            total_faculty = len(df)
            total_students = df['Students'].sum()
            avg_students = df['Students'].mean() if total_faculty > 0 else 0
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Faculty", total_faculty)
            with col2:
                st.metric("Total Students", int(total_students))
            with col3:
                st.metric("Avg Students/Faculty", f"{avg_students:.1f}")
        else:
            st.info("No faculty performance data.")
    except Exception as e:
        st.error(f"Error loading faculty reports: {str(e)}")


# -------------------------------------------------------------
# SYSTEM ANALYTICS — FULL IMPLEMENTATION
# -------------------------------------------------------------
def system_analytics():
    st.subheader("📈 System-wide Analytics")
    
    # Row 1: Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        try:
            total_students = fetch_details("SELECT COUNT(*) FROM student_details")
            st.metric("Total Students", total_students[0][0] if total_students else 0)
        except:
            st.metric("Students", "N/A")
    
    with col2:
        try:
            total_faculty = fetch_details("SELECT COUNT(*) FROM faculty_details WHERE department='B.Tech'")
            st.metric("B.Tech Faculty", total_faculty[0][0] if total_faculty else 0)
        except:
            st.metric("Faculty", "N/A")
    
    with col3:
        try:
            total_subjects = fetch_details("SELECT COUNT(DISTINCT course) FROM results")
            st.metric("Active Subjects", total_subjects[0][0] if total_subjects else 0)
        except:
            st.metric("Subjects", "N/A")
    
    with col4:
        try:
            total_assignments = fetch_details("SELECT COUNT(*) FROM results")
            st.metric("Assignments", total_assignments[0][0] if total_assignments else 0)
        except:
            st.metric("Assignments", "N/A")
    
    st.write("---")
    
    # Row 2: Charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**📊 Attendance Distribution**")
        try:
            att_data = fetch_details("""
                SELECT status, COUNT(*) as count
                FROM attendance
                GROUP BY status
            """)
            if att_data:
                df = pd.DataFrame(att_data, columns=["Status", "Count"])
                st.bar_chart(df.set_index("Status"))
        except Exception as e:
            st.error(f"Error loading attendance analytics: {str(e)}")
    
    with col2:
        st.write("**💰 Fee Status Distribution**")
        try:
            fee_data = fetch_details("""
                SELECT status, SUM(amount) as total
                FROM fees
                GROUP BY status
            """)
            if fee_data:
                df = pd.DataFrame(fee_data, columns=["Status", "Amount"])
                st.bar_chart(df.set_index("Status"))
        except Exception as e:
            st.error(f"Error loading fee analytics: {str(e)}")
    
    # Row 3: Course distribution
    st.write("---")
    st.write("**📚 Course Distribution**")
    try:
        course_data = fetch_details("""
            SELECT 
                CASE 
                    WHEN r.course IN ('CS', 'CSE', 'Computer Science') THEN 'CS'
                    WHEN r.course IN ('ME', 'Mechanical') THEN 'ME'
                    WHEN r.course IN ('CE', 'Civil') THEN 'CE'
                    WHEN r.course IN ('EE', 'Electrical') THEN 'EE'
                    WHEN r.course IN ('EC', 'ECE', 'Electronics') THEN 'EC'
                    ELSE 'Other'
                END as course_group,
                COUNT(DISTINCT r.student_id) as students
            FROM results r
            GROUP BY course_group
            ORDER BY students DESC
        """)
        if course_data:
            df = pd.DataFrame(course_data, columns=["Course", "Students"])
            st.bar_chart(df.set_index("Course"))
    except Exception as e:
        st.error(f"Error loading course distribution: {str(e)}")


# -------------------------------------------------------------
# FEES MANAGEMENT
# -------------------------------------------------------------
def manage_fees():
    st.subheader("💰 Fees Management")
    
    tab1, tab2, tab3, tab4 = st.tabs(["➕ Add Fees", "📋 View All Fees", "✏️ Update Fees", "📊 Fees Analytics"])
    
    with tab1:
        with st.form("add_fee_form"):
            students = fetch_details("SELECT name FROM student_details ORDER BY name")
            student_names = [s[0] for s in students] if students else []
            
            col1, col2, col3 = st.columns(3)
            with col1:
                selected_student = st.selectbox("Select Student", student_names)
                fee_amount = st.number_input("Fee Amount (₹)", min_value=0, value=5000, step=500)
            with col2:
                due_date = st.date_input("Due Date", datetime.date.today() + datetime.timedelta(days=30))
                fee_status = st.selectbox("Status", ["Pending", "Paid", "Partial"])
            with col3:
                fee_type = st.selectbox("Fee Type", ["Tuition", "Exam", "Library", "Hostel", "Transport", "Other"])
                description = st.text_input("Description (Optional)")
            
            submitted = st.form_submit_button("💳 Add Fee Record")
            
            if submitted and selected_student and fee_amount > 0:
                try:
                    existing = fetch_details(
                        "SELECT * FROM fees WHERE student_name=%s AND due_date=%s AND amount=%s", 
                        (selected_student, due_date, fee_amount)
                    )
                    if existing:
                        st.warning("Similar record exists.")
                    else:
                        if execute_query(
                            "INSERT INTO fees (student_name, amount, due_date, status, fee_type, description) VALUES (%s, %s, %s, %s, %s, %s)",
                            (selected_student, fee_amount, due_date, fee_status, fee_type, description)
                        ):
                            st.success(f"✅ Added fee for {selected_student}!")
                            st.balloons()
                        else:
                            st.error("❌ Failed to add fee.")
                except Exception as e:
                    st.error(f"Error: {str(e)}")
            elif submitted:
                st.error("Please fill required fields.")

    with tab2:
        try:
            fees = fetch_details("SELECT student_name, amount, due_date, status, fee_type, description FROM fees ORDER BY due_date DESC")
            if fees:
                for student, amount, due_date, status, fee_type, description in fees:
                    col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 1, 2])
                    with col1: 
                        st.write(f"**{student}**")
                        if fee_type:
                            st.caption(f"{fee_type}")
                    with col2: 
                        st.write(f"₹{amount:,.2f}")
                    with col3: 
                        st.write(str(due_date))
                    with col4:
                        if status == "Paid":
                            st.success("Paid")
                        elif status == "Pending":
                            st.error("Pending")
                        else:
                            st.warning("Partial")
                    with col5:
                        if description:
                            st.caption(f"{description}")
                    st.divider()
            else:
                st.info("No fees found.")
        except Exception as e:
            st.error(f"Error loading fees: {str(e)}")

    with tab3:
        st.info("⚠️ Bulk update feature under development")
        st.write("To update individual fees:")
        st.write("1. Go to 'View All Fees' tab")
        st.write("2. Contact the student directly")
        st.write("3. Update status manually in database")

    with tab4:
        try:
            summary = fetch_details("""
                SELECT status, COUNT(*) as count, SUM(amount) as total
                FROM fees GROUP BY status
            """)
            if summary:
                for status, count, total in summary:
                    col1, col2 = st.columns(2)
                    with col1: 
                        st.metric(f"{status} Count", count)
                    with col2: 
                        st.metric(f"{status} Total", f"₹{total:,.2f}")
                
                # Total summary
                st.write("---")
                total_count = sum([s[1] for s in summary])
                total_amount = sum([s[2] for s in summary])
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Total Records", total_count)
                with col2:
                    st.metric("Total Amount", f"₹{total_amount:,.2f}")
        except Exception as e:
            st.error(f"Error loading analytics: {str(e)}")


# -------------------------------------------------------------
# FIX BROKEN LINKS - NEW FEATURE
# -------------------------------------------------------------
def fix_broken_links():
    st.subheader("🛠️ Fix Broken Account Links")
    
    st.warning("""
    **About Broken Links:**
    - Occurs when login accounts aren't properly linked to faculty/student records
    - Common error: "Your user profile is not linked to a faculty ID"
    """)
    
    tab1, tab2, tab3 = st.tabs(["🔍 Check Broken Links", "🔄 Auto-Fix Links", "🔧 Manual Fix"])
    
    with tab1:
        st.write("### Check for Broken Account Links")
        
        if st.button("🔍 Scan for Broken Links"):
            try:
                # Find faculty with broken links
                broken_faculty = fetch_details("""
                    SELECT ld.uname, ld.email, ld.phoneno, ld.user_id, f.name
                    FROM login_details ld
                    LEFT JOIN faculty_details f ON ld.user_id = f.id
                    WHERE ld.typeOfUser = 'faculty' 
                      AND (f.id IS NULL OR ld.user_id IS NULL OR ld.user_id = 0)
                """)
                
                if broken_faculty:
                    st.error(f"Found {len(broken_faculty)} broken faculty links:")
                    for uname, email, phone, user_id, faculty_name in broken_faculty:
                        st.write(f"👨‍🏫 **{uname}** → User ID: {user_id} | Faculty: {faculty_name or 'NOT FOUND'}")
                        
                        # Check if faculty exists by other means
                        if phone:
                            match = fetch_details(
                                "SELECT id, name FROM faculty_details WHERE phoneno = %s", 
                                (phone,)
                            )
                            if match:
                                st.success(f"   → Found match: {match[0][1]} (ID: {match[0][0]})")
                            else:
                                st.warning("   → No matching faculty found")
                        st.divider()
                else:
                    st.success("✅ No broken faculty links found!")
                
                # Find students with broken links
                broken_students = fetch_details("""
                    SELECT ld.uname, ld.email, ld.phoneno, ld.user_id, s.name
                    FROM login_details ld
                    LEFT JOIN student_details s ON ld.user_id = s.id
                    WHERE ld.typeOfUser = 'student' 
                      AND (s.id IS NULL OR ld.user_id IS NULL OR ld.user_id = 0)
                """)
                
                if broken_students:
                    st.error(f"Found {len(broken_students)} broken student links:")
                    for uname, email, phone, user_id, student_name in broken_students:
                        st.write(f"👨‍🎓 **{uname}** → User ID: {user_id} | Student: {student_name or 'NOT FOUND'}")
                        st.divider()
                else:
                    st.success("✅ No broken student links found!")
                    
            except Exception as e:
                st.error(f"Error scanning: {str(e)}")
    
    with tab2:
        st.write("### Auto-Fix Broken Links")
        
        if st.button("🔄 Run Auto-Fix", type="primary"):
            try:
                fixed_count = 0
                
                # Fix faculty links
                faculty_to_fix = fetch_details("""
                    SELECT ld.uname, ld.email, ld.phoneno 
                    FROM login_details ld
                    LEFT JOIN faculty_details f ON ld.user_id = f.id
                    WHERE ld.typeOfUser = 'faculty' AND f.id IS NULL
                """)
                
                for uname, email, phone in faculty_to_fix:
                    if phone:
                        # Try to match by phone
                        match = fetch_details(
                            "SELECT id FROM faculty_details WHERE phoneno = %s", 
                            (phone,)
                        )
                        if match:
                            faculty_id = match[0][0]
                            execute_query(
                                "UPDATE login_details SET user_id = %s WHERE uname = %s",
                                (faculty_id, uname)
                            )
                            fixed_count += 1
                            st.success(f"Fixed {uname} → Faculty ID: {faculty_id}")
                
                if fixed_count > 0:
                    st.success(f"✅ Auto-fixed {fixed_count} broken links!")
                else:
                    st.info("No broken links needed auto-fixing.")
                    
            except Exception as e:
                st.error(f"Error during auto-fix: {str(e)}")
    
    with tab3:
        st.write("### Manual Fix Tool")
        
        username = st.text_input("Enter Username to Fix (e.g., himanshu_24)")
        
        if username and st.button("🔧 Find and Fix"):
            try:
                # Get login details
                login_info = fetch_details(
                    "SELECT typeOfUser, email, phoneno, user_id FROM login_details WHERE uname = %s",
                    (username,)
                )
                
                if not login_info:
                    st.error(f"Username '{username}' not found!")
                    return
                
                user_type, email, phone, current_user_id = login_info[0]
                
                st.write(f"**User Type:** {user_type}")
                st.write(f"**Current User ID:** {current_user_id}")
                st.write(f"**Phone:** {phone}")
                st.write(f"**Email:** {email}")
                
                if user_type == "faculty":
                    # Find matching faculty
                    matches = []
                    if phone:
                        phone_matches = fetch_details(
                            "SELECT id, name FROM faculty_details WHERE phoneno = %s", 
                            (phone,)
                        )
                        if phone_matches:
                            matches.extend(phone_matches)
                    
                    if email:
                        email_matches = fetch_details(
                            "SELECT id, name FROM faculty_details WHERE email = %s", 
                            (email,)
                        )
                        if email_matches:
                            matches.extend([m for m in email_matches if m not in matches])
                    
                    # Also try name match
                    name_part = username.split('_')[0] if '_' in username else username
                    name_matches = fetch_details(
                        "SELECT id, name FROM faculty_details WHERE LOWER(name) LIKE %s",
                        (f"%{name_part.lower()}%",)
                    )
                    if name_matches:
                        matches.extend([m for m in name_matches if m not in matches])
                    
                    if matches:
                        st.success(f"Found {len(matches)} possible matches:")
                        for fac_id, fac_name in matches:
                            col1, col2, col3 = st.columns([2, 1, 1])
                            with col1:
                                st.write(f"**{fac_name}** (ID: {fac_id})")
                            with col2:
                                if st.button("Link", key=f"link_{fac_id}"):
                                    execute_query(
                                        "UPDATE login_details SET user_id = %s WHERE uname = %s",
                                        (fac_id, username)
                                    )
                                    st.success(f"✅ Linked {username} to {fac_name}!")
                                    st.rerun()
                    else:
                        st.warning("No matching faculty found.")
                        
                        # Option to create new faculty
                        if st.button("➕ Create New Faculty Profile"):
                            new_name = st.text_input("Faculty Full Name", value=name_part.title())
                            new_dept = st.selectbox("Department", ["B.Tech", "MBA", "Pharmacy", "Other"])
                            
                            if st.button("Create and Link"):
                                execute_query(
                                    "INSERT INTO faculty_details (name, department, phoneno) VALUES (%s, %s, %s)",
                                    (new_name, new_dept, phone or "")
                                )
                                new_id_result = fetch_details("SELECT LAST_INSERT_ID()")
                                if new_id_result:
                                    new_id = new_id_result[0][0]
                                    execute_query(
                                        "UPDATE login_details SET user_id = %s WHERE uname = %s",
                                        (new_id, username)
                                    )
                                    st.success(f"✅ Created faculty '{new_name}' and linked to {username}!")
                                    st.rerun()
                
                elif user_type == "student":
                    # Similar logic for students
                    st.info("Student fix functionality (similar to faculty)")
                    
            except Exception as e:
                st.error(f"Error: {str(e)}")


# -------------------------------------------------------------
# Delete Helpers
# -------------------------------------------------------------
def delete_faculty(faculty_id, faculty_name):
    try:
        # First check if faculty has assigned students
        assigned_students = fetch_details(
            "SELECT COUNT(*) FROM results WHERE faculty_id=%s", (faculty_id,)
        )
        
        if assigned_students and assigned_students[0][0] > 0:
            st.error(f"❌ Cannot delete {faculty_name}. They have {assigned_students[0][0]} assigned students.")
            return
        
        # Delete login first
        execute_query("DELETE FROM login_details WHERE user_id=%s AND typeOfUser='faculty'", (faculty_id,))
        
        # Delete faculty
        if execute_query("DELETE FROM faculty_details WHERE id=%s", (faculty_id,)):
            st.success(f"✅ Deleted {faculty_name}!")
            st.rerun()
        else:
            st.error("❌ Failed to delete.")
    except Exception as e:
        st.error(f"Error: {str(e)}")

def delete_student(student_id, student_name):
    try:
        # Check if student has records
        has_grades = fetch_details("SELECT COUNT(*) FROM results WHERE student_id=%s", (student_id,))
        has_fees = fetch_details("SELECT COUNT(*) FROM fees WHERE student_name=%s", (student_name,))
        has_attendance = fetch_details("SELECT COUNT(*) FROM attendance WHERE student_name=%s", (student_name,))
        
        total_records = (has_grades[0][0] if has_grades else 0) + \
                       (has_fees[0][0] if has_fees else 0) + \
                       (has_attendance[0][0] if has_attendance else 0)
        
        if total_records > 0:
            st.warning(f"⚠️ {student_name} has {total_records} records. Deleting will remove all associated data.")
            
            if st.button(f"Confirm Delete {student_name} and all records", key=f"confirm_del_{student_id}"):
                # Delete all associated records
                execute_query("DELETE FROM results WHERE student_id=%s", (student_id,))
                execute_query("DELETE FROM fees WHERE student_name=%s", (student_name,))
                execute_query("DELETE FROM attendance WHERE student_name=%s", (student_name,))
                execute_query("DELETE FROM login_details WHERE user_id=%s AND typeOfUser='student'", (student_id,))
                
                if execute_query("DELETE FROM student_details WHERE id=%s", (student_id,)):
                    st.success(f"✅ Deleted {student_name} and all associated records!")
                    st.rerun()
                else:
                    st.error("❌ Failed to delete.")
            return
        
        # No records, safe to delete
        execute_query("DELETE FROM login_details WHERE user_id=%s AND typeOfUser='student'", (student_id,))
        if execute_query("DELETE FROM student_details WHERE id=%s", (student_id,)):
            st.success(f"✅ Deleted {student_name}!")
            st.rerun()
        else:
            st.error("❌ Failed to delete.")
    except Exception as e:
        st.error(f"Error: {str(e)}")

def fix_faculty_link_manual(faculty_id, faculty_name):
    """Manual fix for faculty login links"""
    try:
        # Check current login link
        login_info = fetch_details(
            "SELECT uname FROM login_details WHERE user_id=%s AND typeOfUser='faculty'",
            (faculty_id,)
        )
        
        if login_info:
            current_username = login_info[0][0]
            st.info(f"Currently linked to: {current_username}")
            
            # Option to update
            new_username = st.text_input("New Username to Link", value=current_username)
            if st.button("Update Link"):
                execute_query(
                    "UPDATE login_details SET user_id = NULL WHERE uname = %s",
                    (current_username,)
                )
                execute_query(
                    "UPDATE login_details SET user_id = %s WHERE uname = %s",
                    (faculty_id, new_username)
                )
                st.success(f"✅ Updated link: {faculty_name} → {new_username}")
                st.rerun()
        else:
            st.warning("No login account linked")
            
            # Find available faculty logins
            available_logins = fetch_details("""
                SELECT uname FROM login_details 
                WHERE typeOfUser='faculty' AND (user_id IS NULL OR user_id = 0)
            """)
            
            if available_logins:
                login_options = [l[0] for l in available_logins]
                selected_login = st.selectbox("Select Login to Link", login_options)
                
                if st.button("Link This Account"):
                    execute_query(
                        "UPDATE login_details SET user_id = %s WHERE uname = %s",
                        (faculty_id, selected_login)
                    )
                    st.success(f"✅ Linked {faculty_name} to {selected_login}")
                    st.rerun()
            else:
                st.error("No available faculty logins. Create one first.")
                
    except Exception as e:
        st.error(f"Error fixing link: {str(e)}")