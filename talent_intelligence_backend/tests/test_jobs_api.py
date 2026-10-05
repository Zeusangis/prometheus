import pytest


@pytest.mark.parametrize("field", ["title", "jobType", "description"])
def test_missing_job_fields(client, job_payload, field):
    del job_payload["job"][field]
    response = client.post("/api/jobs", json=job_payload)
    assert response.status_code == 400
    assert response.json["error"]["code"] == "job_fields_required"


def test_created_path_and_public_job(client, job_payload):
    response = client.post("/api/jobs", json=job_payload)
    assert response.status_code == 201
    job_id = int(response.json["id"].removeprefix("job_"))
    assert response.json["publicApplicationPath"] == f"/apply/{job_id}"
    assert response.json["applicationLink"] == f"/apply/{job_id}"
    assert response.json["createdAt"].endswith("Z")
    public = client.get(f"/api/public/jobs/{job_id}")
    assert public.status_code == 200
    assert public.json["job"]["company"] == "Example Test Organization"
    assert public.json["job"]["title"] == job_payload["job"]["title"]
    assert "recruiter_data" not in public.json["job"]
    assert "interview_config" not in public.json["job"]
    detail = client.get(f"/api/jobs/job_{job_id}").json["job"]
    assert detail["languages"] == ["Python"]
    assert detail["scraperMetrics"]["languageMatch"]["weight"] == 80
    assert detail["interviewLength"] == 20


def test_job_list_update_status(client, job_id):
    assert len(client.get("/api/jobs").json["jobs"]) == 1
    response = client.patch(f"/api/jobs/{job_id}", json={"title": "Updated Test Role"})
    assert response.status_code == 200
    assert response.json["job"]["title"] == "Updated Test Role"
    response = client.patch(f"/api/jobs/{job_id}", json={"status": "invented"})
    assert response.status_code == 400
    assert client.get(f"/api/jobs/{job_id}").json["job"]["status"] == "open"
    assert client.patch(f"/api/jobs/{job_id}", json={"status": "closed"}).status_code == 200
    assert client.get(f"/api/public/jobs/{job_id}").status_code == 409


def test_unknown_and_invalid_jobs(client):
    assert client.get("/api/public/jobs/999").status_code == 404
    assert client.get("/api/jobs/not-an-id").status_code == 400


def test_invalid_create_status(client, job_payload):
    job_payload["status"] = "invented"
    assert client.post("/api/jobs", json=job_payload).status_code == 400


def test_malformed_create_payload(client):
    assert client.post("/api/jobs", json=["invalid"]).status_code == 400
    assert client.post("/api/jobs", json={"job": "invalid"}).status_code == 400
