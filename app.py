
import re
import hmac
import logging

import pandas as pd
import streamlit as st
from supabase import create_client

# ==========================================
# 1. PAGE CONFIGURATION
# ==========================================

st.set_page_config(
    page_title="Student Management System",
    page_icon="🎓",
    layout="wide"
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

COURSES = [
    "Python",
    "Java",
    "C++",
    "AI/ML",
    "Data Science"
]


# ==========================================
# 2. VALIDATION FUNCTIONS
# ==========================================

def valid_email(email):
    pattern = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
    return bool(re.fullmatch(pattern, email))


def validate_student(name, email):
    if not name.strip():
        return "Student name is required."

    if len(name.strip()) > 100:
        return "Student name is too long."

    if not valid_email(email.strip()):
        return "Please enter a valid email address."

    if len(email.strip()) > 255:
        return "Email address is too long."

    return None


# ==========================================
# 3. ADMIN LOGIN
# ==========================================

def login():
    st.title("🎓 Student Management System")
    st.subheader("🔐 Administrator Login")

    if "ADMIN_PASSWORD" not in st.secrets:
        st.error(
            "Admin password is not configured. "
            "Add ADMIN_PASSWORD to Streamlit secrets."
        )
        st.stop()

    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if not st.session_state.authenticated:
        with st.form("login_form"):
            password = st.text_input(
                "Admin Password",
                type="password"
            )

            submitted = st.form_submit_button(
                "Login",
                type="primary"
            )

            if submitted:
                if hmac.compare_digest(
                    password,
                    st.secrets["ADMIN_PASSWORD"]
                ):
                    st.session_state.authenticated = True
                    st.rerun()
                else:
                    st.error("Incorrect administrator password.")

        st.stop()


login()


# ==========================================
# 4. SUPABASE CONNECTION
# ==========================================

@st.cache_resource
def get_supabase_client():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]

    return create_client(url, key)


try:
    supabase = get_supabase_client()

except Exception:
    logger.exception("Supabase initialization failed")
    st.error("Unable to initialize database connection.")
    st.stop()


# ==========================================
# 5. DATABASE FUNCTIONS
# ==========================================

def get_students():
    response = (
        supabase.table("students")
        .select("*")
        .order("id")
        .execute()
    )

    return response.data


def add_student(name, email, course, marks):
    return (
        supabase.table("students")
        .insert({
            "name": name,
            "email": email,
            "course": course,
            "marks": marks
        })
        .execute()
    )


def update_student(student_id, name, email, course, marks):
    return (
        supabase.table("students")
        .update({
            "name": name,
            "email": email,
            "course": course,
            "marks": marks
        })
        .eq("id", student_id)
        .execute()
    )


def delete_student(student_id):
    return (
        supabase.table("students")
        .delete()
        .eq("id", student_id)
        .execute()
    )


def show_database_error(error, action):
    logger.error(
        "%s failed: %s",
        action,
        error,
        exc_info=True
    )

    error_code = getattr(error, "code", None)

    if error_code == "23505":
        st.error(
            "This email address is already registered."
        )
    else:
        st.error(
            f"Unable to {action.lower()}. "
            "Please try again."
        )


# ==========================================
# 6. SIDEBAR
# ==========================================

with st.sidebar:
    st.title("🎓 Student Manager")
    st.success("Administrator")

    if st.button("🚪 Logout", use_container_width=True):
        st.session_state.authenticated = False
        st.rerun()

    st.divider()

    st.write("**Technology Stack**")
    st.write("Frontend: Streamlit")
    st.write("Backend API: Supabase")
    st.write("Database: PostgreSQL")


# ==========================================
# 7. MAIN DASHBOARD
# ==========================================

st.title("🎓 Student Management System")

st.caption(
    "Manage student records using "
    "Streamlit, Supabase and PostgreSQL."
)

# Display success messages after rerun
if "success_message" in st.session_state:
    st.success(st.session_state.pop("success_message"))


# ==========================================
# 8. READ OPERATION
# ==========================================

st.header("📋 Student Records")

try:
    students = get_students()

except Exception:
    logger.exception("Unable to fetch students")
    st.error("Unable to load student records.")
    st.stop()


total_students = len(students)

average_marks = (
    sum(s["marks"] or 0 for s in students) / total_students
    if total_students else 0
)

col1, col2 = st.columns(2)

with col1:
    st.metric(
        "Total Students",
        total_students
    )

with col2:
    st.metric(
        "Average Marks",
        f"{average_marks:.2f}"
    )


