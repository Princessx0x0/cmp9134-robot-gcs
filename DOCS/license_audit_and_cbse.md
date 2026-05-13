# License Audit & CBSE Interface Specification

## Task 3: Open-Source License Audit

| Component | Purpose in System | License | Type |
|---|---|---|---|
| FastAPI | Backend REST API framework | MIT | Permissive |
| React | Frontend UI framework | MIT | Permissive |
| SQLAlchemy | Database ORM / data access layer | MIT | Permissive |
| httpx | Async HTTP client for robot API calls | BSD 3-Clause | Permissive |
| python-jose | JWT token creation and verification | MIT | Permissive |
| bcrypt | Password hashing | Apache 2.0 | Permissive |
| tenacity | Retry logic for robot API resilience | Apache 2.0 | Permissive |
| Tailwind CSS | Frontend utility CSS framework | MIT | Permissive |
| Alembic | Database migration management | MIT | Permissive |
| pytest | Automated testing framework | MIT | Permissive |

**Conclusion:** All dependencies use permissive licences (MIT, BSD, or Apache 2.0).
None impose copyleft restrictions. The Ground Control Station codebase is therefore
under no legal obligation to be released as open source, and all dependencies may
be freely used in this academic project without licence conflict.

---

## Task 4: CBSE Interface Specification — Mission Logger Component

### Component: MissionLogger

The `MissionLogger` is treated as an independent, self-contained CBSE component
responsible for all audit trail functionality. It has no knowledge of the HTTP
layer or the robot client — it only logs what it is told to log.

### Provides Interface (services this component exposes)

| Method | Parameters | Returns | Description |
|---|---|---|---|
| `log_command` | user_id, command_type, x, y, outcome | LogEntry | Persists a command record with timestamp |
| `get_all_logs` | limit, offset | List[LogEntry] | Returns paginated audit log entries |
| `get_logs_by_user` | user_id, limit | List[LogEntry] | Returns logs filtered by user |
| `export_logs` | format (json/csv) | bytes | Exports full audit trail |

### Requires Interface (external services this component depends on)

| Dependency | Why it is needed |
|---|---|
| Database Connection | To persist log entries to SQLite via SQLAlchemy |
| System Clock | To generate accurate UTC timestamps for each entry |
| User Identity | Caller must supply authenticated user_id — logger does not resolve users itself |

### Interface Diagram (Ball and Socket notation — text representation)

```
                    ┌─────────────────────┐
                    │                     │
  log_command ──○──▷│   MissionLogger     │▷──○── Database Connection
  get_all_logs ──○──▷│    Component        │▷──○── System Clock
  get_by_user ──○──▷│                     │▷──○── User Identity
  export_logs ──○──▷│                     │
                    └─────────────────────┘

  ──○──▷  =  Provides interface (socket — accepts incoming calls)
  ▷──○──  =  Requires interface (ball — depends on external service)
```