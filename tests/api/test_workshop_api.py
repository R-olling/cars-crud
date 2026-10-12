def test_post_car_returns_201_and_json(client):
    payload = {
        "make": "Ford",
        "model": "Fiesta",
        "year": 2018,
        "color": "Black",
    }
    response = client.post("/api/cars", json=payload)
    assert response.status_code == 201
    car = response.json()
    assert car["id"] > 0
    assert car["make"] == "Ford"
    assert car["model"] == "Fiesta"
    assert response.headers["location"] == f"/api/cars/{car['id']}"


def test_invalid_year_is_not_saved(client):
    response = client.post(
        "/api/cars",
        json={"make": "Ford", "model": "Fiesta", "year": 1800, "color": "Black"},
    )
    assert response.status_code == 422
    assert client.get("/api/cars").json() == []
