This project is a comprehensive, multi-role Student Management System (SMS) designed to fully automate and streamline the academic and administrative tasks of an educational institution. The core goal is to replace manual, paper-based processes with a centralized, high-efficiency digital platform, ensuring transparency and accessibility for all stakeholders.

Technology and Architecture
The application is built on a robust architecture leveraging Python as the core backend logic, powered by the Streamlit web framework for the interactive, data-driven frontend interface. All system data—including user credentials, student profiles, attendance, grades, and financial records—is securely stored in a MySQL relational database. The system uses environment variables (.env file) for secure handling of database credentials.

Core Features and Role-Based Access
The SMS provides three distinct, secure, role-based dashboards:

🧑‍💼 Admin Dashboard: This is the control center for the institution. Admins have Full CRUD (Create, Read, Update, Delete) functionality for student and faculty profiles, manage subjects and courses, control fee statuses, and generate comprehensive reports and analytics.

👨‍🏫 Faculty Dashboard: Faculty members can efficiently mark and manage student attendance for their assigned courses. They are also responsible for inputting and updating student grades, and viewing basic course statistics.

👩‍🎓 Student Dashboard: Students gain real-time access to their academic information. They can check their personal profile, view subject-wise attendance records, see all their grades and results, and check their current fee status.
