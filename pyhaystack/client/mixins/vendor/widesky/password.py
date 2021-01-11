#!python
# -*- coding: utf-8 -*-
"""
VRT Widesky low-level Password mix-in.
"""


class PasswordOpsMixin(object):
    """
    The Password operations mix-in implements low-level support for
    modifying the current Widesky user's password.
    """

    def update_password(self, new_password, callback=None):
        """
        Change the current logged in user's password.

        If the update is unsuccessful then AsynchronousException is raised.

        :param new_password: Password value.
        :param callback: The function to call after this operation
        is complete.
        """
        op = self._PASSWORD_CHANGE_OPERATION(self, new_password)
        if callback is not None:
            op.done_sig.connect(callback)
        op.go()
        return op
