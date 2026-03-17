import asyncio
from src.integrations.llm.core.model.deepseek_sspu import DeepSeekSSPULLM
from src.integrations.llm.core.model.qwen import Qwen3MaxLLM


async def ds():
    llm = DeepSeekSSPULLM()
    prompt = """
    现在你是一名专业的发票审查员, 请根据下面给出的信息, 提取表格中对应的字段及其对应的数据, 以json形式返回
    发票号码：25317000001856634821
    开票日期：2025年08月08日
    <table border=1 style='margin: auto; word-wrap: break-word;'><tr><td rowspan="2">购买方信息</td><td colspan="3">名称:上海第二工业大学</td><td rowspan="2">销售方信息</td><td colspan="3">名称:中国石化销售股份有限公司上海石油分公司</td></tr><tr><td colspan="3">统一社会信用代码/纳税人识别号:12310000425026417R</td><td colspan="3">统一社会信用代码/纳税人识别号:91310000834486035U</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>项目名称</td><td style='text-align: center; word-wrap: break-word;'>规格型号</td><td style='text-align: center; word-wrap: break-word;'>单位</td><td style='text-align: center; word-wrap: break-word;'>数量</td><td style='text-align: center; word-wrap: break-word;'>单价</td><td style='text-align: center; word-wrap: break-word;'>金额</td><td style='text-align: center; word-wrap: break-word;'>税率/征收率</td><td style='text-align: center; word-wrap: break-word;'>税额</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>*汽油*92号车用汽油(VIB 92号)</td><td style='text-align: center; word-wrap: break-word;'>升</td><td style='text-align: center; word-wrap: break-word;'>20.77562327</td><td style='text-align: center; word-wrap: break-word;'></td><td style='text-align: center; word-wrap: break-word;'>6.38921867</td><td style='text-align: center; word-wrap: break-word;'>132.74</td><td style='text-align: center; word-wrap: break-word;'>13%</td><td style='text-align: center; word-wrap: break-word;'>17.26</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>合    计</td><td style='text-align: center; word-wrap: break-word;'></td><td style='text-align: center; word-wrap: break-word;'></td><td style='text-align: center; word-wrap: break-word;'></td><td style='text-align: center; word-wrap: break-word;'></td><td style='text-align: center; word-wrap: break-word;'>¥132.74</td><td style='text-align: center; word-wrap: break-word;'></td><td style='text-align: center; word-wrap: break-word;'>¥17.26</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>价税合计（大写）</td><td colspan="7">ⓧ壹佰伍拾圆整    （小写）¥150.00</td></tr><tr><td colspan="8">收款人:中国石化; 复核人:中国石化;</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>备注</td><td colspan="7"></td></tr></table>
    开票人: 中国石化
    """

    response = await llm.invoke(prompt)
    print(response)

async def qwen():
    llm = Qwen3MaxLLM()
    system_prompt = "现在你是一名专业的发票审查员"
    user_prompt = """
    现在你是一名专业的发票审查员, 请根据下面给出的信息, 提取表格中对应的字段及其对应的数据, 以json形式返回
    提取字段为"合计金额", "发票号码"
    发票号码：25317000001856634821
    开票日期：2025年08月08日
    <table border=1 style='margin: auto; word-wrap: break-word;'><tr><td rowspan="2">购买方信息</td><td colspan="3">名称:上海第二工业大学</td><td rowspan="2">销售方信息</td><td colspan="3">名称:中国石化销售股份有限公司上海石油分公司</td></tr><tr><td colspan="3">统一社会信用代码/纳税人识别号:12310000425026417R</td><td colspan="3">统一社会信用代码/纳税人识别号:91310000834486035U</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>项目名称</td><td style='text-align: center; word-wrap: break-word;'>规格型号</td><td style='text-align: center; word-wrap: break-word;'>单位</td><td style='text-align: center; word-wrap: break-word;'>数量</td><td style='text-align: center; word-wrap: break-word;'>单价</td><td style='text-align: center; word-wrap: break-word;'>金额</td><td style='text-align: center; word-wrap: break-word;'>税率/征收率</td><td style='text-align: center; word-wrap: break-word;'>税额</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>*汽油*92号车用汽油(VIB 92号)</td><td style='text-align: center; word-wrap: break-word;'>升</td><td style='text-align: center; word-wrap: break-word;'>20.77562327</td><td style='text-align: center; word-wrap: break-word;'></td><td style='text-align: center; word-wrap: break-word;'>6.38921867</td><td style='text-align: center; word-wrap: break-word;'>132.74</td><td style='text-align: center; word-wrap: break-word;'>13%</td><td style='text-align: center; word-wrap: break-word;'>17.26</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>合    计</td><td style='text-align: center; word-wrap: break-word;'></td><td style='text-align: center; word-wrap: break-word;'></td><td style='text-align: center; word-wrap: break-word;'></td><td style='text-align: center; word-wrap: break-word;'></td><td style='text-align: center; word-wrap: break-word;'>¥132.74</td><td style='text-align: center; word-wrap: break-word;'></td><td style='text-align: center; word-wrap: break-word;'>¥17.26</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>价税合计（大写）</td><td colspan="7">ⓧ壹佰伍拾圆整    （小写）¥150.00</td></tr><tr><td colspan="8">收款人:中国石化; 复核人:中国石化;</td></tr><tr><td style='text-align: center; word-wrap: break-word;'>备注</td><td colspan="7"></td></tr></table>
    开票人: 中国石化
    """

    response = await llm.invoke(user_prompt=user_prompt, system_prompt=system_prompt)
    print(response)


asyncio.run(ds())