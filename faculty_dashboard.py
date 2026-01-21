import streamlit as st
from config import fetch_details, execute_query
import datetime
import pandas as pd
import subject_config
from ui_components import display_grade


# -------------------------------------------------------------
# HELPER: Fix Broken Faculty Links
# -------------------------------------------------------------
def fix_faculty_link(username):
    """Try to fix broken faculty login links automatically"""
    
    st.warning(f"🔧 Attempting to fix broken link for: {username}")
    
    # Method 1: Try to find by email or phone from login_details
    login_info = fetch_details(
        "SELECT email, phoneno FROM login_details WHERE uname = %s", 
        (username,)
    )
    
    if login_info:
        email, phone = login_info[0]
        
        # Try to find matching faculty by phone
        if phone and phone != "":
            faculty_match = fetch_details(
                "SELECT id, name FROM faculty_details WHERE phoneno = %s", 
                (phone,)
            )
            if faculty_match:
                faculty_id, faculty_name = faculty_match[0]
                st.info(f"Found match by phone: {faculty_name} (ID: {faculty_id})")
                return faculty_id
        
        # Try to find by email
        if email and email != "":
            faculty_match = fetch_details(
                "SELECT id, name FROM faculty_details WHERE email = %s", 
                (email,)
            )
            if faculty_match:
                faculty_id, faculty_name = faculty_match[0]
                st.info(f"Found match by email: {faculty_name} (ID: {faculty_id})")
                return faculty_id
    
    # Method 2: Try to match by name (extract from username)
    name_part = username.split('_')[0] if '_' in username else username
    faculty_match = fetch_details(
        "SELECT id, name FROM faculty_details WHERE LOWER(name) LIKE %s", 
        (f"%{name_part.lower()}%",)
    )
    if faculty_match:
        faculty_id, faculty_name = faculty_match[0]
        st.info(f"Found match by name: {faculty_name} (ID: {faculty_id})")
        return faculty_id
    
    # Method 3: Try any faculty with missing login link
    available_faculty = fetch_details("""
        SELECT f.id, f.name FROM faculty_details f
        WHERE f.id NOT IN (
            SELECT user_id FROM login_details 
            WHERE typeOfUser='faculty' AND user_id IS NOT NULL AND user_id != 0
        )
        LIMIT 1
    """)
    
    if available_faculty:
        faculty_id, faculty_name = available_faculty[0]
        st.info(f"Using available faculty: {faculty_name} (ID: {faculty_id})")
        return faculty_id
    
    return None


