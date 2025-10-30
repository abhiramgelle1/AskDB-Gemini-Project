# AskDB Database Schema

## Tables Overview

### 1. **contacts** (Primary Table)
Primary table for all students/contacts.

**Key Fields:**
- `student_name` - Primary identifier
- `first_name`, `last_name`
- `email`, `phone`
- `occupation`, `job_title`
- `addresses` (physical, mailing)
- `social_profiles` (LinkedIn, Facebook, Twitter)
- `deleted_status`

**Relationships:**
- → `cases` (one-to-many via `student_name`)
- → `orders` (one-to-many via `student_name`)
- → `student_programs` (one-to-many via `student_name`)

---

### 2. **cases**
Stores support cases for students.

**Key Fields:**
- `case_id` (Primary Key)
- `case_number` (Unique)
- `student_name` → **links to contacts.student_name**
- `subject`, `category`, `subcategory`
- `status` (Open, Closed, Pending)
- `description`, `notes`
- `deleted_status`

**Relationships:**
- ← `contacts` (many-to-one via `student_name`)

---

### 3. **orders**
Student orders/purchases.

**Key Fields:**
- `order_id` (Primary Key)
- `student_name` → **links to contacts.student_name**
- `program_id`
- `order_date`, `order_value`

**Relationships:**
- ← `contacts` (many-to-one via `student_name`)
- → `payments` (one-to-many via `order_id`)

---

### 4. **payments**
Payment records for orders.

**Key Fields:**
- `payment_id` (Primary Key)
- `payment_number` (Unique)
- `order_id` → **links to orders.order_id**
- `amount`, `payment_type`
- `payment_date`
- `payment_status` (done, pending, in-progress)

**Relationships:**
- ← `orders` (many-to-one via `order_id`)

---

### 5. **student_programs**
Student enrollment in programs.

**Key Fields:**
- `program_id`
- `student_name` → **links to contacts.student_name**
- `program_name`
- `start_date`, `end_date`
- `active_status`, `deleted_status`

**Relationships:**
- ← `contacts` (many-to-one via `student_name`)
- ← `programs` (many-to-one via `program_id`)

---

### 6. **programs**
Available programs/courses.

**Key Fields:**
- `program_id` (Primary Key)
- `program_name`
- `deleted_status`

**Relationships:**
- → `student_programs` (one-to-many via `program_id`)

---

### 7. **tasks**
Task management.

**Key Fields:**
- `task_id` (Primary Key)
- `task_number` (Unique)
- `title`, `category`
- `assignment_details`
- `start_time`, `end_time`
- `deleted_status`

---

## Common Query Patterns

### Find contacts with their cases:
```sql
SELECT c.student_name, c.email, cs.case_number, cs.subject, cs.status 
FROM contacts c 
LEFT JOIN cases cs ON c.student_name = cs.student_name 
WHERE c.deleted_status = 0;
```

### Find contacts who made payments over $5000:
```sql
SELECT DISTINCT c.student_name, c.email, c.phone 
FROM contacts c 
JOIN orders o ON c.student_name = o.student_name 
JOIN payments p ON o.order_id = p.order_id 
WHERE p.amount > 5000;
```

### Find orphan cases (cases without matching contacts):
```sql
SELECT c.* 
FROM cases c 
LEFT JOIN contacts ct ON c.student_name = ct.student_name 
WHERE ct.student_name IS NULL;
```

### Total payments by student:
```sql
SELECT c.student_name, SUM(p.amount) as total_payments 
FROM contacts c 
JOIN orders o ON c.student_name = o.student_name 
JOIN payments p ON o.order_id = p.order_id 
WHERE p.payment_status = 'done' 
GROUP BY c.student_name 
ORDER BY total_payments DESC;
```

---

## Entity Relationship Diagram

```
contacts (student_name)
    ├── cases (student_name FK)
    ├── orders (student_name FK)
    │   └── payments (order_id FK)
    └── student_programs (student_name FK)
            └── programs (program_id FK)
```
