try:
    from .transfer import Transfer
    from .product import Product
    from .counterparty import Counterparty
    from .check import Check
except ImportError:
    from transfer import Transfer
    from product import Product
    from counterparty import Counterparty
    from check import Check
