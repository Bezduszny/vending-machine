from vending_machine.products import Product, ProductInfo, Stock


def test_product_equality():
    product1 = Product(id=1)
    product2 = Product(id=1)
    product3 = Product(id=2)

    assert product1 == product2
    assert product1 != product3


def test_add_products_logs_warning_for_missing_info(caplog):
    catalogue = {1: ProductInfo(name="Product 1", price=100)}
    stock = Stock(catalogue)

    product_without_info = Product(id=2)
    stock.add_products(product_without_info)

    assert "Missing product information for product id: 2" in caplog.text


def test_get_product():
    catalogue = {1: ProductInfo(name="Product 1", price=100)}
    stock = Stock(catalogue)

    product = Product(id=1)
    stock.add_products(product)

    retrieved_product = stock.get_product(product.id)

    assert retrieved_product == product


def test_get_offer():
    catalogue = {
        1: ProductInfo(name="Product 1", price=100),
        2: ProductInfo(name="Product 2", price=200),
    }
    stock = Stock(catalogue)

    product1 = Product(id=1)
    product2 = Product(id=2)

    stock.add_products(product1, product2)

    offers = stock.get_offer()

    assert len(offers) == 2  # Both products should be in stock
    assert offers[1] == catalogue[1]
    assert offers[2] == catalogue[2]


def test_get_offer_empty_stock():
    catalogue = {1: ProductInfo(name="Product 1", price=100)}
    stock = Stock(catalogue)

    offers = stock.get_offer()

    assert len(offers) == 0


def test_update_catalogue():
    initial_catalogue = {
        1: ProductInfo(name="Product 1", price=100),
        2: ProductInfo(name="Product 2", price=200),
    }
    stock = Stock(initial_catalogue)

    product1 = Product(id=1)
    stock.add_products(product1)

    new_catalogue = {
        2: ProductInfo(name="Updated Product 2", price=150),
        3: ProductInfo(name="Product 3", price=300),
    }
    stock.update_catalogue(new_catalogue)

    # Check that stock retained old info for product 1
    assert stock.catalogue[1].name == "Product 1"
    # Check that product 2 was updated
    assert stock.catalogue[2].name == "Updated Product 2"
    # Check that new product 3 is added
    assert stock.catalogue[3].name == "Product 3"
