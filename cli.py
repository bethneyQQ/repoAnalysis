"""
CLI 入口：支持四个场景
- snapshot: 本地快照与回滚
- adapt: 开源项目理解与组织化改造
- regression: 回归检测与质量门禁
- arch-drift: 架构影响与漂移扫描
"""

import click
import json
import hashlib
from pathlib import Path
from scenarios import scenario_1_local_snapshot
from scenarios import scenario_2_repo_adapt
from scenarios import scenario_3_regression
from scenarios import scenario_4_arch_drift


@click.group()
def cli():
    """代码仓库分析工具

    支持四个核心场景：
    1. snapshot - 本地快照与回滚
    2. adapt - 开源项目理解与组织化改造
    3. regression - 回归检测与质量门禁
    4. arch-drift - 架构影响与漂移扫描
    """
    pass


@cli.command()
@click.option('--patterns', multiple=True, default=['**/*.py'], help='文件匹配模式')
@click.option('--model', default='gpt-4', help='LLM 模型')
def snapshot(patterns, model):
    """场景①：创建本地快照

    扫描项目文件，解析代码结构，使用 AI 分析并生成快照
    """
    click.echo("🔍 场景①：本地快照与回滚")
    config = {
        'file_patterns': list(patterns),
        'model': model
    }
    result = scenario_1_local_snapshot.run(config)
    snapshot_id = result.get('snapshot_id')
    if snapshot_id:
        click.echo(f" Snapshot created: {snapshot_id}")
        # 打印部分内容
        response = result.get('llm_response', '')
        if response:
            preview = response[:300] + "..." if len(response) > 300 else response
            click.echo(f"\n 快照预览：\n{preview}\n")
    else:
        click.echo(" 快照已生成（mock LLM 内容），详见 .ai-snapshots/ 目录")


@cli.command(name='snapshot-list')
def snapshot_list():
    """列出所有快照"""
    snapshots_dir = Path(".ai-snapshots")
    if not snapshots_dir.exists():
        click.echo("No snapshots found")
        return

    snapshot_files = sorted(snapshots_dir.glob("snapshot-*.json"), reverse=True)

    if not snapshot_files:
        click.echo("No snapshots found")
        return

    click.echo("📋 Available Snapshots:\n")
    for snap_file in snapshot_files:
        try:
            with open(snap_file, 'r') as f:
                data = json.load(f)
            timestamp = data.get('timestamp', 'unknown')
            file_count = len(data.get('files', {}))
            snapshot_id = snap_file.stem.replace('snapshot-', '')
            click.echo(f"  [{snapshot_id}] {timestamp} - {file_count} files")
        except Exception as e:
            click.echo(f"  [Error] {snap_file.name}: {e}")


@cli.command(name='snapshot-restore')
@click.argument('snapshot_id')
def snapshot_restore(snapshot_id):
    """从快照恢复文件

    示例: python cli.py snapshot-restore 20250101_120000
    """
    snapshot_file = Path(f".ai-snapshots/snapshot-{snapshot_id}.json")

    if not snapshot_file.exists():
        click.echo(f"Snapshot not found: {snapshot_id}")
        click.echo("Run 'python cli.py snapshot-list' to see available snapshots")
        return

    try:
        with open(snapshot_file, 'r') as f:
            snapshot_data = json.load(f)

        files = snapshot_data.get('files', {})
        restored_count = 0
        hash_matches = 0

        click.echo(f"🔄 Restoring from snapshot {snapshot_id}...\n")

        for file_path, file_data in files.items():
            content = file_data.get('content', '')
            expected_hash = file_data.get('hash', '')

            # 写入文件
            full_path = Path(file_path)
            full_path.parent.mkdir(parents=True, exist_ok=True)

            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)

            # 验证哈希
            actual_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()
            if actual_hash == expected_hash:
                hash_matches += 1

            restored_count += 1

        click.echo(f"Restored {restored_count} files")
        click.echo(f"Hash verification: {hash_matches}/{restored_count} files matched")

        if hash_matches == restored_count:
            click.echo("All files restored successfully with matching hashes")
        else:
            click.echo("Some files have hash mismatches")

    except Exception as e:
        click.echo(f"Error restoring snapshot: {e}")


@cli.command()
@click.argument('repo', required=False)
@click.option('--model', default='gpt-4', help='LLM 模型')
def adapt(repo, model):
    """场景②：开源项目理解与组织化改造

    分析开源仓库，按组织规范生成改造计划

    示例：\n
    python cli.py adapt https://github.com/pallets/flask
    """
    if not repo:
        click.echo("需要提供仓库 URL")
        click.echo("示例: python cli.py adapt https://github.com/pallets/flask")
        return

    click.echo(f"场景②：开源项目理解与组织化改造")
    click.echo(f"仓库：{repo}")

    config = {'repo_url': repo, 'model': model}
    result = scenario_2_repo_adapt.run(config)

    if result.get('error'):
        click.echo(f"错误：{result['error']}")
        return

    out = result.get('output_file_path')
    if out:
        click.echo(f"改造计划已保存：{out}")
        # 打印关键信息
        if 'llm_response' in result:
            response = result['llm_response']
            if 'plan:' in response:
                plan_start = response.find('plan:')
                plan_section = response[plan_start:plan_start+500]
                click.echo(f"\n📋 计划摘要：\n{plan_section}...\n")


@cli.command()
@click.option('--baseline', default='main~1', help='基线版本（默认: main~1）')
@click.option('--build', default='HEAD', help='构建版本（默认: HEAD）')
@click.option('--model', default='gpt-4', help='LLM 模型')
@click.option('--pass-rate-min', default=95, help='最低测试通过率')
@click.option('--coverage-drop-max', default=5, help='最大覆盖率降幅')
def regression(baseline, build, model, pass_rate_min, coverage_drop_max):
    """场景③：回归检测与质量门禁

    收集测试、覆盖率、Lint 指标，AI 评估是否放行
    """
    click.echo(" 场景③：回归检测与质量门禁")
    click.echo(f" 基线：{baseline}, 构建：{build}")

    config = {
        'baseline': baseline,
        'build': build,
        'model': model,
        'pass_rate_min': pass_rate_min,
        'coverage_drop_max': coverage_drop_max
    }
    result = scenario_3_regression.run(config)

    out = result.get('output_file_path')
    if out:
        click.echo(f" 门禁结果已保存：{out}")
        # 打印门禁判定
        if 'llm_response' in result:
            response = result['llm_response']
            if 'gate:' in response or 'PASS' in response or 'FAIL' in response:
                lines = response.split('\n')[:10]
                click.echo(f"\n 门禁判定：\n" + '\n'.join(lines) + "\n")


@cli.command(name='arch-drift')
@click.option('--model', default='gpt-4', help='LLM 模型')
def arch_drift(model):
    """场景④：架构影响与漂移扫描

    分析依赖图、分层违规、复杂度、API 破坏，AI 审计架构健康度
    """
    click.echo("  场景④：架构影响与漂移扫描")

    config = {'model': model}
    result = scenario_4_arch_drift.run(config)

    out = result.get('output_file_path')
    if out:
        click.echo(f" 架构门禁结果已保存：{out}")
        # 打印架构评分
        if 'llm_response' in result:
            response = result['llm_response']
            if 'arch_gate:' in response or 'score:' in response:
                lines = response.split('\n')[:15]
                click.echo(f"\n📐 架构评估：\n" + '\n'.join(lines) + "\n")

if __name__ == '__main__':
    cli()

# This is a test modification for snapshot demo
# Should be removed by rollback
