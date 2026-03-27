import json
from typing import Dict

from src.services.llm.models import PromptContext


def build_system_prompt(context: PromptContext) -> str:
    standard_fields_json = json.dumps(context.standard_fields, ensure_ascii=False)
    return (
        "你是发票字段提取助手。你的任务是根据提供的发票图片提取标准字段，并严格输出 JSON。\n\n"
        "要求：\n"
        "1. 只能根据输入图片提取字段，禁止猜测或补造不存在的信息。\n"
        "2. 若字段无法确认，返回空值。\n"
        "3. 多张图片或多页 PDF 时，请综合全部图片内容后输出一个 JSON 结果。\n"
        "4. 输出字段名必须与系统给定的固定中文键列表完全一致。\n"
        "5. 最终只输出合法 JSON，不要输出解释、分析过程或额外文本。\n"
        "6. 缺失字段统一返回 `%s`。\n"
        "7. 必须输出完整标准 JSON，即使字段缺失也要保留对应 key。\n"
        "8. 本次仅允许输出以下字段：%s。"
        % (context.missing_value, standard_fields_json)
    )


def build_user_prompt(context: PromptContext) -> str:
    standard_fields_json = json.dumps(context.standard_fields, ensure_ascii=False)
    recommended_output_fields_json = json.dumps(
        context.recommended_output_fields,
        ensure_ascii=False,
    )
    page_indices_json = json.dumps(context.page_indices, ensure_ascii=False)
    json_example = context.json_example or _build_json_example(context)
    json_example_text = json.dumps(json_example, ensure_ascii=False, indent=2)

    sections = [
        "当前任务：请结合上传的全部发票图片提取发票信息，并输出完整标准 JSON。",
        "当前模板：%s（ID: %s）" % (context.template_name, context.template_id),
        "标准 JSON 版本：%s" % context.schema_version,
        "固定输出字段：%s" % standard_fields_json,
        "模板默认导出表头：%s" % recommended_output_fields_json,
        "文件类型：%s" % context.file_type,
        "图片页码顺序：%s" % page_indices_json,
        "输出 JSON 示例：\n%s" % json_example_text,
        (
            "图像分析规则：\n"
            "1. 按页码顺序综合分析全部图片。\n"
            "2. 尽量保留票面原始表达。\n"
            "3. 若字段无法确认，请返回缺失值，不要猜测。\n"
            "4. 所有固定中文键都必须出现在最终 JSON 中。"
        ),
    ]

    if context.extra_instructions:
        sections.append("附加要求：\n%s" % "\n".join(context.extra_instructions))

    return "\n\n".join(sections)


def _build_json_example(context: PromptContext) -> Dict[str, str]:
    return {field_name: context.missing_value for field_name in context.standard_fields}