# -------------------------------------------------------------
# Assign Student Courses — SIMPLIFIED
# -------------------------------------------------------------
def assign_student_courses(faculty_id):
    st.subheader("📚 Assign Courses to My Students")

    # Clear any previous success messages
    if "assign_success" in st.session_state:
        del st.session_state["assign_success"]

    # Get faculty info
    try:
        faculty_info = fetch_details(
            "SELECT name, department FROM faculty_details WHERE id=%s", (faculty_id,)
        )

        if not faculty_info:
            st.error("Faculty information not found. Please contact admin.")
            return

        faculty_name, faculty_dept = faculty_info[0]
        st.write(f"**Faculty:** {faculty_name} | **Department:** {faculty_dept}")

    except Exception as e:
        st.error(f"Error fetching faculty info: {str(e)}")
        return

    # Get ALL students
    try:
        students = fetch_details("""
            SELECT id, name FROM student_details ORDER BY name
        """)
    except Exception as e:
        st.error(f"Error fetching students: {str(e)}")
        return

    if not students:
        st.info("No students found. Please add students first.")
        return

    # Load available courses based on the faculty's department.
    try:
        available_courses = []
        if faculty_dept:
            # Get courses for the faculty's department
            available_courses = subject_config.get_courses_for_department(faculty_dept)
        
        if not available_courses:
            available_courses = subject_config.DEFAULT_COURSES

        available_courses = sorted(list(set(available_courses)))

    except Exception as e:
        st.error(f"Error loading courses: {str(e)}. Using default list.")
        available_courses = subject_config.DEFAULT_COURSES

    # Course assignment form
    with st.form("faculty_assign_course", clear_on_submit=True):
        col1, col2 = st.columns(2)

        with col1:
            student_options = [f"{s[1]} (ID: {s[0]})" for s in students]
            selected_student = st.selectbox(
                "Select Student",
                options=student_options,
                index=0 if student_options else None,
                key="select_student"
            )
            student_id = None
            if selected_student and "(ID:" in selected_student:
                try:
                    student_id = selected_student.split("(ID: ")[1].replace(")", "")
                except Exception:
                    st.error("Invalid student selection format.")
                    return

        with col2:
            selected_course = st.selectbox(
                "Select Course",
                available_courses,
                key="select_course"
            )

        submitted = st.form_submit_button("🎯 Assign Course to Student")

        if submitted:
            if not student_id or not selected_course:
                st.error("Please select both student and course")
                return

            try:
                # Check if already assigned
                existing = fetch_details("""
                    SELECT * FROM results
                    WHERE student_id=%s AND course=%s AND faculty_id=%s
                    LIMIT 1
                """, (int(student_id), selected_course, faculty_id))

                if existing:
                    st.warning(f"⚠️ '{selected_course}' is already assigned to this student.")
                    st.info("You can manage grades for this student in the 'Manage Grades' section.")
                else:
                    success = execute_query("""
                        INSERT INTO results (student_id, course, faculty_id, grade)
                        VALUES (%s, %s, %s, NULL)
                    """, (int(student_id), selected_course, faculty_id))

                    if success:
                        st.success(f"✅ Course '{selected_course}' assigned to student successfully!")
                        st.rerun()
                    else:
                        st.error("❌ Failed to assign course. Please try again.")

            except ValueError:
                st.error("Invalid student ID format.")
            except Exception as e:
                st.error(f"Error assigning course: {str(e)}")

    # Show currently assigned courses
    st.subheader("📋 Currently Assigned Courses")

    try:
        current_assignments = fetch_details("""
            SELECT s.name, r.course, s.id
            FROM results r
            JOIN student_details s ON r.student_id = s.id
            WHERE r.faculty_id = %s
            ORDER BY s.name, r.course
        """, (faculty_id,))

        if current_assignments:
            assignments_df = pd.DataFrame(current_assignments, columns=["Student", "Course", "Student ID"])
            st.dataframe(assignments_df, use_container_width=True)
        else:
            st.info("No courses assigned yet. Use the form above to assign courses to students.")

    except Exception as e:
        st.error(f"Error loading assigned courses: {str(e)}")