if students:
    df = pd.DataFrame(students)

    display_columns = [
        "id",
        "name",
        "email",
        "course",
        "marks",
        "created_at"
    ]

    df = df[display_columns]

    st.dataframe(
        df,
        width="stretch",
        hide_index=True
    )

else:
    st.info("No student records found.")


# ==========================================
# 9. CRUD TABS
# ==========================================

tab1, tab2, tab3 = st.tabs([
    "➕ Add Student",
    "✏️ Update Student",
    "🗑️ Delete Student"
])


# ==========================================
# 10. CREATE OPERATION
# ==========================================

with tab1:
    st.subheader("Add New Student")

    with st.form("add_student_form", clear_on_submit=True):

        name = st.text_input(
            "Student Name",
            placeholder="Enter full name"
        )

        email = st.text_input(
            "Email Address",
            placeholder="student@example.com"
        )

        course = st.selectbox(
            "Select Course",
            COURSES
        )

        marks = st.number_input(
            "Marks",
            min_value=0,
            max_value=100,
            value=0,
            step=1
        )

        submitted = st.form_submit_button(
            "Add Student",
            type="primary"
        )

        if submitted:
            name = name.strip()
            email = email.strip().lower()

            error = validate_student(name, email)

            if error:
                st.warning(error)

            else:
                try:
                    add_student(
                        name,
                        email,
                        course,
                        int(marks)
                    )

                    st.session_state.success_message = (
                        "Student added successfully!"
                    )

                    st.rerun()

                except Exception as e:
                    show_database_error(
                        e,
                        "Add student"
                    )


# ==========================================
# 11. UPDATE OPERATION
# ==========================================

with tab2:
    st.subheader("Update Student Details")

    if students:

        student_options = {
            f"{s['id']} - {s['name']}": s
            for s in students
        }

        selected_label = st.selectbox(
            "Select Student",
            list(student_options.keys()),
            key="update_student_select"
        )

        student = student_options[selected_label]

        with st.form(
            f"update_form_{student['id']}"
        ):

            updated_name = st.text_input(
                "Student Name",
                value=student["name"]
            )

            updated_email = st.text_input(
                "Email Address",
                value=student["email"]
            )

            current_course = student["course"]

            course_options = COURSES.copy()

            if current_course not in course_options:
                course_options.append(current_course)

            updated_course = st.selectbox(
                "Course",
                course_options,
                index=course_options.index(current_course)
            )

            updated_marks = st.number_input(
                "Marks",
                min_value=0,
                max_value=100,
                value=int(student["marks"] or 0),
                step=1
            )

            update_clicked = st.form_submit_button(
                "Update Student",
                type="primary"
            )

            if update_clicked:

                updated_name = updated_name.strip()
                updated_email = updated_email.strip().lower()

                error = validate_student(
                    updated_name,
                    updated_email
                )

                if error:
                    st.warning(error)

                else:
                    try:
                        update_student(
                            student["id"],
                            updated_name,
                            updated_email,
                            updated_course,
                            int(updated_marks)
                        )

                        st.session_state.success_message = (
                            "Student updated successfully!"
                        )

                        st.rerun()

                    except Exception as e:
                        show_database_error(
                            e,
                            "Update student"
                        )

    else:
        st.info("No students available to update.")


# ==========================================
# 12. DELETE OPERATION
# ==========================================

with tab3:
    st.subheader("Delete Student")

    if students:

        delete_options = {
            f"{s['id']} - {s['name']}": s
            for s in students
        }

        selected_delete = st.selectbox(
            "Select Student to Delete",
            list(delete_options.keys()),
            key="delete_student_select"
        )

        student_to_delete = delete_options[selected_delete]

        st.warning(
            "Deleting a student will permanently "
            "remove their record."
        )

        with st.form(
            f"delete_form_{student_to_delete['id']}"
        ):

            confirmation = st.checkbox(
                "I confirm that I want to delete this student"
            )

            delete_clicked = st.form_submit_button(
                "Delete Student",
                type="primary"
            )

            if delete_clicked:

                if not confirmation:
                    st.warning(
                        "Please confirm deletion first."
                    )

                else:
                    try:
                        delete_student(
                            student_to_delete["id"]
                        )

                        st.session_state.success_message = (
                            "Student deleted successfully!"
                        )

                        st.rerun()

                    except Exception as e:
                        show_database_error(
                            e,
                            "Delete student"
                        )

    else:
        st.info("No students available to delete.")


# ==========================================
# 13. FOOTER
# ==========================================

st.divider()

st.caption(
    "Student Management System | "
    "Built with Streamlit, Supabase & PostgreSQL"
)
