"""
AskOGMS prompts configuration.
Prompts used for SQL generation and responses.
"""

# =============================================================================
# SQL QUERY GENERATION PROMPT
# =============================================================================

SQL_GENERATION_PROMPT = """You are an expert SQL query generator for PostgreSQL. Generate syntactically correct queries.

DATABASE (OGMS graduate program operations):
- Tables and columns come from the introspected schema in the TABLES section below. Use ONLY those names (respect quoted/mixed-case identifiers exactly as in the schema).
- Core grain: one row per student in `student_info` keyed by `panther_id`. Many modules repeat `panther_id` to link people across admissions, GTA, CPT, RCL, funding, etc.

KEY RELATIONSHIPS (use schema to confirm exact column types):
1. **Student profile**: `student_info` is the master record. `student_info.status_lookup_id` → `student_status_lookup.status_lookup_id` for the status label.
2. **Admissions**: `admissions` is one row per applicant per `term` per `program`; join to `student_info` on `panther_id` when the person is already a student. Faculty evaluators use `studentevaluation` (`s_panther_id` student, `f_panther_id` faculty).
3. **Terms**: `term` holds `term_id` and term labels/dates. Scheduled sections and many transactional tables use `term_id`; some text columns (e.g. in `admissions` or `gtaapplication`) may store the term label—join on whichever key exists in the schema.
4. **GTA**: `gtaapplication` is per student per term; `gtaapplication.status` → `gta_lookup.gta_lookup_id`. Course placements use `gta_assignment` (`s_panther_id`, `f_panther_id`, `course_id`, `term_id`). Catalog/schedule: `courses`, `courses_schedule` (often `term_id`, `faculty_email`).
5. **Faculty/staff/users**: `faculty` / `staff` by `panther_id` and `email`. `users.role` → `user_roles.user_roles_id`. Academic advisor on `student_info` may match `faculty.panther_id` or `faculty.email`—use the join that matches the column definition.
6. **Lookups**: `rejection_reason_lookup` for GTA rejection reasons; `evaluation_criteria_lor_sop_finaid_rec` for evaluation code labels where referenced.

IMPORTANT RULES:
1. **Always use table aliases** for clarity.
2. **Prefer exact keys** (`panther_id`, `term_id`, `course_id`, FK ids) over free-text when filtering.
3. **Human-readable filters**: Use `ILIKE` on `name`, `email`, `program`, or `term` when the user gives partial text.
4. **Use DISTINCT** when joins may duplicate rows.
5. **Limit results** to top {top_k} unless the user specifies otherwise.
6. **Arrays / JSON**: If a column is an array or JSON (see schema), use the appropriate PostgreSQL operators (`unnest`, `@>`, `->>`) only when needed.
7. **Table anchoring**: For follow-ups ("them", "those students"), keep the same base tables unless the user changes scope.

Table Info: {table_info}

Below are examples of questions and their corresponding SQL queries:"""


# =============================================================================
# TABLE SELECTION PROMPT
# =============================================================================

TABLE_SELECTION_PROMPT = """You are a database schema expert. Analyze the user's question and return ALL SQL tables that might be relevant.

DATABASE TABLES:
{table_details}

TABLE SELECTION GUIDELINES (OGMS):
1. **Direct mentions**: Include any table the user names explicitly.
2. **Student / profile questions**: Include `student_info`; add `student_status_lookup` if status wording matters; add `faculty` (or `staff`) if advisor, instructor, or contact details are needed.
3. **Admissions / applications / evaluations / offers**: Include `admissions`, `studentevaluation`, `required_courses`, `foundation_courses`, or `offer_letter` as appropriate; include `term` if semester or intake period matters.
4. **GTA / TA / assistantship / courses**: Include `gtaapplication`, `gta_assignment`, `courses`, `courses_schedule`, `term`, `faculty`; add `gta_lookup` and `rejection_reason_lookup` if status or rejection reason is asked.
5. **Funding / stipend / speedtype**: Include `student_funding_appointments`, `student_funding_speedtypes`, `student_info`, `term` as needed.
6. **CPT / RCL / waivers / ODH / advisor change**: Include `cpt`, `rcl`, `waiver_request_form`, `outside_dept_hire`, or `advisor_assignment_requests` respectively, usually with `student_info` and `term` or `faculty`.
7. **Login / roles**: Include `users` and `user_roles` for access or role questions.
8. If uncertain, include the central fact table plus `student_info` and `term` rather than omitting a bridge table.

Return the names of ALL tables that might be needed (better to include extra than miss required ones)."""


# =============================================================================
# ANSWER GENERATION PROMPT
# =============================================================================

ANSWER_GENERATION_PROMPT = """You are a helpful database assistant. Answer the user's question based on the query results.

User Question: {question}

Database Query Result: {result}

Provide a clear, concise answer to the user's question. Format the data nicely using markdown (**bold** for important terms, *italic* for emphasis). If the result shows no data, explain that clearly."""


# =============================================================================
# FEW-SHOT EXAMPLES
# =============================================================================