# -------------------------------------------------------------
# Faculty Dashboard — MAIN ENTRY POINT (FIXED VERSION)
# -------------------------------------------------------------
def faculty_dashboard():
    # Sidebar Styling
    st.sidebar.markdown(
        """
    <style>
        .stSidebar {
            background: linear-gradient(135deg, #0f172a, #1e293b);
        }
    </style>
    """,
        unsafe_allow_html=True,
    )

    st.sidebar.title("🧭 Faculty Menu")
    
    # Check if logged in
    if "username" not in st.session_state:
        st.error("⚠️ Session expired. Please log in again.")
        if st.button("Go to Login"):
            st.switch_page("app.py")
        return
    
    username = st.session_state["username"]
    st.sidebar.markdown(f"**Welcome, {username}**")
    st.sidebar.markdown(f"*Role: Faculty*")
    st.sidebar.markdown("---")

    choice = st.sidebar.radio(
        "Menu",
        [
            "Dashboard",
            "Mark Attendance",
            "My Students",
            "Manage Grades",
            "Manage Fees",
            "My Courses",
            "Assign Courses",
            "Logout",
        ],
    )

    st.title(f"👨‍🏫 Faculty Dashboard")

    # ---------------------------------------------------------
    # FIXED SECTION: Handle faculty ID retrieval with auto-fix
    # ---------------------------------------------------------
    try:
        # Step 1: Try to get faculty_id from session (cached)
        if "faculty_id" in st.session_state and st.session_state.faculty_id:
            faculty_id = st.session_state.faculty_id
            st.info(f"Using cached faculty ID: {faculty_id}")
        else:
            # Step 2: Get user_id from login_details table
            user_id_result = fetch_details(
                "SELECT user_id FROM login_details WHERE uname=%s AND typeOfUser='faculty'",
                (username,),
            )

            faculty_id = None
            
            if user_id_result and user_id_result[0][0]:
                faculty_id = user_id_result[0][0]
                st.session_state.faculty_id = faculty_id  # Cache it
                st.success(f"✅ Found faculty ID: {faculty_id}")
            else:
                # Step 3: Auto-fix broken link
                st.error("""
                ## 🔧 Account Link Issue Detected
                
                Your login account is not properly linked to a faculty profile.
                """)
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("🔄 Try Auto-Fix", key="auto_fix_btn"):
                        fixed_id = fix_faculty_link(username)
                        if fixed_id:
                            # Update the database
                            execute_query(
                                "UPDATE login_details SET user_id = %s WHERE uname = %s",
                                (fixed_id, username)
                            )
                            st.session_state.faculty_id = fixed_id
                            st.success(f"✅ Auto-fix successful! Faculty ID: {fixed_id}")
                            st.rerun()
                        else:
                            st.error("Auto-fix failed. Please contact admin.")
                
                with col2:
                    if st.button("🆘 Contact Admin", key="contact_admin_btn"):
                        st.info("""
                        **Contact Administrator:**
                        - Please fix account link for username: `himanshu_24`
                        - In Admin Panel → Fix Broken Links
                        """)
                
                # Show emergency access option
                st.warning("""
                **Emergency Access (Temporary):**
                
                For testing purposes only:
                ```
                -- Admin should run:
                UPDATE login_details 
                SET user_id = [FACULTY_ID] 
                WHERE uname = 'himanshu_24';
                ```
                """)
                return

        # Step 4: Verify faculty exists
        faculty_info_result = fetch_details(
            "SELECT id, name, department FROM faculty_details WHERE id=%s", 
            (faculty_id,)
        )

        if not faculty_info_result:
            st.error(f"""
            ## 🚨 Critical Error: Faculty Profile Missing
            
            Faculty ID `{faculty_id}` not found in database.
            
            **Admin should run:**
            ```sql
            -- Create faculty profile
            INSERT INTO faculty_details (id, name, department) 
            VALUES ({faculty_id}, '{username.split('_')[0].title()}', 'B.Tech');
            ```
            """)
            return

        # Success! We have valid faculty info
        faculty_id, faculty_name, faculty_dept = faculty_info_result[0]
        
        # Store in session for other functions
        st.session_state.faculty_id = faculty_id
        st.session_state.faculty_name = faculty_name
        
        # Display welcome message
        st.write(f"### Welcome, {faculty_name}!")
        st.write(f"**Department:** {faculty_dept}")
        st.write("---")

    except Exception as e:
        st.error(f"""
        ## ⚠️ Unexpected Error Loading Profile
        
        **Error:** {str(e)}
        
        **Troubleshooting Steps:**
        1. Log out and log in again
        2. Contact system administrator
        3. Check database connection
        
        **Debug Info:**
        - Username: {username}
        - Faculty ID in session: {st.session_state.get('faculty_id', 'Not set')}
        """)
        return

    # ---------------------------------------------------------
    # Check if faculty has any courses assigned
    # ---------------------------------------------------------
    try:
        has_courses_result = fetch_details("""
            SELECT COUNT(*) FROM results WHERE faculty_id = %s
        """, (faculty_id,))

        has_courses = has_courses_result and has_courses_result[0][0] > 0

        # Show warning ONLY on Dashboard tab if no courses
        if choice == "Dashboard" and not has_courses:
            st.warning("""
            ⚠️ **No courses assigned to you yet!**

            **Quick Setup Options:**

            1. **Contact Admin:** Ask administrator to assign courses to you
            2. **Self-Assign:** Use the **'Assign Courses'** tab to assign courses to your students

            **Steps to assign courses yourself:**
            1. Go to **'Assign Courses'** tab
            2. Select a student
            3. Select a course
            4. Click **'Assign Course to Student'**
            """)

            col1, col2 = st.columns(2)
            with col1:
                if st.button("📚 Go to Assign Courses", key="go_to_assign_courses"):
                    st.info("Please select 'Assign Courses' from the sidebar menu")
            with col2:
                if st.button("🆘 Contact Admin", key="contact_admin"):
                    st.info("""
                    **Admin Contact:**
                    - Email: admin@university.edu
                    - Phone: (555) 123-4567
                    - Please mention: Faculty `{username}` needs course assignment
                    """.format(username=username))

    except Exception as e:
        st.error(f"Error checking course assignment: {str(e)}")

    # ---------------------------------------------------------
    # DASHBOARD
    # ---------------------------------------------------------
    if choice == "Dashboard":
        st.subheader("📊 My Overview")

        if not has_courses:
            st.info("""
            **📊 Your dashboard is empty because no courses are assigned yet.**

            **Get Started:**
            1. Assign courses to students using the **'Assign Courses'** tab
            2. Or ask admin to assign courses to you
            3. Once courses are assigned, you'll see statistics here
            """)
        else:
            st.subheader("📈 Quick Statistics")
            col1, col2, col3, col4 = st.columns(4)

            metrics = {}
            try:
                # My Students
                student_count = fetch_details(
                    "SELECT COUNT(DISTINCT student_id) FROM results WHERE faculty_id=%s",
                    (faculty_id,)
                )
                metrics['students'] = student_count[0][0] if student_count else 0

                # My Courses
                course_count = fetch_details(
                    "SELECT COUNT(DISTINCT course) FROM results WHERE faculty_id=%s",
                    (faculty_id,)
                )
                metrics['courses'] = course_count[0][0] if course_count else 0

                # Today's Attendance
                today_attendance = fetch_details(
                    "SELECT COUNT(*) FROM attendance WHERE date=%s AND student_name IN (SELECT s.name FROM student_details s JOIN results r ON s.id = r.student_id WHERE r.faculty_id=%s)",
                    (datetime.date.today(), faculty_id)
                )
                metrics['attendance'] = today_attendance[0][0] if today_attendance else 0

                # Pending Grades
                pending_grades = fetch_details(
                    "SELECT COUNT(*) FROM results WHERE faculty_id=%s AND grade IS NULL",
                    (faculty_id,)
                )
                metrics['pending'] = pending_grades[0][0] if pending_grades else 0

                # Display Metrics
                with col1:
                    st.metric("My Students", metrics['students'])
                with col2:
                    st.metric("My Courses", metrics['courses'])
                with col3:
                    st.metric("Today's Attendance", metrics['attendance'])
                with col4:
                    st.metric("Pending Grades", metrics['pending'])

            except Exception as e:
                st.error(f"Error loading dashboard metrics: {str(e)}")

            # Recent Activity
            st.subheader("📋 Recent Activity")
            try:
                recent_attendance = fetch_details(
                    """
                    SELECT student_name, date, status
                    FROM attendance
                    WHERE student_name IN (
                        SELECT s.name
                        FROM student_details s
                        JOIN results r ON s.id = r.student_id
                        WHERE r.faculty_id = %s
                    )
                    ORDER BY date DESC
                    LIMIT 10
                    """,
                    (faculty_id,),
                )

                if recent_attendance:
                    for student, date, status in recent_attendance:
                        date_str = date.strftime("%Y-%m-%d") if hasattr(date, "strftime") else str(date)
                        status_icon = "✅" if status == "Present" else "❌"
                        st.write(f"{status_icon} **{student}** on {date_str} - {status}")
                else:
                    st.info("No recent attendance records found.")

            except Exception as e:
                st.error(f"Error loading recent activity: {str(e)}")

    # ---------------------------------------------------------
    # MARK ATTENDANCE
    # ---------------------------------------------------------
    elif choice == "Mark Attendance":
        st.subheader("📝 Mark Student Attendance")

        try:
            students = fetch_details(
                """
                SELECT DISTINCT s.id, s.name
                FROM student_details s
                JOIN results r ON s.id = r.student_id
                WHERE r.faculty_id = %s
                ORDER BY s.name
                """,
                (faculty_id,),
            )

            if not students:
                st.info("No students assigned to you for attendance marking.")
                return

            with st.form("attendance_form"):
                st.write("**Select Date:**")
                attendance_date = st.date_input("Date", datetime.date.today())

                st.write("**Mark Attendance:**")
                attendance_records = []

                for student_id, student_name in students:
                    col1, col2 = st.columns([3, 2])
                    with col1:
                        st.write(f"**{student_name}**")
                    with col2:
                        status = st.radio(
                            "Status",
                            ["Present", "Absent"],
                            key=f"status_{student_id}",
                            horizontal=True,
                            index=0,
                        )
                    attendance_records.append((student_name, attendance_date, status))
                    st.divider()

                submitted = st.form_submit_button("📊 Submit Attendance")

                if submitted:
                    success_count = 0
                    error_count = 0

                    for student_name, date, status in attendance_records:
                        try:
                            existing = fetch_details(
                                "SELECT * FROM attendance WHERE student_name=%s AND date=%s",
                                (student_name, date),
                            )

                            if existing:
                                update_success = execute_query(
                                    "UPDATE attendance SET status=%s WHERE student_name=%s AND date=%s",
                                    (status, student_name, date),
                                )
                            else:
                                update_success = execute_query(
                                    "INSERT INTO attendance (student_name, date, status) VALUES (%s, %s, %s)",
                                    (student_name, date, status),
                                )

                            if update_success:
                                success_count += 1
                            else:
                                error_count += 1

                        except Exception as e:
                            error_count += 1
                            st.error(f"Error updating attendance for {student_name}: {str(e)}")

                    if success_count > 0:
                        st.success(f"✅ Attendance marked for {success_count} students!")
                    if error_count > 0:
                        st.error(f"❌ Failed to mark attendance for {error_count} students")

        except Exception as e:
            st.error(f"Error loading students for attendance: {str(e)}")

    # ---------------------------------------------------------
    # MY STUDENTS
    # ---------------------------------------------------------
    elif choice == "My Students":
        st.subheader("🎓 My Students & Grades")

        try:
            data = fetch_details(
                """
                SELECT 
                    COALESCE(s.id, 0) as student_id,
                    COALESCE(s.name, 'Unknown Student') as student_name,
                    COALESCE(r.course, 'No Course') as course,
                    COALESCE(r.grade, 'Not Graded') as grade,
                    COALESCE(s.phoneno, 'No Phone') as phone
                FROM results r
                LEFT JOIN student_details s ON r.student_id = s.id
                WHERE r.faculty_id = %s AND r.course IS NOT NULL
                ORDER BY s.name, r.course
                """,
                (faculty_id,),
            )

            if not data:
                st.info("No students assigned to you yet.")
                return

            students_dict = {}
            for student_id, name, course, grade, phone in data:
                if name not in students_dict:
                    students_dict[name] = {"id": student_id, "phone": phone, "courses": []}
                students_dict[name]["courses"].append((course, grade))

            for student_name, info in students_dict.items():
                with st.expander(f"📚 {student_name} (📞 {info['phone'] or 'No phone'})"):
                    for course, grade in info["courses"]:
                        col1, col2 = st.columns([4, 1])
                        with col1:
                            st.write(f"**{course}**")
                        with col2:
                            display_grade(grade)

        except Exception as e:
            st.error(f"Error loading student data: {str(e)}")

    # ---------------------------------------------------------
    # MANAGE GRADES
    # ---------------------------------------------------------
    elif choice == "Manage Grades":
        st.subheader("📊 Manage Student Grades")

        try:
            courses_data = fetch_details("""
                SELECT DISTINCT 
                    r.course as course_name,
                    s.id as student_id,
                    s.name as student_name
                FROM results r
                LEFT JOIN student_details s ON r.student_id = s.id
                WHERE r.faculty_id = %s AND r.course IS NOT NULL AND TRIM(r.course) != ''
                ORDER BY r.course, s.name
            """, (faculty_id,))

            if not courses_data:
                st.info("""
                **📚 No courses assigned to you yet!**

                **How to get started:**
                1. Go to **'Assign Courses'** tab
                2. Select a student and course
                3. Click **'Assign Course to Student'**
                """)
                return

            st.write(f"**Found {len(courses_data)} student-course assignments**")

            courses_dict = {}
            for course_name, student_id, student_name in courses_data:
                if course_name and course_name != 'No Course':
                    if course_name not in courses_dict:
                        courses_dict[course_name] = []
                    courses_dict[course_name].append((student_id, student_name))

            if not courses_dict:
                st.info("No valid courses found.")
                return

            selected_course = st.selectbox("Select Course", list(courses_dict.keys()))

            if selected_course:
                st.write(f"**Enter Grades for {selected_course}:**")

                with st.form("grades_form"):
                    grades_to_update = []

                    for student_id, student_name in courses_dict[selected_course]:
                        col1, col2 = st.columns([3, 2])

                        with col1:
                            st.write(f"**{student_name}**")
                            st.caption(f"ID: {student_id}")

                        with col2:
                            # Get current grade
                            current_grade_data = fetch_details("""
                                SELECT grade FROM results 
                                WHERE student_id=%s AND course=%s AND faculty_id=%s
                            """, (student_id, selected_course, faculty_id))

                            current_grade = ""
                            if current_grade_data and current_grade_data[0][0]:
                                current_grade = current_grade_data[0][0]

                            grade_options = ["Not Graded", "A+", "A", "A-", "B+", "B", "B-",
                                           "C+", "C", "C-", "D", "F"]

                            try:
                                current_idx = grade_options.index(current_grade)
                            except ValueError:
                                current_idx = 0

                            grade = st.selectbox(
                                "Grade",
                                grade_options,
                                index=current_idx,
                                key=f"grade_{student_id}_{selected_course}"
                            )

                            if grade != "Not Graded":
                                grades_to_update.append((student_id, student_name, grade))

                        st.divider()

                    submitted = st.form_submit_button("💾 Save Grades")

                    if submitted:
                        if not grades_to_update:
                            st.warning("No grades to save. Please select grades other than 'Not Graded'.")
                        else:
                            success_count = 0
                            error_count = 0

                            for student_id, student_name, grade in grades_to_update:
                                try:
                                    update_success = execute_query("""
                                        UPDATE results 
                                        SET grade=%s 
                                        WHERE student_id=%s AND course=%s AND faculty_id=%s
                                    """, (grade, student_id, selected_course, faculty_id))

                                    if update_success:
                                        success_count += 1
                                    else:
                                        error_count += 1
                                        st.error(f"Failed to update grade for {student_name}")

                                except Exception as e:
                                    error_count += 1
                                    st.error(f"Error updating {student_name}: {str(e)}")

                            if success_count > 0:
                                st.success(f"✅ Successfully updated grades for {success_count} student(s)!")
                                st.rerun()

                            if error_count > 0:
                                st.error(f"❌ Failed to update {error_count} student(s)")

        except Exception as e:
            st.error(f"Error loading grade management interface: {str(e)}")

    # ---------------------------------------------------------
    # MANAGE FEES
    # ---------------------------------------------------------
    elif choice == "Manage Fees":
        st.subheader("💰 Manage Student Fees")

        try:
            students = fetch_details(
                """
                SELECT DISTINCT s.id, s.name 
                FROM student_details s
                JOIN results r ON s.id = r.student_id
                WHERE r.faculty_id = %s
                ORDER BY s.name
                """,
                (faculty_id,),
            )

            if not students:
                st.info("No students assigned to you for fee management.")
                return

            tab1, tab2 = st.tabs(["➕ Add/Update Fees", "📋 View Student Fees"])

            with tab1:
                with st.form("fees_form"):
                    st.write("**Add/Update Student Fees:**")

                    selected_student = st.selectbox(
                        "Select Student", [student[1] for student in students]
                    )
                    fee_amount = st.number_input(
                        "Fee Amount (₹)", min_value=0, value=5000, step=500
                    )
                    due_date = st.date_input(
                        "Due Date", datetime.date.today() + datetime.timedelta(days=30)
                    )
                    fee_status = st.selectbox("Status", ["Pending", "Paid", "Partial"])
                    fee_type = st.selectbox(
                        "Fee Type", ["Tuition", "Exam", "Library", "Other"]
                    )
                    description = st.text_input("Description (Optional)")

                    submitted = st.form_submit_button("💳 Save Fee Record")

                    if submitted:
                        if fee_amount <= 0:
                            st.error("Fee amount must be greater than 0")
                            return

                        try:
                            existing_fee = fetch_details(
                                "SELECT * FROM fees WHERE student_name=%s AND due_date=%s",
                                (selected_student, due_date),
                            )

                            if existing_fee:
                                st.info("Updating existing fee record...")
                                update_success = execute_query(
                                    "UPDATE fees SET amount=%s, status=%s, fee_type=%s, description=%s WHERE student_name=%s AND due_date=%s",
                                    (
                                        fee_amount,
                                        fee_status,
                                        fee_type,
                                        description,
                                        selected_student,
                                        due_date,
                                    ),
                                )
                            else:
                                st.info("Creating new fee record...")
                                update_success = execute_query(
                                    """
                                    INSERT INTO fees (student_name, amount, due_date, status, fee_type, description) 
                                    VALUES (%s, %s, %s, %s, %s, %s)
                                    """,
                                    (
                                        selected_student,
                                        fee_amount,
                                        due_date,
                                        fee_status,
                                        fee_type,
                                        description,
                                    ),
                                )

                            if update_success:
                                st.success(f"✅ Fee record updated for {selected_student}!")
                            else:
                                st.error("❌ Failed to update fee record")

                        except Exception as e:
                            st.error(f"Error processing fee record: {str(e)}")

            with tab2:
                try:
                    fee_records = fetch_details(
                        """
                        SELECT student_name, amount, due_date, status, fee_type, description
                        FROM fees 
                        WHERE student_name IN (
                            SELECT s.name FROM student_details s
                            JOIN results r ON s.id = r.student_id
                            WHERE r.faculty_id = %s
                        )
                        ORDER BY due_date DESC
                        LIMIT 50
                        """,
                        (faculty_id,),
                    )

                    if fee_records:
                        for student, amount, due_date, status, fee_type, description in fee_records:
                            col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 1, 2])
                            with col1:
                                st.write(f"**{student}**")
                                if fee_type:
                                    st.caption(f"Type: {fee_type}")
                            with col2:
                                st.write(f"₹{amount:,.2f}")
                            with col3:
                                due_date_str = due_date.strftime("%Y-%m-%d") if hasattr(due_date, "strftime") else str(due_date)
                                st.write(due_date_str)
                            with col4:
                                if status == "Paid":
                                    st.success("Paid")
                                elif status == "Pending":
                                    st.error("Pending")
                                else:
                                    st.warning("Partial")
                            with col5:
                                if description:
                                    st.caption(f"Note: {description}")
                            st.divider()
                    else:
                        st.info("No fee records found for your students.")

                except Exception as e:
                    st.error(f"Error loading fee records: {str(e)}")

        except Exception as e:
            st.error(f"Error loading students for fee management: {str(e)}")

    # ---------------------------------------------------------
    # MY COURSES
    # ---------------------------------------------------------
    elif choice == "My Courses":
        st.subheader("📚 My Courses")

        try:
            courses = fetch_details(
                """
                SELECT DISTINCT 
                    COALESCE(course, 'No Course') as course,
                    COUNT(DISTINCT student_id) as student_count
                FROM results
                WHERE faculty_id = %s AND course IS NOT NULL
                GROUP BY course
                HAVING COUNT(DISTINCT student_id) > 0
                ORDER BY course
                """,
                (faculty_id,),
            )

            if not courses:
                st.info("No courses assigned to you.")
                return

            st.write(f"**You are teaching {len(courses)} courses:**")

            for course, count in courses:
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    st.write(f"**{course}**")
                with col2:
                    st.write(f"Students: {count}")
                with col3:
                    if st.button("📊 Manage Grades", key=f"grades_{course}"):
                        st.session_state.manage_grades_course = course
                        st.rerun()
                st.divider()

            st.write("### 📈 Course Statistics")

            for course, _ in courses:
                try:
                    grade_dist = fetch_details(
                        """
                        SELECT grade, COUNT(*)
                        FROM results
                        WHERE course=%s AND faculty_id=%s AND grade IS NOT NULL
                        GROUP BY grade
                        """,
                        (course, faculty_id),
                    )

                    if grade_dist:
                        st.write(f"**{course} Grade Distribution:**")
                        for grade, count in grade_dist:
                            st.write(f"- {grade}: {count} students")
                        st.divider()

                except Exception as e:
                    st.error(f"Error loading grade distribution for {course}: {str(e)}")

        except Exception as e:
            st.error(f"Error loading course information: {str(e)}")

    # ---------------------------------------------------------
    # ASSIGN COURSES
    # ---------------------------------------------------------
    elif choice == "Assign Courses":
        assign_student_courses(faculty_id)

    # ---------------------------------------------------------
    # LOGOUT
    # ---------------------------------------------------------
    elif choice == "Logout":
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()