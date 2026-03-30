import json
from typing import Dict

from src.services.llm.models import PromptContext


def build_system_prompt(context: PromptContext) -> str:
    standard_fields_json = json.dumps(context.standard_fields, ensure_ascii=False)
    return (
        "你是发票字段提取助手。你的任务是根据提供的发票图片提取标准字段。\n\n"
        "要求：\n"
        "1. 只能根据输入图片提取字段，禁止猜测或补造不存在的信息。\n"
        "2. 若字段无法确认，返回空值。\n"
        "3. 输出字段名必须与系统给定的固定中文键列表完全一致。\n"
        "4. 最终只输出合法 JSON，不要输出解释、分析过程或额外文本。\n"
        "5. 缺失字段统一返回 `%s`。\n"
        "6. 必须输出完整标准 JSON，即使字段缺失也要保留对应 key。\n"
        "7. 本次仅允许输出以下字段：%s。"
        % (context.missing_value, standard_fields_json)
    )


def build_user_prompt(context: PromptContext) -> str:
    sections = [
        "当前任务：请结合上传的发票图片提取发票信息，并输出完整标准 JSON。\n"
        "返回json示例如下\n"
        """
            {
                "发票号码": "25317000002264951341",
                "发票代码": "",
                "发票金额": "123.45"
            }
            \n
        """
        "注意: 其中'发票代码'为值缺失的字段, 其余的是有值的字段"
    ]

    if context.extra_instructions:
        sections.append("附加要求：\n%s" % "\n".join(context.extra_instructions))

    return "\n\n".join(sections)


def _build_json_example(context: PromptContext) -> Dict[str, str]:
    return {field_name: context.missing_value for field_name in context.standard_fields}