FEW_SHOT_EXAMPLES = [
    {
        "input": "Show name, email, degree, and major for panther_id 002345678",
        "query": "SELECT si.name, si.email, si.degree, si.major FROM student_info AS si WHERE si.panther_id = '002345678' LIMIT 5;",
    },
    {
        "input": "List active students with their status label",
        "query": "SELECT si.panther_id, si.name, si.email, ssl.status_lookup_value FROM student_info AS si JOIN student_status_lookup AS ssl ON si.status_lookup_id = ssl.status_lookup_id WHERE LOWER(si.status) = 'active' ORDER BY si.name LIMIT 50;",
    },
    {
        "input": "Who is the academic advisor for panther_id 002345678? Show advisor name and email",
        "query": "SELECT si.panther_id, si.name AS student_name, f.name AS advisor_name, f.email AS advisor_email FROM student_info AS si LEFT JOIN faculty AS f ON si.advisor = f.panther_id WHERE si.panther_id = '002345678' LIMIT 5;",
    },
    {
        "input": "Applicants in the MS program for Fall 2025 with admit_status admitted",
        "query": "SELECT a.panther_id, a.name, a.email, a.program, a.term, a.admit_status FROM admissions AS a WHERE a.program ILIKE '%MS%' AND a.term ILIKE '%Fall%2025%' AND LOWER(a.admit_status) LIKE '%admit%' ORDER BY a.name LIMIT 50;",
    },
    {
        "input": "Average GPA of applicants to the PhD program in Spring 2025",
        "query": "SELECT AVG(a.gpa::numeric) AS avg_gpa FROM admissions AS a WHERE a.program ILIKE '%PhD%' AND a.term ILIKE '%Spring%2025%';",
    },
    {
        "input": "Join student profile with their admission row for the same panther_id",
        "query": "SELECT si.panther_id, si.name, si.degree, a.program, a.term, a.admit_status FROM student_info AS si JOIN admissions AS a ON si.panther_id = a.panther_id ORDER BY si.panther_id, a.term LIMIT 50;",
    },
    {
        "input": "Faculty admission evaluations for student panther_id 002345678 with term Fall 2025",
        "query": "SELECT se.evaluation_id, se.f_panther_id, f.name AS faculty_name, se.term, se.program, se.admission_decision, se.status FROM studentevaluation AS se JOIN faculty AS f ON se.f_panther_id = f.panther_id WHERE se.s_panther_id = '002345678' AND se.term ILIKE '%Fall%2025%' ORDER BY f.name LIMIT 50;",
    },
    {
        "input": "All GTA applications for Fall 2025 with human-readable status",
        "query": "SELECT ga.panther_id, ga.term, gl.gta_lookup_value AS application_status, ga.current_gpa, ga.is_accept FROM gtaapplication AS ga JOIN gta_lookup AS gl ON ga.status = gl.gta_lookup_id WHERE ga.term ILIKE '%Fall%2025%' ORDER BY ga.panther_id LIMIT 50;",
    },
    {
        "input": "How many GTA applications per status for Spring 2025?",
        "query": "SELECT gl.gta_lookup_value AS status, COUNT(*) AS cnt FROM gtaapplication AS ga JOIN gta_lookup AS gl ON ga.status = gl.gta_lookup_id WHERE ga.term ILIKE '%Spring%2025%' GROUP BY gl.gta_lookup_value ORDER BY cnt DESC;",
    },
    {
        "input": "GTA assignments for term_id 42 with course subject and number",
        "query": "SELECT ga.gta_assignment_id, ga.s_panther_id, ga.f_panther_id, c.subject, c.course, ga.assigned_hours FROM gta_assignment AS ga JOIN courses AS c ON ga.course_id = c.course_id WHERE ga.term_id = 42 ORDER BY c.subject, c.course LIMIT 50;",
    },
    {
        "input": "Scheduled sections for term_id 42 including faculty email and meeting pattern",
        "query": "SELECT cs.courses_schedule_id, cs.faculty_email, cs.days, cs.start_time, cs.end_time, cs.location, c.title FROM courses_schedule AS cs JOIN courses AS c ON cs.course_id = c.course_id WHERE cs.term_id = 42 ORDER BY cs.faculty_email, cs.start_time LIMIT 50;",
    },
    {
        "input": "Which terms have GTA applications currently open?",
        "query": "SELECT t.term_id, t.term, t.gta_application_start_day, t.gta_application_end_day FROM term AS t WHERE t.is_gta_applications_open IS TRUE ORDER BY t.start_day DESC LIMIT 20;",
    },
    {
        "input": "Pending advisor change requests with student and requested faculty panther ids",
        "query": "SELECT r.request_id, r.student_panther_id, r.current_faculty_panther_id, r.requested_faculty_panther_id, r.status, r.faculty_message FROM advisor_assignment_requests AS r WHERE LOWER(r.status) = 'pending' ORDER BY r.request_id DESC LIMIT 50;",
    },
    {
        "input": "CPT applications for term_id 15 waiting on DGS with student email",
        "query": "SELECT c.cpt_id, c.panther_id, si.email, c.dgs_status, c.advisor_status FROM cpt AS c JOIN student_info AS si ON c.panther_id = si.panther_id WHERE c.term_id = 15 AND LOWER(COALESCE(c.dgs_status, '')) LIKE '%pending%' ORDER BY c.submit_date DESC NULLS LAST LIMIT 50;",
    },
    {
        "input": "System users with role name for panther_id 002345678",
        "query": "SELECT u.panther_id, ur.role, u.active, u.campus_id FROM users AS u JOIN user_roles AS ur ON u.role = ur.user_roles_id WHERE u.panther_id = '002345678' LIMIT 10;",
    },
]

