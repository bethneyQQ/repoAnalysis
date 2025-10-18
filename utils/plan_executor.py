"""
Plan Executor - 执行 repo_adapt_plan 中的变更步骤
"""

import yaml
import shutil
from pathlib import Path
import re


class PlanExecutor:
    """执行 YAML plan 中的变更操作"""

    def __init__(self, plan_file, repo_path="."):
        self.plan_file = Path(plan_file)
        self.repo_path = Path(repo_path)
        self.plan = self._load_plan()

    def _load_plan(self):
        """从 MD 文件中提取 YAML plan"""
        with open(self.plan_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # 查找 YAML 代码块
        yaml_match = re.search(r'```yaml\s*\nplan:(.*?)\n```', content, re.DOTALL)
        if not yaml_match:
            # 尝试直接查找 plan:
            yaml_match = re.search(r'plan:(.*?)(?=\n\n|\Z)', content, re.DOTALL)

        if not yaml_match:
            raise ValueError("No plan YAML found in file")

        yaml_text = "plan:" + yaml_match.group(1)
        return yaml.safe_load(yaml_text)

    def execute(self, step_id=None, dry_run=False):
        """
        执行 plan 中的步骤

        Args:
            step_id: 执行特定步骤，None 表示执行所有步骤
            dry_run: 只打印操作，不实际执行
        """
        steps = self.plan.get('plan', {}).get('steps', [])

        if step_id:
            steps = [s for s in steps if s.get('id') == step_id]

        results = []
        for step in steps:
            result = self._execute_step(step, dry_run)
            results.append(result)

        return results

    def _execute_step(self, step, dry_run=False):
        """执行单个步骤"""
        step_id = step.get('id', 'unknown')
        title = step.get('title', '')
        changes = step.get('changes', [])

        print(f"\n{'[DRY RUN] ' if dry_run else ''}Executing step {step_id}: {title}")

        executed_changes = []
        for change in changes:
            change_type = change.get('type')
            if change_type == 'move':
                self._execute_move(change, dry_run)
            elif change_type == 'dep_replace':
                self._execute_dep_replace(change, dry_run)
            elif change_type == 'rename':
                self._execute_rename(change, dry_run)
            elif change_type == 'config':
                self._execute_config(change, dry_run)
            else:
                print(f"  Unknown change type: {change_type}")

            executed_changes.append(change)

        return {
            'step_id': step_id,
            'title': title,
            'changes_executed': len(executed_changes),
            'success': True
        }

    def _execute_move(self, change, dry_run=False):
        """执行文件/目录移动"""
        files = change.get('files', [])
        from_path = change.get('from', '')
        to_path = change.get('to', '')

        for file_pattern in files:
            # 简化：直接移动目录
            src = self.repo_path / from_path / file_pattern
            dst = self.repo_path / to_path / file_pattern

            print(f"  MOVE: {src} -> {dst}")

            if not dry_run:
                dst.parent.mkdir(parents=True, exist_ok=True)
                if src.exists():
                    shutil.move(str(src), str(dst))
                else:
                    print(f"    Warning: {src} does not exist")

    def _execute_dep_replace(self, change, dry_run=False):
        """执行依赖替换"""
        files = change.get('files', [])
        from_dep = change.get('from', '')
        to_dep = change.get('to', '')

        for file_path in files:
            full_path = self.repo_path / file_path

            print(f"  DEP_REPLACE in {file_path}: '{from_dep}' -> '{to_dep}'")

            if not dry_run and full_path.exists():
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                # 替换依赖
                new_content = content.replace(from_dep, to_dep)

                with open(full_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)

                print(f"    Replaced {from_dep} with {to_dep}")

    def _execute_rename(self, change, dry_run=False):
        """执行文件重命名"""
        files = change.get('files', {})

        for old_name, new_name in files.items():
            old_path = self.repo_path / old_name
            new_path = self.repo_path / new_name

            print(f"  RENAME: {old_path} -> {new_path}")

            if not dry_run and old_path.exists():
                old_path.rename(new_path)

    def _execute_config(self, change, dry_run=False):
        """执行配置文件修改"""
        file_path = change.get('file', '')
        updates = change.get('updates', {})

        full_path = self.repo_path / file_path

        print(f"  CONFIG update in {file_path}")

        if not dry_run and full_path.exists():
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # 简化：直接追加配置
            with open(full_path, 'a', encoding='utf-8') as f:
                f.write('\n# Added by plan executor\n')
                for key, value in updates.items():
                    f.write(f"{key} = {value}\n")

            print(f"    Updated {len(updates)} config items")


def verify_plan(plan_file, verification_commands):
    """
    验证 plan 执行后的结果

    Args:
        plan_file: plan 文件路径
        verification_commands: 验证命令列表（从 plan 的 verify 中提取）
    """
    import subprocess

    results = []
    for cmd in verification_commands:
        if isinstance(cmd, dict):
            run_cmd = cmd.get('run')
            if run_cmd:
                print(f"\nRunning verification: {run_cmd}")
                try:
                    result = subprocess.run(
                        run_cmd, shell=True, capture_output=True, text=True, timeout=30
                    )
                    success = result.returncode == 0
                    results.append({'command': run_cmd, 'success': success})
                    print(f"  {'✅ PASS' if success else '❌ FAIL'}")
                except Exception as e:
                    print(f"  ❌ Error: {e}")
                    results.append({'command': run_cmd, 'success': False, 'error': str(e)})

    return results
