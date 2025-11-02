# Workflow Complete - 使用指南

## 概述

`workflow_complete.py` 是一个简化的BibTeX处理工作流脚本，整合了现有的所有核心功能，实现一站式处理。

## 功能特性

该脚本按照以下步骤处理BibTeX文件：

1. **排序和去重** - 按条目ID字母排序并移除重复条目
2. **补全缺失字段** - 从多个数据源获取完整的文献信息（IEEE/ACM/arXiv/CrossRef/Google Scholar）
3. **格式标准化** - 统一标题大小写、作者名格式、期刊名称等
4. **arXiv替换** - 检测arXiv预印本并尝试替换为正式发表版本
5. **生成修改说明** - 创建详细的Markdown格式修改日志
6. **生成PDF** - 使用LaTeX生成IEEE格式的参考文献PDF

## 安装依赖

```bash
# 核心依赖
pip install bibtexparser tabulate requests beautifulsoup4 lxml

# 可选：Google Scholar支持
pip install scholarly

# 可选：IEEE Selenium支持
pip install selenium webdriver-manager

# 或者一次性安装所有依赖
pip install -r requirements.txt
```

## 基本用法

### 最简单的用法

```bash
python3 workflow_complete.py input.bib
```

这将生成：
- `input_completed.bib` - 处理后的BibTeX文件
- `input_completed_changes.md` - 详细修改说明
- `input_completed.pdf` - IEEE格式PDF（如果安装了LaTeX）

### 指定输出文件

```bash
python3 workflow_complete.py refs.bib --output completed.bib
```

生成：
- `completed.bib`
- `completed_changes.md`
- `completed.pdf`

### 使用自定义配置

```bash
python3 workflow_complete.py refs.bib --output completed.bib --config my_config.json
```

## 配置文件

通过 `config.json` 可以自定义行为：

```json
{
  "citation_style": "ieee",           // PDF样式: ieee, acm, apa, gb7714
  "title_format": "titlecase",        // 标题格式: titlecase, sentencecase
  "journal_format": "both",           // 期刊格式: abbreviation, full, both
  "author_format": "first_last",      // 作者格式: first_last, last_first
  "page_format": "double_dash",       // 页码格式: double_dash, single_dash
  "arxiv_handling": "replace_with_published",  // arXiv处理策略
  "request_delay": 1.0,               // API请求延迟（秒）
  "pdf_output": {
    "enabled": true,                  // 是否生成PDF
    "document_title": "参考文献列表 / References"
  },
  "logging": {
    "enabled": true,                  // 是否生成修改日志
    "output_file": "changes_log.md",
    "verbose": true
  }
}
```

## 输出文件说明

### 1. BibTeX文件 (`*.bib`)

处理后的BibTeX文件，包含：
- 已排序的条目（按ID字母顺序）
- 去重后的唯一条目
- 补全的字段信息
- 标准化的格式

### 2. 修改说明 (`*_changes.md`)

详细的Markdown格式修改日志，包含：

- **摘要统计**：处理的条目数、修改数、错误数等
- **修改分类**：按类型分组的修改统计
- **详细修改**：每个条目的具体修改内容

示例内容：
```markdown
## Summary Statistics

- **Total entries processed**: 10
- **Entries modified**: 8
- **Fields added**: 15
- **Titles formatted**: 8
- **Errors encountered**: 0

## Detailed Changes by Entry

### `smith2023deep`

- ➕ **Added field** `volume`: `42`
  - **Source**: IEEE
- 📝 **Formatted title** (titlecase)
  - **Old**: `deep learning for computer vision`
  - **New**: `Deep Learning for Computer Vision`
```

### 3. PDF文件 (`*.pdf`)

IEEE格式的参考文献列表（需要安装LaTeX）。

安装LaTeX：
- **macOS**: `brew install --cask mactex`
- **Ubuntu**: `sudo apt-get install texlive-full`
- **Windows**: 下载安装 MiKTeX 或 TeX Live

## 工作流程详解

### Step 1: 排序和去重

```
原始文件: 3个条目
├─ smith2023
├─ jones2022
└─ smith2023 (重复)

处理后: 2个条目（按ID排序）
├─ jones2022
└─ smith2023
```

### Step 2: 补全缺失字段

对于每个条目：
1. 检查缺失的重要字段（author, title, year, journal等）
2. 从DOI提取并验证
3. 识别出版商（IEEE/ACM/arXiv等）
4. 从对应数据源获取完整信息
5. 合并到原始条目

### Step 3: 格式标准化

- **标题**: 转换为Title Case（每个单词首字母大写）
- **作者**: 统一格式为 "First Last"
- **期刊**: 规范化期刊名称
- **页码**: 统一使用双短横线（--）

