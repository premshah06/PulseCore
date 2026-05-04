from producer.generators.base import BaseGenerator
from producer.generators.ecommerce import EcommerceGenerator
from producer.generators.infra import InfraGenerator
from producer.generators.iot import IotGenerator

_REGISTRY: dict[str, type[BaseGenerator]] = {
    "infra": InfraGenerator,
    "ecommerce": EcommerceGenerator,
    "iot": IotGenerator,
}


def get_generator(domain: str) -> BaseGenerator:
    cls = _REGISTRY.get(domain)
    if cls is None:
        raise ValueError(f"Unknown domain {domain!r}. Choose from: {list(_REGISTRY)}")
    return cls()


__all__ = ["get_generator", "InfraGenerator", "EcommerceGenerator", "IotGenerator"]
