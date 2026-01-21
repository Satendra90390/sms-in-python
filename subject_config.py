# subject_config.py

# Define departments and their courses with subjects
DEPARTMENT_COURSES = {
    "B.Tech": {
        "Computer Science (CS)": [
            "Data Structures",
            "Algorithms",
            "Database Systems",
            "Operating Systems",
            "Computer Networks"
        ],
        "Mechanical Engineering (ME)": [
            "Thermodynamics",
            "Fluid Mechanics",
            "Machine Design",
            "Heat Transfer",
            "Manufacturing Processes"
        ],
        "Civil Engineering (CE)": [
            "Structural Analysis",
            "Geotechnical Engineering",
            "Transportation Engineering",
            "Environmental Engineering",
            "Construction Management"
        ],
        "Electrical Engineering (EE)": [
            "Power Systems",
            "Control Systems",
            "Electrical Machines",
            "Power Electronics",
            "Renewable Energy"
        ],
        "Electronics & Communication (EC)": [
            "Digital Electronics",
            "Microprocessors",
            "Communication Systems",
            "VLSI Design",
            "Signal Processing"
        ]
    },
    "MBA": {
        "Finance": [
            "Financial Management",
            "Investment Analysis",
            "Risk Management",
            "Corporate Finance",
            "International Finance"
        ],
        "Marketing": [
            "Consumer Behavior",
            "Brand Management",
            "Digital Marketing",
            "Market Research",
            "Sales Management"
        ],
        "HR": [
            "Organizational Behavior",
            "Talent Management",
            "Compensation Management",
            "Industrial Relations",
            "Training & Development"
        ]
    },
    "Pharmacy": {
        "Pharmaceutics": [
            "Pharmaceutical Technology",
            "Biopharmaceutics",
            "Pharmacokinetics",
            "Pharmaceutical Engineering",
            "Dosage Form Design"
        ],
        "Pharmacology": [
            "Clinical Pharmacology",
            "Toxicology",
            "Neuropharmacology",
            "Cardiovascular Pharmacology",
            "Molecular Pharmacology"
        ]
    }
}

def get_all_departments():
    """Return list of all departments"""
    return list(DEPARTMENT_COURSES.keys())

def get_courses_for_department(department):
    """Return courses for a given department"""
    return list(DEPARTMENT_COURSES.get(department, {}).keys())

def get_subjects_for_course(department, course):
    """Return subjects for a given course in a department"""
    return DEPARTMENT_COURSES.get(department, {}).get(course, [])

def get_course_summary():
    """Return summary of all departments and courses"""
    summary = {
        "departments": get_all_departments(),
        "courses_by_dept": {
            dept: {
                "count": len(courses),
                "courses": list(courses.keys())
            }
            for dept, courses in DEPARTMENT_COURSES.items()
        }
    }
    return summary