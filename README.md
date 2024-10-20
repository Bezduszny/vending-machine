[![Python Version](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)

# vending-machine

Design a vending machine using a programming language of your choice. The vending machine should perform as follows:

- Once an item is selected and the appropriate amount of money is inserted, the vending machine should return the correct product.
- It should also return change if too much money is provided, or ask for more money if insufficient funds have been inserted.
- The machine should take an initial load of products and change. The change will be of denominations 1p, 2p, 5p, 10p, 20p, 50p, £1, £2. There should be a way of reloading either products or change at a later point.
- The machine should keep the state of products and change that it contains up to date.


## Clarifying questions:

### Q: What should the machine do if it can’t return the exact change? For instance, if the machine needs to return 150p but only has two £1 coins, should the transaction be canceled? Alternatively, should the machine return £2, or ask the customer if they are willing to accept £1 instead?

**Assumption:** Machine should not return higher change to avoid profits loss. For some customers it may be more important to get the product than to get the exact change. It's also a common practice in supermarkets to not return the exact change, so it seems logical to give customer a choice - cancel or finalize with smaller/no change.

### Q: Should the vending machine system handle multiple transactions simultaneously, or can it be designed with the assumption that it processes one transaction at a time?

**Assumption:** For simplicity, vending machine handles a single transaction at a time. However, machine uses `Stock` and `MonetaryInventory` to handle products and change respectively. It will be enough to subclass them and adjust them to be thread safe.

### Q: Should reloading the machine with change or products be possible during an active transaction (e.g., between product selection and product dispensing)? Or can I assume reloading will only happen during a dedicated "maintenance" mode, with no active transactions?
**Assumption:** For simplicity again, vending machine can be reloaded with products or change only during a "maintenance" mode. Just like before, `Stock` and `MonetaryInventory` classes can be adjusted to achieve no down time during a reload.

## Worth noting

- Machine sells only one product at a time
- Coins' value is represented by integers to avoid floating-point inaccuracy, i.e. £1 = 100, 50p = 50



## Setup
```pip install -r requirements.txt```


## Core library
A vending machine is a great example of a finite state machine. Considering the fact this project would be just a base for a more complex system, using [transitions](https://github.com/pytransitions/transitions/) seemed like a perfect idea. It has continuous support and lots of features that may be very useful in further development. On top of that it enforces well organized structure to the code of the machine, making a development of new features a real pleasure.

## Diagram
To regenerate a diagram you will have to install [Graphviz](https://graphviz.org/download/)

Then:

    pip install graphviz pygraphviz # only one of them is required
    python src/diagram_generator.py

## How does it work?

![Machine diagram](https://raw.github.com/Bezduszny/vending-machine/main/vending_machine_diagram.png)


## Basic initialization

Our machine will need some products along with some information about them like their price. Let's do that:


```python
from vending_machine.products import Product, ProductInfo, Stock

stock = Stock(
    catalogue={
        1: ProductInfo(name="Soda", price=210),  # £2.10
        2: ProductInfo(name="Water", price=100),  # £1
        3: ProductInfo(name="Ice tea", price=195),  # £1.95
    },
    products=(
        Product(id=1),
        Product(id=1),
        Product(id=2),
        Product(id=3),
    ),
)
```

Let's get some change:

```python
from vending_machine.payments import Denomination, MonetaryInventory

monetary_inventory = MonetaryInventory(
    {
        Denomination(100): 5, # 5 x £1
        Denomination(10): 3, # 3 x 10p
    }
)
```

Now we can create a machine and fill it with products and change:

```python
from vending_machine import DeliverySystem, VendingMachine

machine = VendingMachine(
    stock,
    monetary_inventory,
    DeliverySystem(),
)

```

Our machine is now operational! We can buy something:

```python
machine.start()
machine.select(product_id=1)
machine.insert(denomination=100)
machine.insert(denomination=100)
machine.insert(denomination=10)
machine.checkout()
# Product(id=1) has been dispatched!
# No change returned
```

or reload some products and/or change:

```python
machine.start_maintenance()
machine.add_products(products=(Product(2), Product(2), Product(3)))
machine.reload_change(supply={Denomination(50): 10})
machine.end_maintenance()
```

Refer to [VendingMachine tests](https://github.com/Bezduszny/vending-machine/blob/main/src/tests/test_vending_machine.py) for more examples.