import pytest
import transitions

from vending_machine import DeliverySystem, States, VendingMachine
from vending_machine.payments import Denomination, MonetaryInventory
from vending_machine.products import Product, ProductInfo, Stock


class TestVendingMachine:
    def setup_method(self):
        self.machine = VendingMachine(
            Stock(
                catalogue={
                    1: ProductInfo("Soda", 210),
                    2: ProductInfo("Water", 100),
                    3: ProductInfo("Ice tea", 195),
                },
                products=(
                    Product(1),
                    Product(1),
                    Product(2),
                    Product(3),
                ),
            ),
            MonetaryInventory({Denomination(100): 5, Denomination(10): 3}),
            DeliverySystem(),
        )

    def test_maintenance(self):
        self.machine.start_maintenance()
        self.machine.reload_change(supply={Denomination(50): 10})
        assert self.machine.monetary_inventory.inventory == {
            Denomination(100): 5,
            Denomination(10): 3,
            Denomination(50): 10,
        }

        self.machine.add_products(products=(Product(2),))
        assert self.machine.stock.products[2].qsize() == 2

        self.machine.end_maintenance()
        assert self.machine.machine.is_state(States.IDLE, self.machine)

    def test_maintenance_not_allowed(self):
        self.machine.start()

        with pytest.raises(transitions.core.MachineError):
            self.machine.start_maintenance()

    def test_simple_transaction(self):
        self.machine.start()
        self.machine.select(product_id=2)
        self.machine.insert(denomination=100)
        self.machine.checkout()
        assert self.machine.machine.is_state(States.IDLE, self.machine)

    def test_transaction_with_change(self):
        self.machine.start()
        self.machine.select(product_id=2)
        self.machine.insert(denomination=200)
        self.machine.checkout()
        assert self.machine.machine.is_state(States.IDLE, self.machine)
        assert self.machine.monetary_inventory.inventory == {
            Denomination(200): 1,
            Denomination(100): 4,
            Denomination(10): 3,
        }

    def test_accept_transaction_with_missing_change(self):
        self.machine.start()
        self.machine.select(product_id=3)
        self.machine.insert(denomination=200)
        self.machine.checkout()
        self.machine.accept()
        assert self.machine.machine.is_state(States.IDLE, self.machine)

        assert self.machine.monetary_inventory.inventory == {
            Denomination(200): 1,
            Denomination(100): 5,
            Denomination(10): 3,
        }

    def test_cancel_transaction_with_missing_change(self):
        self.machine.start()
        self.machine.select(product_id=3)
        self.machine.insert(denomination=200)
        self.machine.checkout()
        self.machine.cancel()

        assert self.machine.machine.is_state(States.IDLE, self.machine)

        # there was one product and still is one product
        assert self.machine.stock.products[3].qsize() == 1

        # inserted money has been returned
        assert self.machine.monetary_inventory.available_change == {
            Denomination(100): 5,
            Denomination(10): 3,
        }
