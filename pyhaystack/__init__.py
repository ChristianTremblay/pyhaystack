try:
    from hszinc import Quantity, use_pint
    Q_ = Quantity
    from .client.loader import get_instance as connect
    import requests.packages.urllib3
    from requests.packages.urllib3.exceptions import SubjectAltNameWarning
    requests.packages.urllib3.disable_warnings(SubjectAltNameWarning)


except ImportError:
    pass
