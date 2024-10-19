from vending_machine.payments import (
    ChangeConfiguration,
    Denomination,
    MonetaryInventory,
    find_optimal_change,
)


def test_exact_change():
    owed_amount = 210
    cash_inventory = MonetaryInventory({Denomination(100): 2, Denomination(10): 1})

    optimal_config = find_optimal_change(owed_amount, cash_inventory)

    assert optimal_config == ChangeConfiguration(
        configuration={Denomination(100): 2, Denomination(10): 1}, owed=0
    )


def test_exact_change2():
    owed_amount = 130
    cash_inventory = MonetaryInventory(
        {
            Denomination(100): 3,
            Denomination(50): 3,
            Denomination(20): 3,
            Denomination(10): 3,
        }
    )

    optimal_config = find_optimal_change(owed_amount, cash_inventory)

    assert optimal_config == ChangeConfiguration(
        configuration={Denomination(100): 1, Denomination(20): 1, Denomination(10): 1},
        owed=0,
    )


def test_exact_change_large_denomination():
    """This test checks if the larger denomination is favoured over higher quantity of lower denominations."""
    owed_amount = 200
    cash_inventory = MonetaryInventory({Denomination(200): 1, Denomination(100): 2})

    optimal_config = find_optimal_change(owed_amount, cash_inventory)

    assert optimal_config == ChangeConfiguration(
        configuration={Denomination(200): 1}, owed=0
    )


def test_no_available_change():
    owed_amount = 50
    cash_inventory = MonetaryInventory({Denomination(100): 2, Denomination(200): 1})

    optimal_config = find_optimal_change(owed_amount, cash_inventory)

    assert optimal_config == ChangeConfiguration(configuration={}, owed=50)


def test_partial_change():
    owed_amount = 150
    cash_inventory = MonetaryInventory(
        {Denomination(100): 1, Denomination(20): 1, Denomination(10): 2}
    )

    optimal_config = find_optimal_change(owed_amount, cash_inventory)

    assert optimal_config == ChangeConfiguration(
        configuration={Denomination(100): 1, Denomination(20): 1, Denomination(10): 2},
        owed=10,
    )


def test_partial_change2():
    owed_amount = 150
    cash_inventory = MonetaryInventory({Denomination(100): 2, Denomination(10): 1})

    optimal_config = find_optimal_change(owed_amount, cash_inventory)

    assert optimal_config == ChangeConfiguration(
        configuration={Denomination(100): 1, Denomination(10): 1}, owed=40
    )


def test_backtracking():
    owed_amount = 80
    cash_inventory = MonetaryInventory({Denomination(50): 3, Denomination(20): 4})

    optimal_config = find_optimal_change(owed_amount, cash_inventory)

    assert optimal_config == ChangeConfiguration(
        configuration={Denomination(20): 4},
        owed=0,
    )


def test_large_quantities_and_large_owed_amount():
    owed_amount = 7885
    cash_inventory = MonetaryInventory(
        initial_inventory={
            Denomination(2000): 100,
            Denomination(1000): 100,
            Denomination(500): 100,
            Denomination(200): 100,
            Denomination(100): 100,
            Denomination(50): 100,
            Denomination(20): 100,
            Denomination(10): 100,
            Denomination(5): 100,
        },
        supported_denominantions=[
            Denomination(2000),
            Denomination(1000),
            Denomination(500),
            Denomination(200),
            Denomination(100),
            Denomination(50),
            Denomination(20),
            Denomination(10),
            Denomination(5),
            Denomination(2),
            Denomination(1),
        ],
    )

    optimal_config = find_optimal_change(owed_amount, cash_inventory)

    assert optimal_config == ChangeConfiguration(
        configuration={
            Denomination(2000): 3,
            Denomination(1000): 1,
            Denomination(500): 1,
            Denomination(200): 1,
            Denomination(100): 1,
            Denomination(50): 1,
            Denomination(20): 1,
            Denomination(10): 1,
            Denomination(5): 1,
        },
        owed=0,
    )
