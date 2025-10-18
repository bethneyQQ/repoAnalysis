from engine import node
from pathlib import Path
import subprocess

def get_git_diff_node():
    """Get git diff or read diff from file

    Parameters:
        - git_ref: Git reference to diff against (e.g., 'HEAD', 'main', 'HEAD~1')
        - diff_file: Path to diff/patch file (alternative to git_ref)
        - include_staged: Include staged changes (default: False)

    Context Input:
        - project_root: Project root directory

    Context Output:
        - diff_content: Raw diff content
        - diff_source: 'git' or 'file'
    """

    def prep(ctx, params):
        project_root = Path(ctx.get("project_root", ".")).resolve()
        git_ref = params.get("git_ref")
        diff_file = params.get("diff_file")
        include_staged = params.get("include_staged", False)

        return {
            "project_root": project_root,
            "git_ref": git_ref,
            "diff_file": diff_file,
            "include_staged": include_staged
        }

    def exec(prep_result, params):
        project_root = prep_result["project_root"]
        git_ref = prep_result["git_ref"]
        diff_file = prep_result["diff_file"]
        include_staged = prep_result["include_staged"]

        try:
            # Option 1: Read from file
            if diff_file:
                diff_path = Path(diff_file)
                if not diff_path.is_absolute():
                    diff_path = project_root / diff_file

                if not diff_path.exists():
                    return {
                        "success": False,
                        "error": f"Diff file not found: {diff_path}"
                    }

                with open(diff_path, 'r', encoding='utf-8') as f:
                    diff_content = f.read()

                return {
                    "success": True,
                    "diff_content": diff_content,
                    "diff_source": "file",
                    "source_path": str(diff_path)
                }

            # Option 2: Get from git
            elif git_ref is not None:
                cmd = ['git', 'diff']

                if include_staged:
                    cmd.append('--cached')

                if git_ref:
                    cmd.append(git_ref)

                result = subprocess.run(
                    cmd,
                    cwd=str(project_root),
                    capture_output=True,
                    text=True
                )

                if result.returncode != 0:
                    return {
                        "success": False,
                        "error": f"Git diff failed: {result.stderr}"
                    }

                diff_content = result.stdout

                if not diff_content.strip():
                    return {
                        "success": True,
                        "diff_content": "",
                        "diff_source": "git",
                        "warning": "No changes detected in git diff"
                    }

                return {
                    "success": True,
                    "diff_content": diff_content,
                    "diff_source": "git",
                    "git_ref": git_ref or "working directory"
                }

            # Option 3: Default to working directory diff
            else:
                result = subprocess.run(
                    ['git', 'diff'],
                    cwd=str(project_root),
                    capture_output=True,
                    text=True
                )

                if result.returncode != 0:
                    return {
                        "success": False,
                        "error": f"Git diff failed: {result.stderr}"
                    }

                diff_content = result.stdout

                return {
                    "success": True,
                    "diff_content": diff_content,
                    "diff_source": "git",
                    "git_ref": "working directory"
                }

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to get diff: {str(e)}"
            }

    def post(ctx, prep_result, exec_result, params):
        if exec_result["success"]:
            ctx["diff_content"] = exec_result["diff_content"]
            ctx["diff_source"] = exec_result["diff_source"]

            if "source_path" in exec_result:
                ctx["diff_source_path"] = exec_result["source_path"]
            if "git_ref" in exec_result:
                ctx["diff_git_ref"] = exec_result["git_ref"]
            if "warning" in exec_result:
                ctx["diff_warning"] = exec_result["warning"]

            return "diff_retrieved"
        else:
            ctx["diff_error"] = exec_result["error"]
            return "diff_failed"

    return node(prep=prep, exec=exec, post=post)
