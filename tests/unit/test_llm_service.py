import unittest

from src.services.llm import LLMService, PromptContext
from src.services.llm.json_parser import extract_json_object


class LLMServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.context = PromptContext(
            template_id="template_a",
            template_name="模板A",
            file_type="PDF",
            page_indices=[1, 2],
            standard_fields=["发票号码", "开票日期", "价税合计(大写)"],
            schema_version="v1",
            recommended_output_fields=["发票号码", "开票日期"],
            extra_instructions=["金额字段保留票面原始格式。"],
        )
        self.service = LLMService()

    def test_build_prompts_contains_standard_fields(self) -> None:
        prompts = self.service.build_prompts(self.context)

        self.assertIn("模板A", prompts["user_prompt"])
        self.assertIn("发票号码", prompts["system_prompt"])
        self.assertIn("价税合计(大写)", prompts["user_prompt"])
        self.assertIn("图片页码顺序：[1, 2]", prompts["user_prompt"])
        self.assertNotIn("可选字段", prompts["user_prompt"])

    def test_parse_json_result_strips_fenced_wrapper_and_filters_fields(self) -> None:
        raw_text = """```json
{
  "发票号码": "123456",
  "开票日期": "2025-08-08",
  "价税合计(大写)": "壹佰伍拾元整",
  "备注": "忽略"
}
```"""
        result = self.service.parse_json_result(raw_text=raw_text, context=self.context)

        self.assertEqual(
            result.data,
            {
                "发票号码": "123456",
                "开票日期": "2025-08-08",
                "价税合计(大写)": "壹佰伍拾元整",
            },
        )
        self.assertEqual(result.extra_fields, ["备注"])
        self.assertEqual(result.missing_fields, [])

    def test_parse_json_result_fills_missing_fields(self) -> None:
        raw_text = '{"发票号码":"123456"}'
        result = self.service.parse_json_result(raw_text=raw_text, context=self.context)

        self.assertEqual(result.data["发票号码"], "123456")
        self.assertEqual(result.data["开票日期"], "")
        self.assertEqual(result.data["价税合计(大写)"], "")
        self.assertEqual(result.missing_fields, ["开票日期", "价税合计(大写)"])

    def test_extract_json_object_finds_embedded_object(self) -> None:
        raw_text = '以下是结果：{"发票号码":"123456"} 请查收'
        self.assertEqual(extract_json_object(raw_text), '{"发票号码":"123456"}')

    def test_extract_json_object_supports_multiline_invoice_json(self) -> None:
        raw_text = """{
    "发票代码": "",
    "发票号码": "253170000003168913915",
    "开票日期": "2025年12月03日",
    "购买方名称": "上海第二工业大学",
    "购买方纳税人识别号": "",
    "购买方地址电话": "",
    "购买方开户行及账号": "",
    "货物或应税劳务、服务名称": "*汽油*92号车用汽油(VIB-92号",
    "规格型号": "",
    "单位": "升",
    "数量": "32.11678832",
    "单价": "6.06193864",
    "金额": "194.69",
    "税率": "13%",
    "税额": "25.31",
    "合计": "220.00",
    "价税合计(大写)": "贰佰贰拾圆整",
    "销售方名称": "中国石化销售股份有限公司上海石油分公司",
    "销售方纳税人识别号": "91310000834486035U",
    "销售方地址电话": "",
    "销售方开户行及账号": "",
    "收款人": "中国石化",
    "复核": "中国石化",
    "开票人": "中国石化",
    "销售方": "",
    "备注": "收款人:中国石化;复核人:中国石化;"
}"""
        self.assertEqual(extract_json_object(raw_text), raw_text)

    def test_extract_json_object_skips_invalid_braces_before_json(self) -> None:
        raw_text = '说明中的占位符 {invoice} 无需处理，最终结果：{"发票号码":"123456"}'
        self.assertEqual(extract_json_object(raw_text), '{"发票号码":"123456"}')


if __name__ == "__main__":
    unittest.main()
