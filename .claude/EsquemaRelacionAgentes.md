USER
  │
  │ pedido / decisión
  ▼
ARCHITECT
  │
  │ requirements
  │ architecture
  │ decisions
  ▼
PLANNER
  │
  │ implementation plan
  │ task decomposition
  │ status
  ▼
DEVELOPER
  │
  │ code
  ▼
TESTER
  │
  │ validation
  ▼
PLANNER
  │
  │ result / next task
  ▼
ARCHITECT
  │
  │ resultado resumido
  ▼
USER

Ownership de contexto:

ARCHITECT
├── requirements.md     ← WHAT
├── architecture.md     ← HOW / STRUCTURE
└── decisions.md        ← WHY

PLANNER
├── implementation.md   ← HOW TO EXECUTE
└── status.md           ← CURRENT STATE

DEVELOPER
├── implementation.md
└── architecture.md

TESTER
├── testing.md          ← HOW TO VALIDATE
└── requirements.md


1. requirements.md
Propósito

Es la fuente de verdad funcional del proyecto.

Responde:

¿Qué tiene que hacer el sistema?

Lo escribe

Architect.

Lo leen
Architect → principal
Planner → para planificar
Developer → requisitos específicos de la tarea
Tester → para validar comportamiento
NO debe contener
Código.
Tareas.
Estado de implementación.
Resultados de tests.
Decisiones arquitectónicas.
Logs.
Conversaciones completas.


2. architecture.md
Propósito

Responde:

¿Cómo está diseñado el sistema?

Lo escribe

Architect.

Lo leen
Architect
Planner
Developer
Tester cuando sea necesario
NO contiene
Tareas.
Estado.
Logs.
Resultados de testing.
Código completo.


3. decisions.md

Este es uno de los más importantes.

Responde:

¿Por qué elegimos esta solución?

Lo escribe

Architect.

Lo leen

Principalmente:

Architect
Planner
Developer

NO contiene:
Decisiones triviales.


4. implementation.md

Este es el territorio del Planner.

Responde:

¿Qué tenemos que hacer para implementar lo definido por Architect?

Lo escribe

Planner.

Lo leen
Planner
Developer
Architect cuando quiera revisar el plan
NO contiene
Decisiones arquitectónicas.
Test results.
Conversaciones.
Código completo


5. testing.md

Responde:

¿Cómo validamos que el sistema funciona correctamente?

Lo escribe

Tester.

Lo leen
Tester
Planner
Architect cuando necesita revisar calidad
NO contiene
Plan de desarrollo.
Arquitectura completa.
Logs gigantes.
Estado general del proyecto.