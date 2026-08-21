from sqlalchemy import select

from app.db.models import UserProfile


def test_get_me_bootstraps_profile_row(client, db_session, test_user_id):
    resp = client.get("/me/")
    assert resp.status_code == 200
    body = resp.json()

    assert body["user_id"] == test_user_id
    assert body["profile"] == {
        "name": None,
        "years_played": None,
        "handicap": None,
        "skill_level": None,
        "goals": None,
    }

    row = db_session.execute(
        select(UserProfile).where(UserProfile.user_id == test_user_id)
    ).scalar_one()
    assert str(row.user_id) == test_user_id


def test_get_me_is_idempotent(client, db_session, test_user_id):
    client.get("/me/")
    client.get("/me/")

    rows = db_session.execute(
        select(UserProfile).where(UserProfile.user_id == test_user_id)
    ).scalars().all()
    assert len(rows) == 1


def test_update_me_sets_fields(client):
    resp = client.put("/me/", json={"name": "Jordan", "handicap": 12.5})
    assert resp.status_code == 200
    body = resp.json()

    assert body["profile"]["name"] == "Jordan"
    assert body["profile"]["handicap"] == 12.5
    assert body["profile"]["years_played"] is None


def test_update_me_partial_update_preserves_other_fields(client):
    client.put("/me/", json={"name": "Jordan", "skill_level": "intermediate"})
    resp = client.put("/me/", json={"years_played": 5})
    body = resp.json()

    assert body["profile"]["years_played"] == 5
    assert body["profile"]["name"] == "Jordan"
    assert body["profile"]["skill_level"] == "intermediate"


def test_update_me_rejects_out_of_range_handicap(client):
    resp = client.put("/me/", json={"handicap": 999})
    assert resp.status_code == 422
