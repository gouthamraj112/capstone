from fastapi.testclient import TestClient
from app import main

client = TestClient(main.app)


def test_irrelevant_query_triggers_guardrail_warning():
    res = client.post("/api/query", json={"question": "What is the capital of France?", "language": "en"})
    assert res.status_code == 200
    data = res.json()
    assert data["is_relevant"] is False
    assert data["intent"] == "out_of_scope"
    assert data["warning"] is not None
    assert "Off-Topic Query Detected" in data["warning"]
    assert "Smart Grid" in data["answer"]
    assert len(data["suggested_queries"]) > 0


def test_cooking_recipe_triggers_guardrail():
    res = client.post("/api/query", json={"question": "How do I bake a chocolate cake?", "language": "en"})
    assert res.status_code == 200
    data = res.json()
    assert data["is_relevant"] is False
    assert data["intent"] == "out_of_scope"
    assert "Notice: Off-Topic" in data["answer"]


def test_coding_question_triggers_guardrail():
    res = client.post("/api/query", json={"question": "Write a python script to reverse a linked list", "language": "en"})
    assert res.status_code == 200
    data = res.json()
    assert data["is_relevant"] is False
    assert data["intent"] == "out_of_scope"


def test_greeting_gives_welcoming_energy_guidance():
    res = client.post("/api/query", json={"question": "Hello there", "language": "en"})
    assert res.status_code == 200
    data = res.json()
    assert data["intent"] == "greeting"
    assert "Smart Grid Energy Intelligence Assistant" in data["answer"]
    assert len(data["suggested_queries"]) > 0


def test_multilingual_guardrail_warning():
    res = client.post("/api/query", json={"question": "¿Quién es el presidente de Francia?", "language": "es"})
    assert res.status_code == 200
    data = res.json()
    assert data["is_relevant"] is False
    assert "fuera de tema" in data["answer"].lower()
    assert len(data["suggested_queries"]) > 0
