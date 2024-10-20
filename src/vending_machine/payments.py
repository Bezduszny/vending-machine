import logging
import sys
from collections import defaultdict
from dataclasses import dataclass
from functools import total_ordering
from typing import Dict, List, Tuple


@total_ordering
class Denomination:
    """
    Represents a coin or a banknote.
    """

    value: int

    def __init__(self, value: int) -> None:
        if value < 0 or (value > 100 and value % 100 != 0):
            raise ValueError(f"Denomination with {value=} is not supported.")
        self.value = value

    def __hash__(self) -> int:
        return self.value

    def __str__(self) -> str:
        if self.value < 100:
            return f"{self.value}p"

        if self.value % 100 == 0:
            return f"£{self.value//100}"
        raise NotImplementedError()

    def __repr__(self) -> str:
        return f"Denomination({self.value})"

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Denomination):
            return self.value == other.value
        return False

    def __lt__(self, other: object) -> bool:
        if isinstance(other, Denomination):
            return self.value < other.value
        raise NotImplementedError()


class MonetaryInventory:
    inventory: Dict[Denomination, int]
    _supported_denominantions: List[Denomination] = [
        Denomination(200),
        Denomination(100),
        Denomination(50),
        Denomination(20),
        Denomination(10),
        Denomination(5),
        Denomination(2),
        Denomination(1),
    ]

    def __init__(
        self,
        initial_inventory: Dict[Denomination, int],
        supported_denominantions: List[Denomination] | None = None,
    ) -> None:
        if supported_denominantions is not None:
            self._supported_denominantions = supported_denominantions
        self.inventory = defaultdict(lambda: 0)
        self.add_cash(initial_inventory)

    def add_monetary_unit(self, denomination: Denomination):
        if denomination not in self._supported_denominantions:
            raise ValueError(f"{denomination} is not supported.")
        self.inventory[denomination] += 1

    def add_cash(self, supply: Dict[Denomination, int]):
        for cash in supply.keys():
            if cash not in self._supported_denominantions:
                raise ValueError(f"{cash} is not supported.")

        for cash, quantity in supply.items():
            self.inventory[cash] += quantity

    def remove_change(self, change: Dict[Denomination, int]):
        for denomination, quantity in change.items():
            if self.inventory[denomination] < quantity:
                raise RuntimeError(
                    f"Asked to remove {quantity} of {denomination}, but there's only {self.inventory[denomination]} in the inventory."
                )
            self.inventory[denomination] -= quantity

    @property
    def available_change(self) -> Dict[Denomination, int]:
        return {
            denomination: quantity
            for denomination, quantity in self.inventory.items()
            if quantity > 0
        }

    def __repr__(self) -> str:
        return f"MonetaryInventory({self.inventory=})"


@dataclass
class ChangeConfiguration:
    owed: int
    configuration: Dict[Denomination, int]

    def __init__(self, owed: int, configuration: Dict[Denomination, int]):
        self.owed = owed
        self.configuration = defaultdict(lambda: 0)
        self.configuration |= configuration

    @property
    def is_exact(self) -> bool:
        return self.owed == 0

    def __repr__(self) -> str:
        return ", ".join(
            [
                str(quantity) + " x " + str(denomination)
                for denomination, quantity in self.configuration.items()
            ]
        )


def find_optimal_change(
    owed_amount: int, monetary_inventory: MonetaryInventory
) -> ChangeConfiguration | None:
    change = {
        denomination.value: quantity
        for denomination, quantity in monetary_inventory.inventory.items()
    }
    result, diff = backtrack_best_change(owed=owed_amount, change=change)
    if result is not None:
        configuration = {
            Denomination(value): quantity for value, quantity in result.items()
        }
        return ChangeConfiguration(diff, configuration)

    return None


def backtrack_best_change(
    owed: int,
    change: Dict[int, int],
    current_solution: Dict[int, int] | None = None,
    best_solution: Dict[int, int] | None = None,
    lowest_owed: int = sys.maxsize,
) -> Tuple[Dict[int, int] | None, int]:
    logging.debug(f"{current_solution=}")
    logging.debug(f"{best_solution=}")
    logging.debug(f"{lowest_owed=}\n")

    if current_solution is None:
        current_solution = {}

    if owed < lowest_owed:
        best_solution = current_solution
        lowest_owed = owed

    if owed == 0:
        return (current_solution, 0)

    # Get available denominations in descending order to get the lowest number of monetary units possible
    denominations: List[int] = sorted(
        [k for k, v in change.items() if v > 0], reverse=True
    )

    for denomination in denominations:
        max_number_of_monetary_units = min(owed // denomination, change[denomination])
        for number_of_monetary_units in reversed(
            range(1, max_number_of_monetary_units + 1)
        ):
            new_change = change.copy()
            # otherwise lower values will be checked more than once
            new_change[denomination] = 0
            new_owed_amount = owed - number_of_monetary_units * denomination
            new_solution = current_solution.copy()
            new_solution[denomination] = number_of_monetary_units

            new_solution, difference = backtrack_best_change(
                new_owed_amount,
                new_change,
                new_solution,
                best_solution,
                lowest_owed,
            )

            if difference == 0:
                return new_solution, 0

            if difference < lowest_owed:
                best_solution = new_solution
                lowest_owed = difference

    return best_solution, lowest_owed
