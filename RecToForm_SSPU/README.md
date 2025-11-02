# RecToForm_SSPU_Assetlmport 发票信息提取与模板自动导入
作者：Yunxi_Zhu（2025年4月）  kkghrsbsb（2025年11月）


---

## 一、程序功能说明

这个程序能自动读取发票（PDF 或 OFD 文件），用 AI 提取其中的关键信息，例如：
- 发票代码  
- 发票号码  
- 发票金额（价税合计小写）

然后它能自动生成 Excel 文件，或者直接把这些数据填进学院的资产模板里。

***！使用模板导入，95%以上的信息都能填上哦！***

程序分两种模式：

| 模式编号 | 功能说明                               | 结果文件 |
|-----------|------------------------------------|-----------|
| 1 | 普通发票信息提取                           | 生成一个发票清单（发票信息.xlsx） |
| 2 | 大创低值材料资产入库模板自动导入 (网站填信息申请信息栏有导入按键) | 自动填写模板（模板_自动填写版.xlsx） |

---

## 二、环境准备

### 1) 安装 Python
在命令行输入：
```bash
python --version
```
没装的话去官方安装：https://www.python.org/downloads/
（安装时勾选 Add Python to PATH）。

### 2) 安装uv (Python 包管理器)
```bash
pip install uv
```
### 3) 初始化依赖
进入项目目录（按你的真实路径调整）：
```bash
cd RecToForm_SSPU
uv sync
```
`uv sync` 会自动安装所需依赖（如 requests、openpyxl、pdfplumber、easyofd 等）。

## 三、准备文件与目录
确保目录文件中有这些：
```bash
RecToForm_SSPU/
├── 发票/                 # 你要识别的发票放这里（.pdf 或 .ofd）
├── 模板.xlsx             # 仅在模式 2 需要，必须是 .xlsx
└── RecToForm_SSPU_AssetImport.py
```
> 注意：模板必须是 xlsx，xls 不支持。旧模板请用 WPS/Excel 另存为 .xlsx。

## 四、怎么运行
目录结构示例：
```bash
# uv方式启动
uv run RecToForm_SSPU_AssetImport.py

# 使用.exe直接启动即可
```
屏幕会出现选择：
```md
请选择功能模式：
1. 普通发票信息提取 制作者：Yunxi_Zhu
2. 大创低值材料资产入库模板自动导入 制作者：kkghrsbsb
输入数字选择模式：
```
输入 1 → 生成 发票信息.xlsx

输入 2 → 生成 模板_自动填写版.xlsx

过程中可能还会询问：
```bash
请确保你已创建“发票”文件夹并放入发票[y/n]：
```
输入 y 回车即可继续。

##  五、运行示例
```bash
uv run RecToForm_SSPU_AssetImport.py
输入数字选择模式：2
请确保你已创建“发票”文件夹并放入发票[y/n]：y
文件1 digital_25117000001364279590 已分析完成
文件2 digital_25317000002666281495 已分析完成
模板已填写完成：模板_自动填写版.xlsx
```

## 七、api信息
程序调用了 **DeepSeek Chat API** 来识别发票。
如需更换 Key，请修改代码中的： \
`api_key = "sk-xxxxxxxxxxxxxxxx"` \
接口地址： \
`https://api.deepseek.com/chat/completions`

## 八、附注
- 运行时请保持网络畅通；
- Excel 输出默认覆盖同名文件；
- 如果想清理旧数据，只需删除输出文件重新运行即可。

