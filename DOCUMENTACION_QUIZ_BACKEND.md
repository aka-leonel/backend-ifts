# Documentación Técnica - Feature: Quiz con IA (miIFTS Frontend)

> **Feature**: Quiz con IA — Generación de cuestionarios de opción múltiple a partir de PDF
> **Fecha**: 2026-10-20
> **Estado**: Implementado en Frontend (React 19 + TypeScript + Vite + Tailwind CSS v4)
> **Endpoint Backend**: `POST /quiz/` (multipart/form-data)

---

## 1. Resumen de la Funcionalidad

El módulo **Quiz con IA** permite a los estudiantes subir un archivo PDF con material de estudio y generar automáticamente un cuestionario de preguntas de opción múltiple (multiple choice) usando IA en el backend. El flujo completo es:

1. **Usuario selecciona PDF** (máx. 10 MB, validado en cliente)
2. **Usuario elige cantidad de preguntas** (3, 5, 8 o 10)
3. **Frontend envía** `POST /quiz/` con `multipart/form-data` (archivo + query param `cantidad`)
4. **Backend procesa** el PDF y genera el quiz con IA
5. **Frontend muestra** las preguntas una por una con opciones radio
6. **Usuario responde** y hace clic en "Corregir"
7. **Frontend calcula** aciertos localmente y muestra resultado + explicaciones

---

## 2. Contrato de API (Backend → Frontend)

### 2.1 Endpoint Principal

| Método | Ruta | Content-Type | Autenticación |
|--------|------|--------------|---------------|
| `POST` | `/quiz/` | `multipart/form-data` | **Requerida** (Bearer JWT) |

### 2.2 Request

**FormData fields:**
| Campo | Tipo | Descripción | Validación Frontend |
|-------|------|-------------|---------------------|
| `archivo` | `File` (binary) | PDF con material de estudio | `accept="application/pdf"`, máx. 10 MB |
| `cantidad` | `number` (query param `?cantidad=N`) | Cantidad de preguntas a generar | Enum: `[3, 5, 8, 10]`, default: 5 |

**Ejemplo de llamada:**
```typescript
const body = new FormData();
body.append("archivo", archivo); // File object
return apiClient<Quiz>(`/quiz/?cantidad=${cantidad}`, { method: "POST", body });
```

### 2.3 Response Exitosa (200)

```typescript
interface QuizResponse {
  preguntas: Pregunta[];
}

interface Pregunta {
  enunciado: string;      // Texto de la pregunta
  opciones: string[];     // Array de 4 strings (opciones A/B/C/D)
  correcta: number;       // Índice 0-3 de la opción correcta
  explicacion: string;    // Explicación de por qué es correcta (puede ser vacía)
}
```

**Ejemplo de respuesta:**
```json
{
  "preguntas": [
    {
      "enunciado": "¿Qué es una variable en programación?",
      "opciones": [
        "Un contenedor para almacenar datos",
        "Una función matemática",
        "Un tipo de bucle",
        "Un operador lógico"
      ],
      "correcta": 0,
      "explicacion": "Una variable es un espacio en memoria con un nombre simbólico que almacena un valor que puede cambiar durante la ejecución del programa."
    }
  ]
}
```

### 2.4 Códigos de Error Esperados

| Código | Causa | Manejo Frontend |
|--------|-------|-----------------|
| `400` | Archivo no es PDF / corrupto / vacío | Toast: `err.detail` del backend |
| `413` | Archivo > 10 MB (límite backend) | Toast: "El archivo supera el tamaño permitido" |
| `422` | Error de validación (ej. `cantidad` inválida) | Toast con `detail` o `errors[]` mapeado |
| `401` | Token expirado/inválido | `apiClient` intercepta → logout automático + redirect a login |
| `500` | Error interno IA / procesamiento PDF | Toast: "Error generando el quiz. Intente nuevamente." |

> **Nota**: El frontend valida **tamaño (10 MB)** y **tipo (PDF)** en cliente *antes* de enviar, pero el backend **debe revalidar** como defensa en profundidad.

---

## 3. Tipos TypeScript (Generados vía `openapi-typescript`)

Los tipos vienen de `src/api/schema.d.ts` generado con `npm run gen:api` contra el `openapi.json` del backend:

```typescript
// En src/api/types.ts (líneas 189-191)
export type Pregunta = S["Pregunta"];      // { enunciado, opciones, correcta, explicacion }
export type Quiz = S["QuizResponse"];      // { preguntas: Pregunta[] }
```

**Estructura en `schema.d.ts`:**
```typescript
// components.schemas.Pregunta
{
  enunciado: string;
  opciones: string[];        // length === 4
  correcta: number;          // 0-3
  explicacion: string;       // opcional, puede ser ""
}

// components.schemas.QuizResponse
{
  preguntas: Pregunta[];
}

// Body request (multipart)
Body_generar_quiz_quiz__post: {
  archivo: string;  // format: binary
}
```

---

## 4. Implementación Frontend (Referencia)

### 4.1 Archivos del Feature

```
src/features/quiz/
├── index.ts          # Exports públicos
├── service.ts        # Llamada HTTP pura (generarQuiz)
├── hooks.ts          # Hook React (useGenerarQuiz)
└── QuizScreen.tsx    # Pantalla completa (UI + lógica)
```

