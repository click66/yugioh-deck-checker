import requests

BASE_URL = "http://localhost:8000/v2"


def test_create_consistency_job_and_read_status():
    # Given an expected payload
    payload = {
        "deckcount": 40,
        "names": [
            "newalbaz", "mululu", "lukias", "faimena", "ht",
            "cart", "ecclesia", "panurg", "phyrx", "ketu",
            "rahu", "fusion", "spoon", "corwley", "zoroa"
        ],
        "ratios": [3, 1, 3, 3, 12, 1, 1, 3, 1, 1, 3, 2, 0, 0, 0],
        "ideal_hands": [
            ["newalbaz"], ["ecclesia"], ["fusion"], ["spoon"],
        ],
        "num_hands": 1_000_000,
    }

    # When the request is made
    response = requests.post(
        f"{BASE_URL}/consistency/jobs/create",
        json=payload,
    )

    # Then a 200 response with job ID and status is returned
    assert response.status_code == 200, "Request failed"
    data = response.json()
    assert "jobId" in data, "Response missing job_id"
    assert "status" in data, "Response missing status"
    assert data["status"] in {
        "pending",
        "running",
        "completed",
    }, "Unexpected status value"

    # And When a request is made for the status of that job
    response = requests.get(f"{BASE_URL}/consistency/jobs/{data['jobId']}")

    # Then a 200 response is returned with a valid status
    assert response.status_code == 200, "Request failed"
    data = response.json()
    assert "status" in data, "Response missing status"
    assert data["status"] in {
        "pending",
        "running",
        "completed",
    }


def test_create_400_if_names_and_ratios_different_lengths():
    # Given a payload that contains "names" and "ratios" as lists of differing lengths
    payload = {
        "deckcount": 40,
        "names": ["one", "two", "three"],
        "ratios": [1, 2, 3, 4],
        "ideal_hands": [],
        "num_hands": 1_000_000,
    }

    # When the request is made
    response = requests.post(
        f"{BASE_URL}/consistency/jobs/create",
        json=payload,
    )

    # Then a 400 response with relevant detail is returned
    assert response.status_code == 400, "Request failed"
    data = response.json()
    assert "detail" in data, "Error response missing detail"
    assert data['detail'] == "names and ratios must be the same length"


def test_read_nonexistent_job():
    # When a request is made for the status of a non-existent job
    response = requests.get(
        f"{BASE_URL}/consistency/jobs/4df1a4db-7f6a-491e-8e82-884927bb8522",
    )

    # Then a 404 response is returned
    assert response.status_code == 404, "Request failed"
