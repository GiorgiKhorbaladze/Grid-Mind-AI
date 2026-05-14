import pytest
from backend.models.message import Message, Role


def test_message_defaults():
    msg = Message(role=Role.USER, content="hello")
    assert msg.role == Role.USER
    assert msg.content == "hello"
    assert msg.id is not None
    assert msg.created_at is not None


def test_to_api_dict():
    msg = Message(role=Role.ASSISTANT, content="hi there")
    d = msg.to_api_dict()
    assert d == {"role": "assistant", "content": "hi there"}


def test_unique_ids():
    a = Message(role=Role.USER, content="x")
    b = Message(role=Role.USER, content="x")
    assert a.id != b.id
