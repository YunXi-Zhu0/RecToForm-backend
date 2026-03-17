import httpx
import re
from src.core.config import DEEPSEEK_SSPU_MODEL


class DeepSeekSSPULLM:
    def __init__(self):
        self.base_url = DEEPSEEK_SSPU_MODEL["BASE_URL"]
        self.model = DEEPSEEK_SSPU_MODEL["MODEL_NAME"]
        self.temperature = DEEPSEEK_SSPU_MODEL["TEMPERATURE"]
        self.max_tokens = DEEPSEEK_SSPU_MODEL["MAX_TOKENS"]
        self.prompt = None

    async def invoke(self, user_prompt: str) -> str:
        payload = {
            "model": self.model,
            "prompt": user_prompt,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }

        headers = {"Content-Type": "application/json"}
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(self.base_url, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()

        content = data["choices"][0]["text"]
        cleaned_content = re.sub(r'.*?</think>', '', content, flags=re.DOTALL).strip()

        return cleaned_content

if __name__ == "__main__":
    import asyncio
    async def main():
        llm = DeepSeekSSPULLM()
        user_prompt = "请介绍一下你自己"
        response = await llm.invoke(user_prompt)
        print(response)

    asyncio.run(main())
