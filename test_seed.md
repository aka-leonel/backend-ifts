# Pasos para ejecutar el seed

## 1. Asegúrate de estar en el directorio correcto
cd C:\Users\juan\backend-ifts

## 2. Activa el entorno virtual
.\venv\Scripts\activate

## 3. Ejecuta el seed (esto borra y recrea la DB)
python seed.py

## Qué hace el seed:
- Borra miifts.db si existe
- Crea todas las tablas
- Inserta:
  - 1 IFTS
  - 2 Carreras
  - 19 Materias
  - 11 Correlativas
  - 1 Usuario de prueba (email: test@miifts.ar, password: test1234)

## Después del seed tendrás:
- Usuario ID 1 (test@miifts.ar)
- Carrera ID 1 y 2
- Materias ID 1-19
