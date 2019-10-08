#!python
# -*- coding: utf-8 -*-
"""
Haystack Implementation loader and factory.  This module provides a simplified
wrapper around importlib to allow implementation of a near-consistent interface
for fetching session instances.
"""

from importlib import import_module
from six import string_types

# IMPLEMENTATION ALIASES: These help map short-hand aliases to full session
# instances.  Further aliases can be added here.
IMPLEMENTATION_ALIAS = {
    "niagara-ax": "niagara.NiagaraHaystackSession",
    "ax": "niagara.NiagaraHaystackSession",
    "niagara4": "niagara.Niagara4HaystackSession",
    "n4": "niagara.Niagara4HaystackSession",
    "skyspark2": "skyspark.SkysparkHaystackSession",
    "skyspark": "skyspark.SkysparkScramHaystackSession",
    "widesky": "widesky.WideskyHaystackSession",
}

# KNOWN IMPLEMENTATIONS: This is populated at run time with instances of session
# classes as they are loaded.  It should be empty at first.
_known_implementations = {}


def get_implementation(implementation):
    """
    Get an implementation of Project Haystack session manager based on
    the class name.
    """
    # De-reference aliases first.
    if implementation in IMPLEMENTATION_ALIAS:
        implementation = IMPLEMENTATION_ALIAS[implementation]

    try:
        return _known_implementations[implementation]
    except KeyError:
        # Not here, we need to load it.
        pass

    # Extract class name from implementation
    implementation_parts = implementation.split(".")
    implementation_class = implementation_parts.pop()
    implementation_mod = ".".join(implementation_parts)

    # Try short name, e.g. widesky.WideskySession
    try:
        mod = import_module(".%s" % implementation_mod, package="pyhaystack.client")
    except ImportError:
        # Nope, not a short name, try the absolute full name.
        mod = import_module(implementation_mod)

    # If we didn't get an ImportError, look for the class.
    try:
        impl = getattr(mod, implementation_class)
    except AttributeError:
        # Is it aliased?
        if hasattr(mod, "IMPLEMENTATIONS"):
            impl_alias = getattr(mod, "IMPLEMENTATIONS")
            try:
                impl = impl_alias[implementation_class]
            except KeyError:
                raise ImportError("No implementation named %s" % implementation)
        else:
            raise ImportError("No implementation named %s" % implementation)
    _known_implementations[implementation] = impl
    return impl


def get_instance(implementation, *args, **kwargs):
    """
    Get an instance of a Project Haystack client.
    """
    if isinstance(implementation, string_types):
        implementation = get_implementation(implementation)

    return implementation(*args, **kwargs)
