# Database Schema

The default backend uses **SQLite** at `backend/app.db`. Switch to **Postgres**
by setting `DATABASE_URL=postgresql+psycopg://user:pass@host:5432/db`.

All tables use surrogate `id` primary keys, UTC timestamps, and indexes on
foreign keys + commonly filtered columns.

## ER Diagram

```mermaid
erDiagram
    users ||--o{ students : owns
    users ||--o{ recommendations : creates
    users ||--o{ counseling_sessions : conducts
    users ||--o{ uploads : uploaded_by
    users ||--o{ audit_logs : performs
    users ||--o{ faculty_notes : authors

    departments ||--o{ users : has
    departments ||--o{ students : has

    students ||--o{ predictions : has
    students ||--o{ recommendations : receives
    students ||--o{ counseling_sessions : attends
    students ||--o{ risk_history : tracks
    students ||--o{ faculty_notes : has

    predictions ||--o{ recommendations : informs

    users {
      int id PK
      string email UK
      string hashed_password
      string full_name
      enum role "admin|faculty|student"
      int department_id FK
      bool is_active
      datetime created_at
      datetime updated_at
    }

    departments {
      int id PK
      string name UK
      string code
      datetime created_at
    }

    students {
      int id PK
      string roll_no UK
      string name
      int age
      string gender
      int department_id FK
      int semester
      float attendance_pct
      float internal_marks
      float semester_marks
      int backlogs
      bool fee_paid
      int fee_delay_days
      enum financial_status "low|medium|high"
      text family_background
      text behavioral_indicators
      text extracurricular
      enum placement_readiness "low|medium|high"
      text counselor_remarks
      text faculty_notes
      datetime created_at
      datetime updated_at
    }

    predictions {
      int id PK
      int student_id FK
      enum risk_level "low|medium|high"
      float confidence
      string model_version
      json features_json
      json explanation_json
      datetime created_at
    }

    recommendations {
      int id PK
      int student_id FK
      int prediction_id FK
      text summary
      json plan_json
      enum source "llm|fallback"
      enum status "pending|in_progress|completed|dismissed"
      int created_by FK
      datetime created_at
      datetime updated_at
    }

    uploads {
      int id PK
      string filename
      string original_name
      string file_type
      int size_bytes
      int rows_imported
      enum status "pending|parsed|imported|failed"
      text error
      int uploaded_by FK
      datetime created_at
    }

    counseling_sessions {
      int id PK
      int student_id FK
      int faculty_id FK
      text notes
      text outcome
      date next_followup
      datetime created_at
    }

    audit_logs {
      int id PK
      int user_id FK
      string action
      string entity
      int entity_id
      json meta_json
      datetime created_at
    }

    risk_history {
      int id PK
      int student_id FK
      enum risk_level "low|medium|high"
      float confidence
      datetime snapshot_date
    }

    faculty_notes {
      int id PK
      int student_id FK
      int faculty_id FK
      text note
      datetime created_at
    }
```

## Indexes

| Table                | Index                                       | Purpose                  |
|----------------------|---------------------------------------------|--------------------------|
| students             | `idx_students_department`, `idx_students_created` | Faculty filters     |
| predictions          | `idx_predictions_student_created`           | Latest prediction lookup |
| risk_history         | `idx_risk_history_student_date`             | Trend lines              |
| recommendations      | `idx_reco_student_created`                  | History panel            |
| audit_logs           | `idx_audit_user_created`, `idx_audit_entity`| Forensics                |
| counseling_sessions  | `idx_counseling_student_created`            | Faculty timeline         |

## Migrations

* Alembic is initialized under `backend/alembic/`.
* On the very first run, `init_db.py` calls `Base.metadata.create_all()` so the
  app works with zero migration steps; subsequent schema changes go through
  `alembic revision --autogenerate`.
