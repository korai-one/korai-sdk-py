from enum import Enum


class FleetVariantBackend(str, Enum):
    LLAMACPP = "llamacpp"
    MLX = "mlx"
    VLLM = "vllm"

    def __str__(self) -> str:
        return str(self.value)
