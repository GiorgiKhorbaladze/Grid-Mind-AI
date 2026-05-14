import pytest
from backend.models.message import Role
from backend.services.session.manager import SessionManager, SessionNotFoundError


def test_create_and_retrieve_session():
    mgr = SessionManager()
    session = mgr.create_session(metadata={"user": "test"})
    retrieved = mgr.get_session(session.id)
    assert retrieved.id == session.id
    assert retrieved.metadata["user"] == "test"


def test_get_missing_session_raises():
    mgr = SessionManager()
    import uuid
    with pytest.raises(SessionNotFoundError):
        mgr.get_session(uuid.uuid4())


def test_add_message_appends():
    mgr = SessionManager()
    session = mgr.create_session()
    mgr.add_message(session.id, Role.USER, "hello")
    mgr.add_message(session.id, Role.ASSISTANT, "hi")
    assert session.message_count == 2


def test_history_limit_enforced():
    mgr = SessionManager(max_history=3)
    session = mgr.create_session()
    for i in range(10):
        mgr.add_message(session.id, Role.USER, str(i))
    assert session.message_count == 3
    assert session.messages[-1].content == "9"


def test_delete_session():
    mgr = SessionManager()
    session = mgr.create_session()
    sid = session.id
    mgr.delete_session(sid)
    assert not mgr.session_exists(sid)


def test_list_sessions():
    mgr = SessionManager()
    s1 = mgr.create_session()
    s2 = mgr.create_session()
    ids = mgr.list_sessions()
    assert s1.id in ids
    assert s2.id in ids
