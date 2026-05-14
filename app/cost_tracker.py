from app.models import MODEL_MAP


def calculate_cost(model_id: str, input_tokens: int, output_tokens: int) -> float:
    cfg = MODEL_MAP.get(model_id)
    if not cfg:
        return 0.0
    return (input_tokens * cfg["input_cost_per_M"] + output_tokens * cfg["output_cost_per_M"]) / 1_000_000


def format_cost(cost_usd: float) -> str:
    if cost_usd == 0.0:
        return "$0.00"
    if cost_usd < 0.0001:
        return "<$0.0001"
    return f"${cost_usd:.4f}"
