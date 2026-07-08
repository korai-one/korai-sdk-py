"""Quickstart for the Korai Platform SDK.

Demonstrates the three load-bearing parts of an app on Korai:

1. ``client.llm.complete`` — a chat completion against Korai Cloud.
2. ``client.audit.log`` + ``client.audit.verify_chain`` — an append-only
   signed audit log of the operation.
3. ``client.tools.register`` + ``client.tools.invoke`` — a typed
   business tool you'd hand to the LLM.

Run with::

    KORAI_BASE_URL=https://cloud.korai.one \
    KORAI_API_KEY=sk-korai-... \
    python examples/quickstart.py
"""

from __future__ import annotations

import asyncio
import os
import sys

from pydantic import BaseModel, Field

from korai import KoraiClient
from korai.llm import Message
from korai.tools import Tool, ToolInput, ToolOutput


# --- 1. Define a tool ----------------------------------------------------


class TaxInput(ToolInput):
    revenue_chf: float = Field(description="Annual revenue in CHF")
    canton: str = Field(default="GE", description="Swiss canton code")


class TaxOutput(ToolOutput):
    federal_tax_chf: float


class FederalTaxTool(Tool[TaxInput, TaxOutput]):
    name = "compute_federal_tax"
    description = "Compute Swiss federal tax (illustrative, not authoritative)."
    input_model = TaxInput
    output_model = TaxOutput

    async def execute(self, input: TaxInput) -> TaxOutput:  # noqa: A002
        # Toy formula — replace with the real Swiss federal table.
        rate = 0.115 if input.revenue_chf > 100_000 else 0.07
        tax = round(input.revenue_chf * rate, 2)
        return TaxOutput(
            federal_tax_chf=tax,
            calculation_steps=[
                f"revenue={input.revenue_chf:.0f} CHF",
                f"rate={rate:.3%}",
                f"tax = revenue * rate = {tax:.2f} CHF",
            ],
            confidence=0.85,
        )


class DemoSummary(BaseModel):
    """Tiny structured printout for the example."""

    completion: str
    tax_chf: float
    audit_entries: int
    chain_valid: bool


# --- 2. Glue together ----------------------------------------------------


async def main() -> None:
    api_key = os.getenv("KORAI_API_KEY", "sk-korai-demo-key")
    base_url = os.getenv("KORAI_BASE_URL", "https://cloud.korai.one")

    async with KoraiClient(
        api_key=api_key,
        base_url=base_url,
        audit_secret=b"demo-audit-secret-please-change",
        organization_id="org-demo",
    ) as client:
        # Register the tool — schemas are now ready to be sent to any LLM.
        client.tools.register(FederalTaxTool())

        # Fire one completion. We catch network errors so the example
        # works without a live orchestrator (just illustrating the SDK).
        try:
            result = await client.llm.complete(
                messages=[
                    Message(
                        role="user",
                        content="En une phrase, quelle est la mission de Korai ?",
                    )
                ],
                model="claude-opus-4-7",
                max_tokens=64,
            )
            completion = result.content
            print(f"LLM said: {completion}")
            await client.audit.log(
                "llm.completion",
                payload={"latency_ms": result.latency_ms, "model": result.model},
            )
        except Exception as exc:  # noqa: BLE001
            print(f"(skipping live LLM call: {exc})")
            completion = "<no live cloud>"

        # Run the local tool — pure-Python, no network.
        tax_out = await client.tools.invoke(
            "compute_federal_tax", {"revenue_chf": 120_000, "canton": "GE"}
        )
        assert isinstance(tax_out, TaxOutput)
        await client.audit.log(
            "tool.invoked",
            resource_type="tool",
            resource_id="compute_federal_tax",
            payload={
                "input": {"revenue_chf": 120_000},
                "output": {"federal_tax_chf": tax_out.federal_tax_chf},
            },
        )

        # Verify the audit chain.
        verification = await client.audit.verify_chain()
        entries = await client.audit.list_entries()

        summary = DemoSummary(
            completion=completion,
            tax_chf=tax_out.federal_tax_chf,
            audit_entries=len(entries),
            chain_valid=verification.is_valid,
        )
        print(summary.model_dump_json(indent=2))


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        sys.exit(130)
