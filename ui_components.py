import streamlit as st

def display_grade(grade):
    """Displays a grade with consistent color-coding."""
    if not grade or grade == "Not Graded":
        st.info("No Grade")
    elif grade.startswith("A"):
        st.success(f"**{grade}**")
    elif grade.startswith("B"):
        st.info(f"**{grade}**")
    elif grade.startswith("C"):
        st.warning(f"**{grade}**")
    else:
        st.error(f"**{grade}**")

def display_subject_card(subject, faculty, grade, use_columns=False):
    """
    Displays a single subject in a styled card or a simple list item.
    - subject (str): The name of the subject.
    - faculty (str): The name of the faculty member.
    - grade (str): The grade received.
    - use_columns (bool): If True, displays in a simple row with columns.
    """
    if use_columns:
        col1, col2, col3 = st.columns([3, 2, 1])
        with col1:
            st.write(f"**{subject}**")
        with col2:
            st.write(f"👨‍🏫 {faculty}")
        with col3:
            display_grade(grade)
        st.divider()
    else:
        border_color = "#60a5fa"  # Default blue
        if grade and grade != "Not Graded":
            if grade.startswith("A"): border_color = "#10b981"  # Green
            elif grade.startswith("B"): border_color = "#3b82f6"  # Blue
            elif grade.startswith("C"): border_color = "#f59e0b"  # Amber
            else: border_color = "#ef4444"  # Red

        st.markdown(f"""
        <div style='
            background: rgba(30,41,59,0.8);
            border-radius: 10px;
            padding: 15px;
            border-left: 4px solid {border_color};
            margin: 10px 0;
            border: 1px solid #334155;
        '>
            <h4 style='color:#60a5fa;margin:0;'>{subject}</h4>
            <p style='color:#cbd5e1;margin:5px 0;'><strong>👨‍🏫 Faculty:</strong> {faculty}</p>
            <p style='color:#cbd5e1;margin:5px 0;'><strong>📊 Grade:</strong> {grade or 'Not Graded Yet'}</p>
        </div>
        """, unsafe_allow_html=True)