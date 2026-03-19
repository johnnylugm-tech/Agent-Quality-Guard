# Agent Quality Guard - 開發計劃

> 基於 2-Agent Playbook v3.0

---

## 一、任務定義

### 1.1 目標
建立一個 AI Agent 程式碼品質把關系統，自動審查 AI 產出的程式碼，給出品質評分與問題列表。

### 1.2 核心功能
| 功能 | 說明 |
|------|------|
| Code Review | 自動審查 AI 產出 |
| 品質評分 | 0-100 分 + 等級 |
| 問題分類 | 邏輯/安全/效能/風格 |
| 修復建議 | 給出具體修改建議 |
| Git Hook | CI/CD 整合 |
| 歷史追蹤 | 品質趨勢分析 |

---

## 二、版本規劃

### 2.1 MVP (2週) ✅ 完成
- [x] 基礎靜態分析 (AST Parser)
- [x] 命令列工具 (CLI)
- [x] 基礎評分系統

### 2.2 v1.0 (4週) ✅ 完成
- [x] LLM Judge 整合 (GPT-4/Claude)
- [x] 詳細報告生成
- [x] 問題分類優化

### 2.3 v1.5 (6週) ✅ 完成 (v2.0 的一部分)
- [x] Git Hook 整合 (pre-commit)
- [x] 報告系統 (Markdown/HTML)
- [x] 趨勢追蹤

### 2.4 v2.0 (8週) ✅ 完成
- [x] LLM Judge 整合 - `llm_judge.py`
  - OpenAI API 支援
  - Anthropic API 支援
  - 錯誤處理 (L1-L4 分類)
- [x] Git Hook 整合 - `git_hook.py`
  - pre-commit 鉤子安裝
  - 自動審查功能
  - staged files 檢查
- [x] 報告增強 - `reporter.py`
  - Markdown 報告格式
  - HTML 報告格式
  - 趨勢追蹤與分析
- [x] CLI 增強 - `main.py`
  - 向後兼容
  - 子命令支援 (analyze, hook, trends)
  - 新功能整合

---

## 三、團隊分工

### Agent A - 前端/工具
- CLI 開發 ✅
- Git Hook 整合 ✅
- 報告生成 ✅

### Agent B - 後端/分析
- 靜態分析引擎 ✅
- LLM Judge 整合 ✅
- 數據處理 ✅

### 人類 - 決策者
- 需求確認 ✅
- 品質把關 ✅
- 最終審批 ✅

---

## 四、設計模式

### 4.1 主要模式
- **ReAct**: 推理 → 行動 → 觀察 → 輸出
- **Reflection**: 執行 → 自審 → 修正 → 輸出
- **Pipeline**: 輸入 → 解析 → 分析 → 評分 → 報告

### 4.2 錯誤處理
| 層級 | 類型 | 處理 |
|------|------|------|
| L1 | 輸入錯誤 | 立即返回 |
| L2 | 分析失敗 | 重試 |
| L3 | 執行錯誤 | 降級/上報 |
| L4 | 系統錯誤 | 熔斷 |

---

## 五、驗證清單

### 開發前
- [x] 需求確認
- [x] 架構設計
- [x] 技術選型

### 開發中
- [x] 單元測試
- [x] 整合測試
- [x] 日誌記錄

### 發布前
- [x] E2E 測試
- [x] 效能測試
- [x] 安全測試

---

## 六、使用方式

### 基本分析
```bash
python main.py --file path/to/code.py
echo "code" | python main.py --stdin
```

### LLM 審查 (需要 API key)
```bash
python main.py --file code.py --llm
```

### 報告生成
```bash
python main.py --file code.py --report --report-format html
```

### Git Hook
```bash
python main.py hook install
python main.py hook run
```

### 趨勢分析
```bash
python main.py trends --days 30
```

---

## 七、相關檔案

- `/workspace/team/2-agent-playbook-v3.md` - 開發規範
- `/workspace/agent-quality-guard/` - 專案目錄
  - `src/main.py` - CLI 入口
  - `src/analyzer.py` - 靜態分析引擎
  - `src/scorer.py` - 評分系統
  - `src/llm_judge.py` - LLM 審查 (v2.0)
  - `src/git_hook.py` - Git Hook 整合 (v2.0)
  - `src/reporter.py` - 報告生成 (v2.0)

---

*版本：2.0*
*建立日期：2026-03-19*
*更新日：2026-03-19*