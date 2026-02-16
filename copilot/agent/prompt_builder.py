import json
from typing import Dict, List


class PromptBuilder:
    def build(self, user_query: str, structured_result: Dict, memory_turns: List[Dict]) -> str:
        memory_text = "\n".join(
            [f"{t['role']}: {t['content']}" for t in memory_turns]
        )

        payload = json.dumps(structured_result, indent=2)

        return f"""
You are CITAGENT FactoryOps Copilot.
Governance rules (mandatory):
1) Use ONLY the provided StructuredResult JSON.
2) Never compute or invent costs, forecasts, or anomaly numbers.
3) Never claim database access.
4) If StructuredResult status is no_data, clearly say data is missing.
5) Keep response concise, professional, and actionable.

Conversation Memory (latest):
{memory_text}

User Query:
{user_query}

StructuredResult JSON:
{payload}

Respond with:
- Direct answer
- Key observations
- Suggested next operational action
""".strip()
