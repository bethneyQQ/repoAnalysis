from engine import node
from pathlib import Path
import fnmatch

def files_to_prompt_node():
    """Files-to-Prompt Node - 本地轻量级 RAG 工具

    将文件内容格式化为适合 LLM 的提示文本，支持多种格式化选项。

    参数：
        - format: 'xml' (默认) 或 'markdown' - 输出格式
        - include_line_numbers: bool - 是否包含行号 (默认 False)
        - cxml: bool - 使用紧凑的 XML 格式 (默认 False)
        - include_stats: bool - 包含文件统计信息 (默认 True)
        - output_key: str - 输出到 context 的键名 (默认 'formatted_prompt')
        - files_source: str - 从 context 中获取文件列表的键名 (默认 'files')
    """

    def prep(ctx, params):
        # 从 context 中获取文件列表
        files_key = params.get("files_source", "files")
        files = ctx.get(files_key, [])

        return {
            "files": files,
            "format": params.get("format", "xml"),
            "include_line_numbers": params.get("include_line_numbers", False),
            "cxml": params.get("cxml", False),
            "include_stats": params.get("include_stats", True),
            "output_key": params.get("output_key", "formatted_prompt")
        }

    def exec(prep_result, params):
        files = prep_result["files"]
        format_type = prep_result["format"]
        include_line_numbers = prep_result["include_line_numbers"]
        cxml = prep_result["cxml"]
        include_stats = prep_result["include_stats"]

        if not files:
            return {
                "success": False,
                "error": "No files provided",
                "formatted_text": ""
            }

        formatted_parts = []
        total_lines = 0
        total_chars = 0
        files_processed = 0

        # 处理每个文件
        for file_path in files:
            try:
                path = Path(file_path)
                if not path.exists():
                    continue

                with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()

                # 统计信息
                lines = content.split('\n')
                total_lines += len(lines)
                total_chars += len(content)
                files_processed += 1

                # 格式化文件内容
                if format_type == "xml":
                    formatted_parts.append(_format_xml(
                        path, content, include_line_numbers, cxml
                    ))
                else:  # markdown
                    formatted_parts.append(_format_markdown(
                        path, content, include_line_numbers
                    ))

            except Exception as e:
                # 跳过无法读取的文件
                continue

        # 组合所有部分
        if format_type == "xml":
            header = "<documents>\n" if not cxml else "<documents>"
            footer = "\n</documents>" if not cxml else "</documents>"
            separator = "\n\n" if not cxml else ""
        else:
            header = "# Code Repository Content\n\n"
            footer = ""
            separator = "\n\n---\n\n"

        formatted_text = header + separator.join(formatted_parts) + footer

        # 添加统计信息
        stats = {
            "files_processed": files_processed,
            "total_lines": total_lines,
            "total_chars": total_chars,
            "avg_lines_per_file": total_lines // files_processed if files_processed > 0 else 0
        }

        if include_stats:
            stats_text = _format_stats(stats, format_type)
            formatted_text = stats_text + "\n\n" + formatted_text

        return {
            "success": True,
            "formatted_text": formatted_text,
            "stats": stats
        }

    def post(ctx, prep_result, exec_result, params):
        if exec_result["success"]:
            output_key = prep_result["output_key"]
            ctx[output_key] = exec_result["formatted_text"]
            ctx["files_to_prompt_stats"] = exec_result["stats"]
            return "formatted"
        else:
            ctx["files_to_prompt_error"] = exec_result["error"]
            return "failed"

    return node(prep=prep, exec=exec, post=post)


def _format_xml(path: Path, content: str, include_line_numbers: bool, cxml: bool):
    """格式化为 XML 格式"""
    file_name = path.name
    file_path = str(path)

    if cxml:
        # 紧凑格式
        result = f'<document path="{file_path}">'
        if include_line_numbers:
            lines = content.split('\n')
            numbered = '\n'.join(f'{i+1:4d} {line}' for i, line in enumerate(lines))
            result += numbered
        else:
            result += content
        result += '</document>'
    else:
        # 标准格式
        result = f'<document>\n<path>{file_path}</path>\n<content>\n'
        if include_line_numbers:
            lines = content.split('\n')
            numbered = '\n'.join(f'{i+1:4d} {line}' for i, line in enumerate(lines))
            result += numbered
        else:
            result += content
        result += '\n</content>\n</document>'

    return result


def _format_markdown(path: Path, content: str, include_line_numbers: bool):
    """格式化为 Markdown 格式"""
    file_path = str(path)
    extension = path.suffix.lstrip('.')

    result = f'## File: `{file_path}`\n\n'

    if include_line_numbers:
        lines = content.split('\n')
        numbered = '\n'.join(f'{i+1:4d} {line}' for i, line in enumerate(lines))
        result += f'```{extension}\n{numbered}\n```'
    else:
        result += f'```{extension}\n{content}\n```'

    return result


def _format_stats(stats: dict, format_type: str):
    """格式化统计信息"""
    if format_type == "xml":
        return f"""<stats>
  <files_processed>{stats['files_processed']}</files_processed>
  <total_lines>{stats['total_lines']}</total_lines>
  <total_chars>{stats['total_chars']}</total_chars>
  <avg_lines_per_file>{stats['avg_lines_per_file']}</avg_lines_per_file>
</stats>"""
    else:
        return f"""## Statistics

- **Files Processed**: {stats['files_processed']}
- **Total Lines**: {stats['total_lines']}
- **Total Characters**: {stats['total_chars']}
- **Average Lines per File**: {stats['avg_lines_per_file']}"""
