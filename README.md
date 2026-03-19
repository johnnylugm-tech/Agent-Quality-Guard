# Agent Quality Guard

> AI 程式碼品質把關系統

---

## 📦 版本資訊

- **版本**: 1.0.1
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
| **API Server** | REST API 服務 |
| **Docker** | 容器化支援 |
| **CI/CD** | GitHub Actions / GitLab / Jenkins |
| **OWASP Top 10** | 2023 最新規則 |

---

## 🛡️ 偵測規則 (50+)

### OWASP Top 10 2023

| 類別 | 說明 |
|------|------|
| A01 | Broken Access Control |
| A02 | Cryptographic Failures |
| A03 | Injection |
| A04 | Insecure Design |
| A05 | Security Misconfiguration |
| A06 | Vulnerable Components |
| A07 | Auth Failures |
| A08 | Software Integrity |
| A09 | Logging Failures |
| A10 | SSRF |

### 經典規則

| 規則 | 說明 |
|------|------|
| API Key | API Key 硬編碼 |
| Password | 密碼硬編碼 |
| AWS Key | AWS Access Key |
| GitHub Token | GitHub Token |
| SQL Injection | SQL 注入 |
| Command Injection | 命令注入 |
| Eval Usage | 不安全的 eval() |
| Hardcoded IP | IP 位址硬編碼 |

---

## 🚀 安裝

```bash
# 方式 1: Clone
git clone https://github.com/johnnylugm-tech/Agent-Quality-Guard.git
cd Agent-Quality-Guard
pip install -r requirements.txt

# 方式 2: Docker
docker build -t agent-quality-guard .
```

---

## 💻 使用

```bash
# 基本掃描
python src/main.py --file your_code.py

# LLM 審查
python src/main.py --file your_code.py --llm

# GitHub Actions
# 見 .github/workflows/scan.yml

# API Server
python -c "from src.api_server import run_server; run_server()"
```
| Missing docstring | 缺少文檔字串 |
| Nested loops | 巢狀迴圈 |

---

## 📊 評分維度

| 維度 | 權重 |
|------|:----:|
| 正確性 | 30% |
| 安全性 | 25% |
| 可維護性 | 20% |
| 效能 | 15% |
| 測試覆蓋 | 10% |

---

## 🚀 快速開始

```bash
# 克隆專案
git clone https://github.com/johnnylugm-tech/agent-quality-guard.git
cd agent-quality-guard/src

# 基本分析
python main.py --file your_code.py

# LLM 審查
python main.py --file code.py --llm

# Git Hook
python main.py hook install

# 報告生成
python main.py --file code.py --report --report-format html
```

---

## 📁 專案結構

```
agent-quality-guard/
├── README.md
├── LICENSE
├── requirements.txt
└── src/
    ├── main.py          # CLI 入口
    ├── analyzer.py      # AST 靜態分析
    ├── scorer.py        # 評分引擎
    ├── llm_judge.py    # LLM 審查
    ├── git_hook.py     # Git Hook
    ├── reporter.py     # 報告生成
    └── test_analyzer.py
```

---

## 📝 更新日誌

| 版本 | 日期 | 說明 |
|------|------|------|
| v1.0.0 | 2026-03-19 | 首次發布 |

---

**Made with 🚀 for AI Builders**
