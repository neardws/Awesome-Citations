# 文件结构整理方案

## 当前问题
- 根目录下有太多文件（50+个文件）
- 文档、脚本、测试、数据混杂在一起
- 难以找到需要的文件

## 建议的新文件结构

```
Awesome-Citations/
├── README.md                          # 项目说明
├── LICENSE                            # 许可证
├── requirements.txt                   # 依赖列表
├── config.json                        # 默认配置文件
├── .gitignore                         # Git忽略规则
│
├── docs/                              # 📚 文档目录
│   ├── WORKFLOW_GUIDE.md             # Workflow使用指南
│   ├── USAGE_GUIDE.md                # 通用使用指南
│   ├── CLAUDE.md                     # Claude Code项目说明
│   ├── COMPLETION_SUMMARY.md         # 补全功能总结
│   ├── IMPLEMENTATION_SUMMARY.md     # 实施总结
│   ├── WORKFLOW_IMPLEMENTATION_SUMMARY.md  # Workflow实施总结
│   ├── OPTIMIZATION_SUMMARY.md       # 优化总结
│   ├── OPTIMIZATION_RESULTS.md       # 优化结果
│   ├── IEEE_FAILURE_ANALYSIS.md      # IEEE失败分析
│   ├── IEEE失败原因说明.md            # IEEE失败说明（中文）
│   ├── TEST_SUMMARY.md               # 测试总结
│   ├── TEST_REPORT.md                # 测试报告
│   ├── TESTING_COMPLETE.md           # 测试完成报告
│   └── REAL_RUN_TEST_SUMMARY.md      # 真实运行测试总结
│
├── scripts/                           # 🔧 主要脚本（用户使用）
│   ├── workflow_complete.py          # ⭐ 完整workflow（推荐）
│   ├── complete_bibtex.py            # BibTeX补全
│   ├── format_bibtex.py              # BibTeX格式化
│   ├── sort_bibtex.py                # BibTeX排序
│   ├── analyze_bibtex.py             # BibTeX分析
│   ├── generate_pdf.py               # PDF生成
│   ├── enhanced_complete.py          # 增强版补全（高级）
│   └── utilities.py                  # 工具函数
│
├── research/                          # 🔬 研究和实验脚本
│   └── ieee_api_research.py          # IEEE API研究
│
├── data/                              # 💾 数据文件
│   ├── failed_dois.json              # 失败的DOI记录
│   ├── doi_corrections.json          # DOI修正数据库
│   └── journal_abbr.json             # 期刊缩写映射
│
├── templates/                         # 📄 LaTeX模板
│   ├── ieee_template.tex
│   ├── acm_template.tex
│   ├── apa_template.tex
│   └── gb7714_template.tex
│
├── utils/                             # 🛠 工具模块
│   ├── __init__.py
│   ├── change_logger.py
│   ├── arxiv_detector.py
│   ├── multi_source_merger.py
│   └── title_formatter.py
│
├── tests/                             # ✅ 测试文件
│   ├── __init__.py
│   ├── test_*.py                     # 测试脚本
│   ├── pytest.ini                    # pytest配置
│   └── test_run.log                  # 测试日志
│
├── examples/                          # 📖 示例文件
│   ├── sample_input.bib              # 示例输入
│   ├── sample_config.json            # 示例配置
│   └── README.md                     # 示例说明
│
└── output/                            # 📁 输出文件（不提交到git）
    ├── *.bib                         # 处理后的BibTeX
    ├── *_changes.md                  # 修改日志
    └── *.pdf                         # 生成的PDF

# 已删除/移动的文件
- .cache/                             → 保持不变（缓存）
- .venv/                              → 保持不变（虚拟环境）
- htmlcov/                            → 保持不变（测试覆盖率）
- __pycache__/                        → 保持不变（Python缓存）
- .coverage                           → 保持不变（覆盖率数据）
```

## 文件移动计划

### 1. 文档文件 → docs/
- WORKFLOW_GUIDE.md
- USAGE_GUIDE.md
- CLAUDE.md
- COMPLETION_SUMMARY.md
- IMPLEMENTATION_SUMMARY.md
- WORKFLOW_IMPLEMENTATION_SUMMARY.md
- OPTIMIZATION_SUMMARY.md
- OPTIMIZATION_RESULTS.md
- IEEE_FAILURE_ANALYSIS.md
- IEEE失败原因说明.md
- TEST_SUMMARY.md
- TEST_REPORT.md
- TESTING_COMPLETE.md
- REAL_RUN_TEST_SUMMARY.md

### 2. 脚本文件 → scripts/
- workflow_complete.py
- complete_bibtex.py
- format_bibtex.py
- sort_bibtex.py
- analyze_bibtex.py
- generate_pdf.py
- enhanced_complete.py
- utilities.py

### 3. 研究文件 → research/
- ieee_api_research.py

### 4. 测试文件 → tests/
- pytest.ini (移动到tests/)
- test_run.log (移动到tests/)

### 5. 示例文件 → examples/
- test_input.bib → examples/sample_input.bib

### 6. 输出文件 → output/
- test_completed_output.bib
- test_changes_log.md
- deduplicated_output.bib
- sorted_output.bib

### 7. 保留在根目录
- README.md
- LICENSE
- requirements.txt
- config.json
- .gitignore
- refs.bib (用户的主文件，可选择移动)

## 执行步骤

1. 创建新目录结构
2. 移动文件到对应目录
3. 更新导入路径
4. 更新.gitignore
5. 测试所有脚本
6. 更新README.md中的路径引用

## 优点

1. ✅ 清晰的目录结构
2. ✅ 文档、脚本、测试分离
3. ✅ 易于查找和维护
4. ✅ 符合Python项目最佳实践
5. ✅ 方便新用户理解项目结构
