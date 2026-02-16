import logging
from dataclasses import dataclass
from typing import Dict, Optional

from agent.intents import IntentClassifier
from agent.memory import ConversationMemory
from agent.ollama_client import OllamaClient
from agent.prompt_builder import PromptBuilder
from agent.router import ToolRouter


LOGGER = logging.getLogger(__name__)


@dataclass
class CopilotAgent:
    classifier: IntentClassifier
    router: ToolRouter
    memory: ConversationMemory
    prompt_builder: PromptBuilder
    ollama: OllamaClient

    def ask(
        self,
        user_query: str,
        machine_id: str,
        start_ts,
        end_ts,
        granularity: str,
        compare_machine: Optional[str] = None,
        forecast_days: int = 90,
        whatif_inputs: Optional[Dict] = None,
    ) -> Dict:
        intent = self.classifier.classify(user_query)
        structured_result = self.router.route(
            intent=intent,
            user_query=user_query,
            machine_id=machine_id,
            start_ts=start_ts,
            end_ts=end_ts,
            granularity=granularity,
            compare_machine=compare_machine,
            forecast_days=forecast_days,
            whatif_inputs=whatif_inputs,
        )

        result_body = structured_result.get("result", {})
        if result_body.get("status") == "no_data":
            answer = result_body.get("message", "Data unavailable for this request.")
            self.memory.add_turn("user", user_query)
            self.memory.add_turn("assistant", answer)
            return {
                "intent": intent.value,
                "structured_result": structured_result,
                "answer": answer,
            }

        prompt = self.prompt_builder.build(
            user_query=user_query,
            structured_result=structured_result,
            memory_turns=self.memory.list_turns(),
        )

        try:
            answer = self.ollama.generate(prompt)
        except Exception as exc:
            LOGGER.exception("Ollama generation failed: %s", exc)
            answer = (
                "Unable to get a response from local Ollama right now. "
                "Structured result is available for inspection."
            )

        self.memory.add_turn("user", user_query)
        self.memory.add_turn("assistant", answer)

        return {
            "intent": intent.value,
            "structured_result": structured_result,
            "answer": answer,
        }
