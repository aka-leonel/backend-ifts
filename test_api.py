"""
Script de prueba rápida para la API de miIFTS
Ejecutar con: python test_api.py
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def print_test(name, passed):
    symbol = "✓" if passed else "✗"
    status = "PASS" if passed else "FAIL"
    print(f"{symbol} {name}: {status}")

def test_api():
    print("\n" + "="*50)
    print("TESTING miIFTS API")
    print("="*50 + "\n")

    # Test 1: Health check
    print("1. Testing health endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        print_test("GET /health", response.status_code == 200)
        print(f"   Response: {response.json()}\n")
    except Exception as e:
        print_test("GET /health", False)
        print(f"   Error: {e}\n")
        print("   ⚠️  Asegúrate de que el servidor esté corriendo:")
        print("      uvicorn app.main:app --reload\n")
        return

    # Test 2: Login
    print("2. Testing login...")
    login_data = {
        "email": "test@miifts.ar",
        "password": "test1234"
    }
    try:
        response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
        print_test("POST /auth/login", response.status_code == 200)
        if response.status_code == 200:
            token = response.json()["access_token"]
            print(f"   Token obtenido: {token[:30]}...\n")
        else:
            print(f"   Response: {response.json()}\n")
            print("   ⚠️  Ejecuta el seed primero: python seed.py\n")
            return
    except Exception as e:
        print_test("POST /auth/login", False)
        print(f"   Error: {e}\n")
        return

    headers = {"Authorization": f"Bearer {token}"}

    # Test 3: Get current user
    print("3. Testing authenticated endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/auth/me", headers=headers)
        print_test("GET /auth/me", response.status_code == 200)
        if response.status_code == 200:
            user = response.json()
            print(f"   Usuario: {user['email']} (ID: {user['id']})\n")
    except Exception as e:
        print_test("GET /auth/me", False)
        print(f"   Error: {e}\n")

    # Test 4: List carreras
    print("4. Testing carreras endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/materias/carreras")
        print_test("GET /materias/carreras", response.status_code == 200)
        if response.status_code == 200:
            carreras = response.json()
            print(f"   Carreras encontradas: {len(carreras)}\n")
    except Exception as e:
        print_test("GET /materias/carreras", False)
        print(f"   Error: {e}\n")

    # Test 5: Create carrera (NUEVO CRUD)
    print("5. Testing CREATE carrera (NUEVO CRUD)...")
    nueva_carrera = {
        "nombre": "Test Carrera",
        "duracion_cuatrimestres": 5,
        "ifts_id": 1
    }
    try:
        response = requests.post(
            f"{BASE_URL}/materias/carreras",
            json=nueva_carrera,
            headers=headers
        )
        print_test("POST /materias/carreras", response.status_code == 201)
        if response.status_code == 201:
            carrera = response.json()
            carrera_id = carrera["id"]
            print(f"   Carrera creada con ID: {carrera_id}\n")
        else:
            print(f"   Response: {response.json()}\n")
            carrera_id = None
    except Exception as e:
        print_test("POST /materias/carreras", False)
        print(f"   Error: {e}\n")
        carrera_id = None

    # Test 6: Update carrera (NUEVO CRUD)
    if carrera_id:
        print("6. Testing UPDATE carrera (NUEVO CRUD)...")
        update_data = {
            "nombre": "Test Carrera Actualizada"
        }
        try:
            response = requests.put(
                f"{BASE_URL}/materias/carreras/{carrera_id}",
                json=update_data,
                headers=headers
            )
            print_test("PUT /materias/carreras/{id}", response.status_code == 200)
            if response.status_code == 200:
                carrera = response.json()
                print(f"   Nombre actualizado: {carrera['nombre']}\n")
        except Exception as e:
            print_test("PUT /materias/carreras/{id}", False)
            print(f"   Error: {e}\n")

        # Test 7: Delete carrera (NUEVO CRUD)
        print("7. Testing DELETE carrera (NUEVO CRUD)...")
        try:
            response = requests.delete(
                f"{BASE_URL}/materias/carreras/{carrera_id}",
                headers=headers
            )
            print_test("DELETE /materias/carreras/{id}", response.status_code == 204)
            print(f"   Carrera eliminada\n")
        except Exception as e:
            print_test("DELETE /materias/carreras/{id}", False)
            print(f"   Error: {e}\n")

    # Test 8: Create materia (NUEVO CRUD)
    print("8. Testing CREATE materia (NUEVO CRUD)...")
    nueva_materia = {
        "carrera_id": 1,
        "nombre": "Test Materia",
        "codigo": "TST",
        "anio": 1,
        "cuatrimestre": 1
    }
    try:
        response = requests.post(
            f"{BASE_URL}/materias/",
            json=nueva_materia,
            headers=headers
        )
        print_test("POST /materias/", response.status_code == 201)
        if response.status_code == 201:
            materia = response.json()
            materia_id = materia["id"]
            print(f"   Materia creada con ID: {materia_id}\n")
        else:
            print(f"   Response: {response.json()}\n")
            materia_id = None
    except Exception as e:
        print_test("POST /materias/", False)
        print(f"   Error: {e}\n")
        materia_id = None

    # Test 9: Update materia (NUEVO CRUD)
    if materia_id:
        print("9. Testing UPDATE materia (NUEVO CRUD)...")
        update_data = {
            "nombre": "Test Materia Actualizada"
        }
        try:
            response = requests.put(
                f"{BASE_URL}/materias/{materia_id}",
                json=update_data,
                headers=headers
            )
            print_test("PUT /materias/{id}", response.status_code == 200)
            if response.status_code == 200:
                materia = response.json()
                print(f"   Nombre actualizado: {materia['nombre']}\n")
        except Exception as e:
            print_test("PUT /materias/{id}", False)
            print(f"   Error: {e}\n")

        # Test 10: Delete materia (NUEVO CRUD)
        print("10. Testing DELETE materia (NUEVO CRUD)...")
        try:
            response = requests.delete(
                f"{BASE_URL}/materias/{materia_id}",
                headers=headers
            )
            print_test("DELETE /materias/{id}", response.status_code == 204)
            print(f"   Materia eliminada\n")
        except Exception as e:
            print_test("DELETE /materias/{id}", False)
            print(f"   Error: {e}\n")

    print("="*50)
    print("TESTING COMPLETADO")
    print("="*50)
    print("\nPara más detalles, visita: http://localhost:8000/docs\n")

if __name__ == "__main__":
    test_api()
