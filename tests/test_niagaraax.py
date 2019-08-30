# -*- coding: utf-8 -*-
"""
First test... just import something...
"""
import pytest

from pyhaystack.client.niagara import NiagaraHaystackSession


@pytest.fixture(scope="module")
def session(request):
    session = NiagaraHaystackSession(
        uri="http://www.myserver.com", username="user_name", password="M87h$&"
    )

    def terminate():
        session = None
        print("It's over")

    request.addfinalizer(terminate)
    return session


def test_session_username(session):
    assert session._username == "user_name"


def test_session_password(session):
    assert session._password == "M87h$&"
