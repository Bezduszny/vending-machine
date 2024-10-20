from transitions.extensions.diagrams import GraphMachine

from vending_machine import DeliverySystem, VendingMachine
from vending_machine.payments import MonetaryInventory
from vending_machine.products import Stock

if __name__ == "__main__":
    m = VendingMachine(
        stock=Stock(catalogue={}),
        monetary_inventory=MonetaryInventory({}),
        delivery_system=DeliverySystem(),
        MachineType=GraphMachine,
        machine_kwargs={
            "show_conditions": True,
            "show_state_attributes": True,
        },
    )

    # get_graph is assigned dynamically
    m.get_graph("Vending Machine").draw(  # type: ignore
        "vending_machine_diagram.png", prog="dot"
    )
