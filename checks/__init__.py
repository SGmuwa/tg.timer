try:
    from .product import Product
    from .counterparty import Counterparty
    from .check import Check
except ImportError:
    from product import Product
    from counterparty import Counterparty
    from check import Check
