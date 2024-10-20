import logging
from enum import Enum, auto
from typing import Any, Callable, Dict, Type

from transitions import EventData, Machine

from .payments import (
    ChangeConfiguration,
    Denomination,
    MonetaryInventory,
    find_optimal_change,
)
from .products import Product, Stock

logger = logging.getLogger("vending_machine")
logger.setLevel(logging.DEBUG)


class States(Enum):
    IDLE = auto()
    MAINTENANCE_MODE = auto()
    PRODUCT_SELECTION = auto()
    COLLECTING_PAYMENT = auto()
    CONFIRM_SMALLER_CHANGE = auto()
    DISPATCHING_PRODUCT = auto()
    RETURNING_CHANGE = auto()


class DeliverySystem:
    def dispatch(self, product: Product):
        logger.info(f"{product} has been dispatched!")

    def send_cash(self, change_configuration: ChangeConfiguration):
        logger.info(f"Sending {change_configuration} to the customer.")


def get_condition_name(func: Callable | str) -> str:
    try:
        return func.__name__  # type: ignore
    except Exception:
        return str(func)


class VendingMachine:
    stock: Stock
    monetary_inventory: MonetaryInventory
    selected_product: int | None = None
    customer_balance: int = 0
    is_in_maintenance_mode: bool = False
    delivery_system: DeliverySystem

    def __init__(
        self,
        stock: Stock,
        monetary_inventory: MonetaryInventory,
        delivery_system: DeliverySystem,
        MachineType: Type[Machine] = Machine,
        machine_kwargs: Dict[str, Any] = {},
    ) -> None:
        self.stock = stock
        self.monetary_inventory = monetary_inventory
        self.delivery_system = delivery_system
        self.machine = MachineType(
            model=self,
            states=self._get_states(),
            transitions=self._get_transitions(),
            initial=States.IDLE,
            after_state_change=self.on_state_change,
            send_event=True,
            model_override=True,
            **machine_kwargs,
        )

    def _get_states(self):
        return [
            States.IDLE,
            States.MAINTENANCE_MODE,
            States.PRODUCT_SELECTION,
            States.COLLECTING_PAYMENT,
            States.CONFIRM_SMALLER_CHANGE,
            {
                "name": States.DISPATCHING_PRODUCT,
                "on_enter": [self._dispatch_product, "advance"],
            },
            {
                "name": States.RETURNING_CHANGE,
                "on_enter": [self._return_change, "advance"],
            },
        ]

    def _get_transitions(self):
        return [
            {
                "trigger": "start_maintenance",
                "source": States.IDLE,
                "dest": States.MAINTENANCE_MODE,
            },
            {
                "trigger": "reload_change",
                "source": States.MAINTENANCE_MODE,
                "dest": States.MAINTENANCE_MODE,
                "before": [self._reload_change],
            },
            {
                "trigger": "add_products",
                "source": States.MAINTENANCE_MODE,
                "dest": States.MAINTENANCE_MODE,
                "before": [self._add_products],
            },
            {
                "trigger": "end_maintenance",
                "source": States.MAINTENANCE_MODE,
                "dest": States.IDLE,
            },
            {
                "trigger": "start",
                "source": States.IDLE,
                "dest": States.PRODUCT_SELECTION,
            },
            {
                "trigger": "cancel",
                "source": States.PRODUCT_SELECTION,
                "dest": States.IDLE,
            },
            {
                "trigger": "select",
                "source": States.PRODUCT_SELECTION,
                "dest": States.COLLECTING_PAYMENT,
                "before": [self._select],
            },
            {
                "trigger": "insert",
                "source": States.COLLECTING_PAYMENT,
                "dest": States.COLLECTING_PAYMENT,
                "before": [self._insert],
            },
            {
                "trigger": "checkout",
                "source": States.COLLECTING_PAYMENT,
                "dest": States.COLLECTING_PAYMENT,
                "conditions": [self._not_enough_money],
            },
            {
                "trigger": "checkout",
                "source": States.COLLECTING_PAYMENT,
                "dest": States.DISPATCHING_PRODUCT,
                "conditions": [self._can_return_exact_change],
                "before": [self._charge_customer],
            },
            {
                "trigger": "checkout",
                "source": States.COLLECTING_PAYMENT,
                "dest": States.CONFIRM_SMALLER_CHANGE,
            },
            {
                "trigger": "accept",
                "source": States.CONFIRM_SMALLER_CHANGE,
                "dest": States.DISPATCHING_PRODUCT,
                "before": [self._charge_customer],
            },
            {
                "trigger": "advance",
                "source": States.DISPATCHING_PRODUCT,
                "dest": States.RETURNING_CHANGE,
            },
            {
                "trigger": "advance",
                "source": States.RETURNING_CHANGE,
                "dest": States.IDLE,
            },
            {
                "trigger": "cancel",
                "source": [States.COLLECTING_PAYMENT, States.CONFIRM_SMALLER_CHANGE],
                "dest": States.RETURNING_CHANGE,
            },
        ]

    def on_state_change(self, event: EventData) -> None:
        if event.state and event.transition and event.event:
            logger.info(
                f"{type(self).__name__} state changed: {event.state.name}   Transition: {event.event.name}  {event.transition.source} -> {event.transition.dest} {[get_condition_name(c.func) for c in event.transition.conditions]}"
            )
        else:
            logger.info(f"{type(self).__name__} state changed: {event}")
        if event.error:
            logger.error(event.error)

    # Typing support for triggers
    def start(self) -> None:
        raise RuntimeError("Should be overriden!")

    def start_maintenance(self) -> None:
        raise RuntimeError("Should be overriden!")

    def end_maintenance(self) -> None:
        raise RuntimeError("Should be overriden!")

    def select(self, product_id: int) -> None:
        raise RuntimeError("Should be overriden!")

    def insert(self, denomination: int) -> None:
        raise RuntimeError("Should be overriden!")

    def checkout(self) -> None:
        raise RuntimeError("Should be overriden!")

    def cancel(self) -> None:
        raise RuntimeError("Should be overriden!")

    def accept(self) -> None:
        raise RuntimeError("Should be overriden!")

    def advance(self) -> None:
        raise RuntimeError("Should be overriden!")

    def add_products(self, *products: Product) -> None:
        raise RuntimeError("Should be overriden!")

    def reload_change(self, supply: Dict[Denomination, int]) -> None:
        """
        Adds cash from the specified supply to the vending machine's inventory.

        Parameters:
            supply (Dict[Denomination, int]): A dictionary mapping Denomination objects
            to their quantities, representing the cash to be added.

        If a cash type does not exist in the inventory, it will be added.

        Example:
            supply = {Denomination(1): 5, Denomination(2): 10}
            vending_machine.add_cash(cash_supply)
        """
        raise RuntimeError("Should be overriden!")

    # Conditions
    def _not_enough_money(self, _) -> bool:
        assert self.selected_product is not None
        total = self.stock.get_price_of(self.selected_product)
        return total > self.customer_balance

    def _can_return_exact_change(self, _) -> bool:
        assert self.selected_product is not None
        owed_change = self.customer_balance - self.stock.get_price_of(
            self.selected_product
        )

        config: ChangeConfiguration | None = find_optimal_change(
            owed_change, self.monetary_inventory
        )
        if config is None:
            return False

        return config.is_exact

    # Actions
    def _go_to_returning_change(self, _) -> None:
        self.machine.set_state(States.RETURNING_CHANGE)  # type: ignore

    def _go_to_idle(self, _) -> None:
        self.machine.set_state(States.IDLE)

    def _select(self, event: EventData) -> None:
        product_id = event.kwargs.get("product_id", None)
        self.selected_product = product_id

    def _insert(self, event: EventData) -> None:
        denomination = event.kwargs.get("denomination", None)
        self.customer_balance += denomination
        self.monetary_inventory.add_monetary_unit(Denomination(denomination))

    def _cancel(self, _) -> None:
        self.selected_product = None

    def _add_products(self, event: EventData) -> None:
        products = event.kwargs.get("products", [])
        self.stock.add_products(*products)

    def _reload_change(self, event: EventData) -> None:
        supply = event.kwargs.get("supply", {})
        self.monetary_inventory.add_cash(supply)

    def _dispatch_product(self, _):
        product = self.stock.get_product(self.selected_product)
        self.selected_product = None
        self.delivery_system.dispatch(product)

    def _charge_customer(self, _):
        if self.selected_product is not None:
            self.customer_balance -= self.stock.get_price_of(self.selected_product)

    def _return_change(self, _) -> None:
        if self.customer_balance == 0:
            return

        config: ChangeConfiguration | None = find_optimal_change(
            owed_amount=self.customer_balance,
            monetary_inventory=self.monetary_inventory,
        )
        if config is None or not config.configuration:  # not able to return a change
            return

        self.monetary_inventory.remove_change(config.configuration)
        self.delivery_system.send_cash(config)
