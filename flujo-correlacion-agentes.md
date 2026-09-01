USER
 │
 │ "Quiero agregar X"
 ▼
ARCHITECT
 │
 ├── lee requirements.md
 ├── lee architecture.md
 ├── lee decisions.md
 │
 ├── analiza repo
 │
 ├── actualiza contexto
 │
 ▼
PLANNER
 │
 ├── lee requirements
 ├── lee architecture
 ├── lee decisions
 ├── actualiza implementation.md
 ├── actualiza status.md
 │
 ├───────────────┐
 ▼               ▼
DEVELOPER      TESTER
 │               │
 │               │
 └───────┬───────┘
         ▼
       PLANNER
         │
         ├── actualiza status.md
         │
         ▼
      ARCHITECT
         │
         ▼
        USER