"""HTTP/API tests are integration tests too; kept separate for learning."""

import pytest

pytestmark = pytest.mark.api


def test_list_starts_empty(client):
    response = client.get("/api/cars")
    assert response.status_code == 200
    assert response.json() == []


def test_create_returns_201_json_and_location(client, car_payload):
    response = client.post("/api/cars", json=car_payload)
    assert response.status_code == 201
    assert response.headers["content-type"] == "application/json"
    created = response.json()
    assert created == {"id": created["id"], **car_payload}
    assert created["id"] > 0
    assert response.headers["location"] == f"/api/cars/{created['id']}"
    assert client.get(response.headers["location"]).json() == created
    assert client.get("/api/cars").json() == [created]


def test_update_replaces_fields_but_keeps_id(client, car_payload):
    created = client.post("/api/cars", json=car_payload).json()
    replacement = {"make": "Honda", "model": "Civic", "year": 2025}
    response = client.put(f"/api/cars/{created['id']}", json=replacement)
    assert response.status_code == 200
    assert response.json() == {"id": created["id"], **replacement, "color": ""}
    assert client.get(f"/api/cars/{created['id']}").json() == response.json()


def test_delete_returns_204_without_a_body(client, car_payload):
    created = client.post("/api/cars", json=car_payload).json()
    path = f"/api/cars/{created['id']}"
    response = client.delete(path)
    assert response.status_code == 204
    assert response.content == b""
    assert client.get(path).status_code == 404
    assert client.get("/api/cars").json() == []


@pytest.mark.parametrize("method", ["GET", "PUT", "DELETE"])
def test_unknown_car_returns_404(client, car_payload, method):
    options = {"json": car_payload} if method == "PUT" else {}
    response = client.request(method, "/api/cars/999", **options)
    assert response.status_code == 404
    assert response.json() == {"detail": "Car not found"}


@pytest.mark.parametrize("car_id", [0, -1, "abc"])
def test_invalid_car_id_returns_422(client, car_id):
    assert client.get(f"/api/cars/{car_id}").status_code == 422


@pytest.mark.parametrize(
    "field,value",
    [("make", "   "), ("model", ""), ("year", 1885), ("year", 2101),
     ("year", True), ("year", "2024"), ("color", "x" * 41)],
)
def test_invalid_create_returns_422_and_does_not_save(client, car_payload, field, value):
    car_payload[field] = value
    response = client.post("/api/cars", json=car_payload)
    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"][-1] == field
    assert client.get("/api/cars").json() == []


def test_invalid_update_does_not_change_existing_car(client, car_payload):
    created = client.post("/api/cars", json=car_payload).json()
    path = f"/api/cars/{created['id']}"
    response = client.put(path, json={**car_payload, "year": 1700})
    assert response.status_code == 422
    assert client.get(path).json() == created


def test_malformed_json_returns_422(client):
    response = client.post("/api/cars", content="{bad json", headers={"Content-Type": "application/json"})
    assert response.status_code == 422


def test_unknown_fields_return_422(client, car_payload):
    assert client.post("/api/cars", json={**car_payload, "price": 10000}).status_code == 422


def test_html_pages_and_static_assets_are_served(client, car_payload):
    car_id = client.post("/api/cars", json=car_payload).json()["id"]
    for path in ["/", "/cars/new", f"/cars/{car_id}", f"/cars/{car_id}/edit"]:
        response = client.get(path)
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/html")
        assert "<!doctype html>" in response.text.lower()
    assert client.get("/static/app.js").status_code == 200
    assert client.get("/static/style.css").status_code == 200


def test_missing_car_pages_return_404(client):
    assert client.get("/cars/999").status_code == 404
    assert client.get("/cars/999/edit").status_code == 404


def test_openapi_documents_all_five_crud_operations(client):
    schema = client.get("/openapi.json").json()
    assert {"get", "post"} <= schema["paths"]["/api/cars"].keys()
    assert {"get", "put", "delete"} <= schema["paths"]["/api/cars/{car_id}"].keys()
