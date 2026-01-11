import pytest

def test_listar_movimientos_sin_filtros(client):
    """Verifica el listado general de movimientos"""
    response = client.get("/api/movimientos")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_filtrar_movimientos_por_fecha(client):
    """Verifica el filtro de fecha (aunque sea un rango vacío)"""
    params = {
        "desde": "2024-01-01",
        "hasta": "2024-01-31"
    }
    response = client.get("/api/movimientos", params=params)
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_excluir_traslados(client):
    """Verifica que el flag excluir_traslados sea aceptado"""
    response = client.get("/api/movimientos?excluir_traslados=true")
    assert response.status_code == 200
    
    response_false = client.get("/api/movimientos?excluir_traslados=false")
    assert response_false.status_code == 200
