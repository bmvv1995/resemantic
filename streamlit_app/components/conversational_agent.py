"""
Simple conversational agent using OpenAI.
"""

from openai import OpenAI
import os


class ConversationalAgent:
    """Simple chat agent."""

    def __init__(self, api_key: str = None):
        self.client = OpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))
        self.model = "gpt-4o-mini"

        self.system_prompt = """You are a helpful, friendly AI assistant engaged in natural conversation.

Keep responses:
- Natural and conversational
- Concise but informative
- Helpful and engaging

You are part of ReSemantic, a system that extracts semantic knowledge from conversations.
"""

    def chat(self, user_message: str, conversation_history: list) -> str:
        """Generate response to user message."""

        # Build messages for API
        messages = [
            {"role": "system", "content": self.system_prompt}
        ]

        # Add conversation history (last 10 messages)
        for msg in conversation_history[-10:]:
            messages.append({
                "role": msg['role'],
                "content": msg['content']
            })

        # Add current message
        messages.append({
            "role": "user",
            "content": user_message
        })

        # Call API
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=500
            )

            return response.choices[0].message.content

        except Exception as e:
            return f"Error: {str(e)}"
