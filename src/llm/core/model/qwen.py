from src.core.config import QWEN3_MAX_MODEL
from openai import AsyncOpenAI

class Qwen3MaxLLM:
    def __init__(self):
        self.client = AsyncOpenAI(
            api_key=QWEN3_MAX_MODEL["API_KEY"],
            base_url=QWEN3_MAX_MODEL["BASE_URL"]
        )

    async def invoke(self, user_prompt: str, system_prompt: str = None) -> str:
        completion = await self.client.chat.completions.create(
            model=QWEN3_MAX_MODEL["MODEL_NAME"],
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ]
        )
        return completion.choices[0].message.content


if __name__ == "__main__":
    import asyncio

    async def main():
        llm = Qwen3MaxLLM()
        system_prompt = "你是一个有帮助的助手。"
        user_prompt = "请介绍一下你自己。"
        response = await llm.invoke(user_prompt=user_prompt, system_prompt=system_prompt)
        print(response)
    asyncio.run(main())