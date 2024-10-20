import logging
from collections import defaultdict
from dataclasses import dataclass
from queue import Queue
from typing import Dict, Iterable

ProductID = int


@dataclass
class Product:
    id: ProductID

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Product):
            return self.id == other.id
        return False


@dataclass
class ProductInfo:
    name: str
    price: int


class Stock:
    products: Dict[ProductID, Queue[Product]]
    catalogue: Dict[ProductID, ProductInfo]

    def __init__(
        self, catalogue: Dict[ProductID, ProductInfo], products: Iterable[Product] = []
    ) -> None:
        self.catalogue = catalogue
        self.products = defaultdict(lambda: Queue())
        self.add_products(*products)

    def add_products(self, *products: Product):
        for product in products:
            self.products[product.id].put(product)

            if product.id not in self.catalogue:
                logging.warning(
                    f"Missing product information for product id: {product.id} This product is now in stock, but can't be sold until catalogue is updated."
                )

    def get_product(self, product_id: ProductID) -> Product:
        return self.products[product_id].get_nowait()

    def get_price_of(self, product_id: ProductID) -> int:
        info = self.catalogue.get(product_id, None)

        if info is not None:
            return info.price

        raise RuntimeError(
            f"No price found for product with id={product_id}, it's not in the catalogue!"
        )

    def get_offer(self) -> Dict[ProductID, ProductInfo]:
        """Returns information about products that are in stock."""
        return {
            product_id: info
            for product_id, info in self.catalogue.items()
            if not self.products[product_id].empty()
        }

    def update_catalogue(self, new_catalogue: Dict[ProductID, ProductInfo]):
        """
        Updates the catalogue with new product information,
        but also keeps some of the old products information,
        if they're not in the new catalogue, but are still in stock.
        """
        self.catalogue = self.get_offer() | new_catalogue