### 4.2 service.ts
```typescript
import { apiClient } from "../../api/client";
import type { Quiz } from "../../api/types";

export async function generarQuiz(archivo: File, cantidad: number): Promise<Quiz> {
  const body = new FormData();
  body.append("archivo", archivo);
  return apiClient<Quiz>(`/quiz/?cantidad=${cantidad}`, { method: "POST", body });
}
```

### 4.3 hooks.ts
```typescript
import { useAsyncAction } from "../../hooks/useAsyncQuery";
import { generarQuiz } from "./service";
import type { Quiz } from "../../api/types";

export function useGenerarQuiz() {
  return useAsyncAction<[File, number], Quiz>((archivo, cantidad) => generarQuiz(archivo, cantidad));
}
```

### 4.4 QuizScreen.tsx — Flujo de UI

| Estado | Descripción |
|--------|-------------|
| **Inicial** | Input file (PDF) + Select cantidad (3/5/8/10) + Botón "Generar quiz" |
| **Loading** | Botón deshabilitado, texto "Generando… (puede tardar unos segundos)" |
| **Quiz generado** | Lista de preguntas con opciones radio, botón "Corregir" (habilitado solo si todas respondidas) |
| **Corregido** | Muestra ✓ en correcta, borde rojo en incorrecta, explicación bajo cada pregunta, resumen "Resultado: X de Y" |
| **Reinicio** | Botón "Nuevo quiz" vuelve al estado inicial |

---

## 5. Requisitos No Funcionales (Backend)

| Requisito | Detalle |
|-----------|---------|
| **Tamaño máx. archivo** | 10 MB (validar en backend, frontend valida en cliente) |
| **Tipo de archivo** | Solo `application/pdf` (validar MIME + extensión) |
| **Tiempo de respuesta** | Puede tardar "unos segundos" (IA) — frontend no tiene timeout especial, usa fetch nativo |
| **Cantidad preguntas** | Validar que `cantidad ∈ {3,5,8,10}`; default 5 si no se envía |
| **Estructura respuesta** | Exactamente `QuizResponse { preguntas: Pregunta[] }` con `opciones.length === 4` y `correcta ∈ [0,3]` |
| **Autenticación** | JWT Bearer obligatorio (el endpoint está protegido) |
| **Rate limiting** | Recomendado (evitar abusos de IA costosa) |

---

## 6. Integración en la App (Navegación)

El Quiz es una **pestaña principal** en la navegación (BottomNav mobile + Sidebar desktop):

```typescript
// App.tsx - NavTab incluye "quiz"
type NavTab = "inicio" | "materias" | "recordatorios" | "convenios" | "quiz" | "perfil" | "admin";

// Ícono en nav (SVR inline)
{ key: "quiz", label: "Quiz", icon: <svg>...</svg> }

// Ruta en switch(screen)
case "quiz": return <QuizFeatureScreen />;
```

**Acceso**: Solo usuarios autenticados (estudiantes y admins). No requiere rol especial.

---

## 7. Checklist para Validación Backend

- [ ] Endpoint `POST /quiz/` expuesto en `openapi.json` con `multipart/form-data`
- [ ] Parámetro query `cantidad` (integer, enum 3/5/8/10, default 5)
- [ ] Campo `archivo` (binary, format: binary, max 10MB, MIME application/pdf)
- [ ] Response 200: `QuizResponse { preguntas: Pregunta[] }`
- [ ] `Pregunta` tiene `enunciado`, `opciones[4]`, `correcta` (0-3), `explicacion`
- [ ] Error 400/413/422 con `ApiError { detail, errors[] }` consistente
- [ ] Auth requerida (Bearer JWT), 401 si no hay token o expirado
- [ ] `npm run gen:api` en frontend genera tipos correctos sin errores TS
- [ ] Test manual: PDF válido → quiz generado → estructura correcta
- [ ] Test error: archivo >10MB / no PDF / cantidad inválida → 4xx con detail

---

## 8. Posibles Mejoras Futuras (Out of Scope Actual)

| Mejora | Descripción |
|--------|-------------|
| **Historial de quizzes** | Guardar quizzes generados por usuario (GET /quiz/historial) |
| **PATCH /quiz/{id}** | Permitir editar/regenerar preguntas individuales |
| **Estadísticas** | Endpoint con métricas de aciertos por materia/usuario |
| **Compartir quiz** | Generar link público para estudiar en grupo |
| **Modo examen** | Tiempo límite, una sola oportunidad, resultados guardados |

---

## 9. Contacto / Escalación

- **Frontend Owner**: Integrante asignado al feature Quiz
- **Decisiones Arquitectónicas**: Ver `docs/context/decisions.md`
- **Contrato API**: `docs/openapi.json` (fuente de verdad para `gen:api`)
- **Testing**: Ver `docs/context/testing.md` para criterios de validación

---

> **Nota para Backend**: Este documento refleja la implementación **actual del frontend**. Cualquier cambio en el contrato (nombres de campos, códigos de error, estructura de respuesta) requiere regenerar tipos (`npm run gen:api`) y ajustar el frontend en consecuencia. Mantener `openapi.json` actualizado es crítico.