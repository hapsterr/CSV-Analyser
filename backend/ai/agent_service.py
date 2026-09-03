import os
import json
import logging
from openai import OpenAI

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an AI data analysis agent. You help users analyze their datasets by selecting the appropriate action and explaining results.

CRITICAL RULES:
1. You must ONLY select from the available actions listed below.
2. You must NEVER generate Python, SQL, JavaScript, or any executable code.
3. You must NEVER request raw data, actual values, or real column names.
4. You must NEVER request customer names, product names, or personal information.
5. You must ONLY use the masked placeholder names provided in the schema.
6. If a question cannot be answered by available actions, return the "unsupported" action.

AVAILABLE ACTIONS:
{actions}

AVAILABLE DATASET SCHEMA (use these masked column names):
{schema}

RESPONSE FORMAT:
Return a JSON object with exactly this structure:
{{
    "action": "action_name_or_unsupported",
    "parameters": {{...}},
    "reason": "Brief explanation of your choice"
}}

If the question cannot be answered, use:
{{
    "action": "unsupported",
    "parameters": {{}},
    "reason": "Explanation of why this question cannot be answered"
}}"""

EXPLANATION_PROMPT = """You are an AI data analyst explaining analysis results to a user.

The user asked: {question}

The analysis produced the following result:
{result}

Explain the result clearly and concisely. Use the placeholder names from the result directly. 
Do NOT try to guess or reveal real values. Just explain what the data shows using the placeholders.
Keep your response under 3 sentences.
Do NOT generate code. Do NOT include any formatting other than plain text."""


class AgentService:
    def __init__(self):
        api_key = os.getenv("AI_API_KEY")
        self.model = os.getenv("AI_MODEL", "gpt-4o-mini")
        if api_key:
            self.client = OpenAI(api_key=api_key)
        else:
            self.client = None
            logger.warning("AI_API_KEY not set. AI features will be unavailable.")

    def select_action(self, question: str, schema_text: str, actions_text: str) -> dict:
        if not self.client:
            return {"action": "unsupported", "parameters": {}, "reason": "AI service not configured"}

        system = SYSTEM_PROMPT.format(actions=actions_text, schema=schema_text)

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": question},
            ],
            temperature=0,
            response_format={"type": "json_object"},
        )

        content = response.choices[0].message.content
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            logger.error(f"Failed to parse AI response: {content}")
            return {"action": "unsupported", "parameters": {}, "reason": "Invalid AI response format"}

    def explain_result(self, question: str, result_text: str) -> str:
        if not self.client:
            return "AI service not configured. Please set AI_API_KEY."

        prompt = EXPLANATION_PROMPT.format(question=question, result=result_text)

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
        )

        return response.choices[0].message.content


agent_service = AgentService()
