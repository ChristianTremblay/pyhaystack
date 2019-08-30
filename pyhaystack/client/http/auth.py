# -*- coding: utf-8 -*-
"""
Base HTTP client authentication classes.  These classes simply act as
containers for authentication methods defined in the HTTP spec.
"""


class AuthenticationCredentials(object):
    """
    A base class to represent authentication credentials.
    """

    pass


class UserPasswordAuthenticationCredentials(AuthenticationCredentials):
    """
    A base class that represents username/password type authentication.
    """

    def __init__(self, username, password):
        self.username = username
        self.password = password


class BasicAuthenticationCredentials(UserPasswordAuthenticationCredentials):
    """
    A class that represents Basic authentication.
    """

    pass


class DigestAuthenticationCredentials(UserPasswordAuthenticationCredentials):
    """
    A class that represents Digest authentication.
    """

    pass
