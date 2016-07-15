try:
    from hszinc import Quantity, use_pint
    Q_ = Quantity
    
except ImportError:
    pass