### Step 4: arXiv替换

检测arXiv预印本条目（如 `doi: 10.48550/arXiv.*`），尝试通过以下来源查找正式发表版本：
- Semantic Scholar API
- DBLP
- CrossRef

如果找到，更新条目为正式发表版本的信息。

### Step 5: 生成修改说明

自动生成详细的Markdown修改日志，记录所有变更。

### Step 6: 生成PDF

使用LaTeX将BibTeX编译为格式化的PDF参考文献列表。

## 高级功能

### 数据源优先级

脚本使用多层回退策略获取数据：

```
DOI验证 → 出版商API → CrossRef API → Google Scholar
    ↓           ↓              ↓              ↓
  ✓/✗       IEEE/ACM/arXiv   通用API       最后备选
```

### 缓存机制

- 缓存目录: `.cache/`
- 缓存有效期: 30天
- 缓存格式: JSON

已缓存的DOI会显示：`✓ Using cached data (age: 0.5 days)`

### 失败日志

所有失败的DOI获取尝试都会记录到 `data/failed_dois.json`：

```json
{
  "doi": "10.1109/EXAMPLE.2023",
  "entry_id": "smith2023",
  "publisher": "IEEE",
  "error_message": "HTTP 404: Not Found",
  "http_status": 404,
  "timestamp": "2025-11-02 12:00:00"
}
```

### DOI修正数据库

可以通过 `data/doi_corrections.json` 手动修正已知的错误DOI：

```json
{
  "corrections": [
    {
      "original_doi": "10.1109/INVALID",
      "corrected_doi": "10.1109/CORRECT",
      "status": "corrected",
      "reason": "DOI typo in original source"
    }
  ]
}
```

## 常见问题

### Q1: PDF生成失败

**A**: 需要安装LaTeX。如果不需要PDF，可以在 `config.json` 中设置 `pdf_output.enabled: false`。

### Q2: 某些DOI无法获取数据

**A**: 检查 `data/failed_dois.json` 查看详细错误信息。可能原因：
- DOI不存在或格式错误
- 出版商网站限制或临时不可用
- 网络问题

### Q3: Google Scholar被限流

**A**: 增加 `config.json` 中的 `request_delay` 值（建议2.0或更高）。

### Q4: 如何只执行部分步骤？

**A**: 当前版本执行完整workflow。如需单独步骤，可使用独立脚本：
- `sort_bibtex.py` - 仅排序
- `complete_bibtex.py` - 仅补全
- `format_bibtex.py` - 仅格式化

## 命令行参数

```bash
python3 workflow_complete.py -h
```

```
usage: workflow_complete.py [-h] [--output OUTPUT_FILE] [--config CONFIG_FILE]
                            input_file

positional arguments:
  input_file            Input BibTeX file

optional arguments:
  -h, --help            show this help message and exit
  --output OUTPUT_FILE, -o OUTPUT_FILE
                        Output BibTeX file (default: <input>_completed.bib)
  --config CONFIG_FILE, -c CONFIG_FILE
                        Configuration file (default: config.json)
```

## 性能优化

- **并行处理**: 可以在 `config.json` 中启用 `parallel_processing: true`
- **缓存**: 重复处理相同DOI时会使用缓存（0.2秒延迟）
- **速率限制**:
  - 缓存命中: 0.2秒
  - 新API请求: 0.5秒
  - Google Scholar: 2秒

## 完整示例

```bash
# 1. 准备输入文件
cat refs.bib
# @article{smith2023, ...}
# @article{jones2022, ...}

# 2. 运行workflow
python3 workflow_complete.py refs.bib

# 3. 查看输出
ls -l refs_completed*
# refs_completed.bib
# refs_completed_changes.md
# refs_completed.pdf

# 4. 查看修改日志
cat refs_completed_changes.md

# 5. 查看失败记录（如果有）
cat data/failed_dois.json
```

## 与现有脚本对比

| 功能 | workflow_complete.py | enhanced_complete.py |
|------|---------------------|---------------------|
| 代码行数 | ~450行 | ~375行 |
| 排序去重 | ✅ | ❌ |
| 补全字段 | ✅ | ✅ |
| 格式化 | ✅ | ✅ |
| arXiv替换 | ✅ | ✅ |
| 多源合并 | ❌ | ✅ |
| 并行处理 | ❌ | ✅ |
| 命令行参数 | ✅ | ✅ |
| 目标用户 | 简化workflow | 高级用户 |

## 贡献

欢迎提交Issue和Pull Request！

## 许可证

与项目其他部分保持一致。
