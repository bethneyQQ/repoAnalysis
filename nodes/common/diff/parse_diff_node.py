from engine import node
from pathlib import Path
import re

def parse_diff_node():
    """Parse git diff into structured format

    Context Input:
        - diff_content: Raw diff content
        - project_root: Project root directory

    Context Output:
        - parsed_diff: Dict of file changes
        - file_changes: List of changed files
        - code_context: Dict[file_path, List[code_lines]]
    """

    def prep(ctx, params):
        diff_content = ctx.get("diff_content", "")
        project_root = Path(ctx.get("project_root", ".")).resolve()

        return {
            "diff_content": diff_content,
            "project_root": project_root
        }

    def exec(prep_result, params):
        diff_content = prep_result["diff_content"]
        project_root = prep_result["project_root"]

        if not diff_content.strip():
            return {
                "success": True,
                "parsed_diff": {},
                "file_changes": [],
                "code_context": {},
                "warning": "No diff content to parse"
            }

        try:
            parsed_diff = _parse_unified_diff(diff_content)
            file_changes = list(parsed_diff.keys())

            # Extract code context from changed files
            code_context = {}
            for file_path in file_changes:
                full_path = project_root / file_path
                if full_path.exists() and full_path.is_file():
                    try:
                        with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                            code_context[file_path] = f.readlines()
                    except:
                        # If file can't be read, use changed lines from diff
                        code_context[file_path] = parsed_diff[file_path].get("added_lines", [])
                else:
                    # For new files, use added lines from diff
                    code_context[file_path] = parsed_diff[file_path].get("added_lines", [])

            return {
                "success": True,
                "parsed_diff": parsed_diff,
                "file_changes": file_changes,
                "code_context": code_context,
                "total_files": len(file_changes)
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to parse diff: {str(e)}"
            }

    def post(ctx, prep_result, exec_result, params):
        if exec_result["success"]:
            ctx["parsed_diff"] = exec_result["parsed_diff"]
            ctx["file_changes"] = exec_result["file_changes"]
            ctx["code_context"] = exec_result["code_context"]
            ctx["total_files_changed"] = exec_result.get("total_files", 0)

            if "warning" in exec_result:
                ctx["parse_warning"] = exec_result["warning"]

            return "diff_parsed"
        else:
            ctx["parse_error"] = exec_result["error"]
            return "parse_failed"

    return node(prep=prep, exec=exec, post=post)


def _parse_unified_diff(diff_content):
    """Parse unified diff format into structured data"""
    parsed = {}
    current_file = None
    current_changes = None

    lines = diff_content.split('\n')
    i = 0

    while i < len(lines):
        line = lines[i]

        # File header: diff --git a/file b/file
        if line.startswith('diff --git'):
            # Extract file path
            match = re.search(r'b/(.+)$', line)
            if match:
                current_file = match.group(1)
                current_changes = {
                    "added_lines": [],
                    "removed_lines": [],
                    "added_line_numbers": [],
                    "removed_line_numbers": [],
                    "hunks": []
                }
                parsed[current_file] = current_changes

        # New file
        elif line.startswith('new file mode'):
            if current_changes is not None:
                current_changes["change_type"] = "added"

        # Deleted file
        elif line.startswith('deleted file mode'):
            if current_changes is not None:
                current_changes["change_type"] = "deleted"

        # Hunk header: @@ -start,count +start,count @@
        elif line.startswith('@@'):
            match = re.search(r'@@\s+-(\d+)(?:,(\d+))?\s+\+(\d+)(?:,(\d+))?\s+@@', line)
            if match and current_changes is not None:
                old_start = int(match.group(1))
                new_start = int(match.group(3))

                current_hunk = {
                    "old_start": old_start,
                    "new_start": new_start,
                    "changes": []
                }
                current_changes["hunks"].append(current_hunk)

        # Added line
        elif line.startswith('+') and not line.startswith('+++'):
            if current_changes is not None:
                content = line[1:]  # Remove '+'
                current_changes["added_lines"].append(content)

                # Estimate line number from hunks
                if current_changes["hunks"]:
                    last_hunk = current_changes["hunks"][-1]
                    line_num = last_hunk["new_start"] + len(current_changes["added_lines"]) - 1
                    current_changes["added_line_numbers"].append(line_num)

        # Removed line
        elif line.startswith('-') and not line.startswith('---'):
            if current_changes is not None:
                content = line[1:]  # Remove '-'
                current_changes["removed_lines"].append(content)

                # Estimate line number from hunks
                if current_changes["hunks"]:
                    last_hunk = current_changes["hunks"][-1]
                    line_num = last_hunk["old_start"] + len(current_changes["removed_lines"]) - 1
                    current_changes["removed_line_numbers"].append(line_num)

        i += 1

    # Set default change_type for files that were modified
    for file_path, changes in parsed.items():
        if "change_type" not in changes:
            changes["change_type"] = "modified"

    return parsed
