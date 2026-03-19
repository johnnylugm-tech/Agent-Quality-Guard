# Agent Quality Guard v3.0

> AI 程式碼品質把關系統

---

## 📦 版本資訊

- **版本**: 3.1.0
- **發布日期**: 2026-03-19
- **作者**: OpenClaw AI Agent

---

## ✨ 功能特色

| 功能 | 說明 |
|------|------|
| 靜態分析 | AST 語法樹分析 |
| 品質評分 | 0-100 分 + 等級 (A-F) |
| 問題分類 | 正確性/安全性/可維護性/效能/測試覆蓋 |
| LLM Judge | 整合 OpenAI/Claude 深度審查 |
| Git Hook | pre-commit 整合 |
| 報告生成 | Markdown/HTML 格式 |
| 趨勢追蹤 | 歷史分數趨勢分析 |

---

## 📊 評分維度

| 維度 | 權重 | 檢查項目 |
|------|:----:|----------|
| 正確性 | 30% | 語法、邏輯、邊界條件 |
| 安全性 | 25% | 漏洞、認證、加密 |
| 可維護性 | 20% | 結構、命名、註解 |
| 效能 | 15% | 複雜度、資源使用 |
| 測試覆蓋 | 10% | 單元測試、整合測試 |

---

## 🛠️ 安裝

```bash
# 克隆或下載專案
cd agent-quality-guard/src

# 確保 Python 3.8+
python --version
```

---

## 📖 使用方式

### 基本分析

```bash
# 直接輸入程式碼
python main.py --code 'def hello(): print("Hello")'

# 從檔案分析
python main.py --file path/to/code.py

# JSON 輸出
python main.py --file code.py --json

# 從 stdin 讀取
cat code.py | python main.py --stdin
```

### LLM Judge (需要 API Key)

```bash
# 設定環境變數
export OPENAI_API_KEY="your-key"
export ANTHROPIC_API_KEY="your-key"

# 啟用 LLM 審查
python main.py --file code.py --llm
```

### Git Hook

```bash
# 安裝 hook
python main.py hook install

# 卸載 hook
python main.py hook uninstall

# 執行 hook
python main.py hook run
```

### 報告生成

```bash
# Markdown 報告
python main.py --file code.py --report

# HTML 報告
python main.py --file code.py --report --report-format html
```

### 趨勢分析

```bash
# 顯示趨勢
python main.py trends --days 30
```

---

## 📁 檔案結構

```
agent-quality-guard/
├── PLAN.md              # 開發計劃
├── src/
│   ├── __init__.py      # 套件初始化
│   ├── analyzer.py      # AST 靜態分析器
│   ├── scorer.py        # 評分引擎
│   ├── main.py          # CLI 入口
│   ├── git_hook.py      # Git Hook 整合
│   ├── llm_judge.py     # LLM Judge
│   ├── reporter.py      # 報告生成器
│   └── test_analyzer.py # 測試
```

---

## 🛡️ 錯誤處理

遵循 L1-L4 分類：

| 等級 | 類型 | 處理方式 |
|------|------|----------|
| L1 | 輸入錯誤 | 立即返回錯誤訊息 |
| L2 | 工具錯誤 | 自動重試 (最多3次) |
| L3 | 執行錯誤 | 降級處理並上報 |
| L4 | 系統錯誤 | 熔斷保護 |

---

## 🧪 測試

```bash
cd src
python -m pytest test_analyzer.py -v
```

---

## 📝 License

MIT License

---

## 🤝 聯繫

如有問題，請聯繫 OpenClaw 團隊。
