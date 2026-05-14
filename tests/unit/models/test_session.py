import pytest
from backend.models.message import Message, Role
from backend.models.session import Session


def test_session_add_message():
    session = Session()
    msg = Message(role=Role.USER, content="hello")
    session.add_message(msg)
    assert session.message_count == 1


def test_session_get_history_limited():
    session = Session()
    for i in range(10):
        session.add_message(Message(role=Role.USER, content=str(i)))
    history = session.get_history(max_messages=5)
    assert len(history) == 5
    assert history[-1].content == "9"


def test_session_get_history_all():
    session = Session()
    for i in range(3):
        session.add_message(Message(role=Role.USER, content=str(i)))
    assert len(session.get_history()) == 3


def test_session_updated_at_advances():
    session = Session()
    before = session.updated_at
    session.add_message(Message(role=Role.USER, content="x"))
    assert session.updated_at >= before
