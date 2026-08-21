import uuid


def _log_round(client, **overrides):
    payload = {
        "round_date": "2026-07-01",
        "course_name": "Pebble Creek",
        "score": 88,
        "score_to_par": 16,
        "putts": 32,
        "fairways_hit": 7,
        "greens_in_regulation": 9,
        "notes": "Windy back nine",
    }
    payload.update(overrides)
    return client.post("/progress/", json=payload)


def test_create_round_log(client):
    resp = _log_round(client)
    assert resp.status_code == 201
    body = resp.json()

    assert body["course_name"] == "Pebble Creek"
    assert body["score"] == 88
    assert uuid.UUID(body["id"])


def test_create_round_log_rejects_invalid_score(client):
    resp = _log_round(client, score=5)
    assert resp.status_code == 422


def test_list_progress_returns_only_own_rounds(make_client, test_user_id):
    mine = make_client(user_id=test_user_id)
    _log_round(mine)

    other_user_id = str(uuid.uuid4())
    theirs = make_client(user_id=other_user_id)
    _log_round(theirs, course_name="Other Course")

    resp = mine.get("/progress/")
    assert resp.status_code == 200
    rounds = resp.json()
    assert len(rounds) == 1
    assert rounds[0]["course_name"] == "Pebble Creek"


def test_list_progress_filters_by_date_range(client):
    _log_round(client, round_date="2026-01-10", score=90)
    _log_round(client, round_date="2026-06-15", score=85)
    _log_round(client, round_date="2026-12-01", score=80)

    resp = client.get("/progress/", params={"start_date": "2026-02-01", "end_date": "2026-07-01"})
    assert resp.status_code == 200
    rounds = resp.json()
    assert len(rounds) == 1
    assert rounds[0]["score"] == 85


def test_update_round_log(client):
    created = _log_round(client).json()

    resp = client.put(f"/progress/{created['id']}", json={"score": 79, "notes": "Career best"})
    assert resp.status_code == 200
    body = resp.json()

    assert body["score"] == 79
    assert body["notes"] == "Career best"
    assert body["course_name"] == "Pebble Creek"


def test_update_round_log_not_owned_returns_404(make_client, test_user_id):
    mine = make_client(user_id=test_user_id)
    created = _log_round(mine).json()

    theirs = make_client(user_id=str(uuid.uuid4()))
    resp = theirs.put(f"/progress/{created['id']}", json={"score": 70})
    assert resp.status_code == 404


def test_update_round_log_invalid_id_returns_422(client):
    resp = client.put("/progress/not-a-uuid", json={"score": 70})
    assert resp.status_code == 422


def test_delete_round_log(client):
    created = _log_round(client).json()

    resp = client.delete(f"/progress/{created['id']}")
    assert resp.status_code == 204

    resp = client.get("/progress/")
    assert resp.json() == []


def test_delete_round_log_not_found(client):
    resp = client.delete(f"/progress/{uuid.uuid4()}")
    assert resp.status_code == 404


def test_progress_summary_aggregates_own_rounds(make_client, test_user_id):
    mine = make_client(user_id=test_user_id)
    _log_round(mine, round_date="2026-01-01", score=90, putts=34, fairways_hit=6, greens_in_regulation=8)
    _log_round(mine, round_date="2026-02-01", score=84, putts=30, fairways_hit=9, greens_in_regulation=11)

    other = make_client(user_id=str(uuid.uuid4()))
    _log_round(other, round_date="2026-01-15", score=70)

    resp = mine.get("/progress/summary")
    assert resp.status_code == 200
    body = resp.json()

    assert body["rounds_played"] == 2
    assert body["avg_score"] == 87.0
    assert body["best_score"] == 84
    assert body["avg_putts"] == 32.0


def test_progress_summary_empty_returns_zero_rounds(client):
    resp = client.get("/progress/summary")
    assert resp.status_code == 200
    body = resp.json()

    assert body["rounds_played"] == 0
    assert body["avg_score"] is None
    assert body["best_score"] is None


def test_progress_summary_respects_date_range(client):
    _log_round(client, round_date="2026-01-01", score=95)
    _log_round(client, round_date="2026-06-01", score=80)

    resp = client.get("/progress/summary", params={"start_date": "2026-05-01"})
    body = resp.json()

    assert body["rounds_played"] == 1
    assert body["avg_score"] == 80.0
