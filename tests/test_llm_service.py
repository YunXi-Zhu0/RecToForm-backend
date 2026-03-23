import unittest

from src.services.llm import LLMService, PromptContext, PromptFieldSet
from src.services.llm.json_parser import extract_json_object


class LLMServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.context = PromptContext(
            template_id="template_a",
            template_name="模板A",
            file_type="PDF",
            page_indices=[1, 2],
            fields=PromptFieldSet(
                default_fields=["发票号码", "开票日期"],
                optional_fields=["价税合计"],
            ),
            extra_instructions=["金额字段保留票面原始格式。"],
        )
        self.service = LLMService()

    def test_build_prompts_contains_target_fields(self) -> None:
        prompts = self.service.build_prompts(self.context)

        self.assertIn("模板A", prompts["user_prompt"])
        self.assertIn("发票号码", prompts["system_prompt"])
        self.assertIn("价税合计", prompts["user_prompt"])
        self.assertIn("图片页码顺序：[1, 2]", prompts["user_prompt"])

    def test_parse_json_result_strips_fenced_wrapper_and_filters_fields(self) -> None:
        raw_text = """```json
{
  "发票号码": "123456",
  "开票日期": "2025-08-08",
  "价税合计": "150.00",
  "备注": "忽略"
}
```"""
        result = self.service.parse_json_result(raw_text=raw_text, context=self.context)

        self.assertEqual(
            result.data,
            {
                "发票号码": "123456",
                "开票日期": "2025-08-08",
                "价税合计": "150.00",
            },
        )
        self.assertEqual(result.extra_fields, ["备注"])
        self.assertEqual(result.missing_fields, [])

    def test_parse_json_result_fills_missing_fields(self) -> None:
        raw_text = '{"发票号码":"123456"}'
        result = self.service.parse_json_result(raw_text=raw_text, context=self.context)

        self.assertEqual(result.data["发票号码"], "123456")
        self.assertEqual(result.data["开票日期"], "")
        self.assertEqual(result.data["价税合计"], "")
        self.assertEqual(result.missing_fields, ["开票日期", "价税合计"])

    def test_extract_json_object_finds_embedded_object(self) -> None:
        raw_text = '以下是结果：{"发票号码":"123456"} 请查收'
        self.assertEqual(extract_json_object(raw_text), '{"发票号码":"123456"}')


if __name__ == "__main__":
    unittest.main()
