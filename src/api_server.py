#!/usr/bin/env python3
"""
Agent Quality Guard - API Server

簡單的 API 伺服器，用於遠程掃描
"""

import json
from flask import Flask, request, jsonify
from pathlib import Path
import sys
import os

# 添加當前目錄到路徑
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from src.analyzer import CodeAnalyzer
    from src.scorer import ScoreEngine
    from src.llm_judge import LLmJudge
except ImportError:
    # 備用導入（直接運行時）
    from analyzer import CodeAnalyzer
    from scorer import ScoreEngine
    from llm_judge import LLmJudge


app = Flask(__name__)


@app.route("/health", methods=["GET"])
def health():
    """健康檢查"""
    return jsonify({"status": "healthy"})


@app.route("/analyze", methods=["POST"])
def analyze():
    """分析代碼"""
    data = request.json or {}
    
    code = data.get("code")
    file_path = data.get("file")
    use_llm = data.get("llm", False)
    
    if not code and not file_path:
        return jsonify({"error": "code or file is required"}), 400
    
    # 讀取代碼
    if file_path:
        try:
            with open(file_path, "r") as f:
                code = f.read()
        except Exception as e:
            return jsonify({"error": str(e)}), 400
    
    # 分析
    analyzer = CodeAnalyzer(code)
    issues = analyzer.analyze()
    
    # 評分
    scorer = ScoreEngine()
    score = scorer.calculate_score(issues)
    
    result = {
        "score": score.total,
        "grade": score.grade,
        "issues": [i.to_dict() for i in issues],
        "breakdown": score.breakdown
    }
    
    # LLM Judge (可選)
    if use_llm:
        llm = LLmJudge()
        try:
            llm_result = llm.judge(code, issues)
            result["llm_judge"] = llm_result
        except Exception as e:
            result["llm_error"] = str(e)
    
    return jsonify(result)


@app.route("/analyze/batch", methods=["POST"])
def analyze_batch():
    """批量分析"""
    data = request.json or {}
    files = data.get("files", [])
    
    results = []
    for file_path in files:
        try:
            with open(file_path, "r") as f:
                code = f.read()
            
            analyzer = CodeAnalyzer(code)
            issues = analyzer.analyze()
            
            scorer = ScoreEngine()
            score = scorer.calculate_score(issues)
            
            results.append({
                "file": file_path,
                "score": score.total,
                "grade": score.grade,
                "issues_count": len(issues)
            })
        except Exception as e:
            results.append({
                "file": file_path,
                "error": str(e)
            })
    
    return jsonify({"results": results})


def run_server(host="0.0.0.0", port=8080):
    """啟動服務器"""
    app.run(host=host, port=port, debug=False)


if __name__ == "__main__":
    run_server()
