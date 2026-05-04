import random

from producer.generators.base import BaseGenerator
from producer.models import StreamEvent

_STOREFRONTS = [f"store-{s}" for s in ["us", "uk", "de", "fr", "ca", "au"]]


class EcommerceGenerator(BaseGenerator):
    """Simulates storefront telemetry: orders, revenue, funnel, and session metrics."""

    domain = "ecommerce"

    def __init__(self, source_id: str | None = None) -> None:
        self._source_id = source_id or random.choice(_STOREFRONTS)

    def generate(self) -> StreamEvent:
        orders = random.randint(0, 50)
        revenue = round(orders * random.uniform(12.0, 250.0), 2)
        sessions = random.randint(50, 5000)
        add_to_cart = random.randint(0, sessions)
        checkouts = random.randint(0, add_to_cart)

        return StreamEvent(
            source_id=self._source_id,
            domain=self.domain,
            metrics={
                "orders_count": float(orders),
                "revenue_usd": revenue,
                "avg_order_value_usd": round(revenue / orders, 2) if orders else 0.0,
                "sessions": float(sessions),
                "add_to_cart_count": float(add_to_cart),
                "checkout_count": float(checkouts),
                "cart_abandonment_rate": round(
                    1.0 - (checkouts / add_to_cart) if add_to_cart else 0.0, 4
                ),
                "page_views": float(random.randint(sessions, sessions * 8)),
                "bounce_rate": round(random.uniform(0.2, 0.8), 4),
                "conversion_rate": round(orders / sessions if sessions else 0.0, 4),
            },
            metadata={"currency": "USD", "storefront": self._source_id},
        )
