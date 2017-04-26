try:
    from hszinc import Quantity, use_pint
    Q_ = Quantity
    from .client.loader import get_instance as connect
    
except ImportError:
    pass
