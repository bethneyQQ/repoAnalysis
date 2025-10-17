import click
from scenarios import scenario_1_local_snapshot

@click.group()
def cli():
    """代码仓库分析工具"""
    pass

@cli.command()
@click.option('--patterns', multiple=True, default=['**/*.py'], help='文件匹配模式')
@click.option('--output', default='.ai-snapshots', help='输出目录（当前未直接使用）')
def snapshot(patterns, output):
    """创建本地快照"""
    config = {'file_patterns': list(patterns), 'output_dir': output}
    result = scenario_1_local_snapshot.run(config)
    out = result.get('output_file_path')
    if out:
        click.echo(f"✅ 快照已保存：{out}")
    else:
        click.echo("✅ 快照已生成（mock LLM 内容），详见 .ai-snapshots/ 目录")

@cli.command()
@click.argument('repo', required=False)
def adapt(repo):
    """开源项目理解与组织化改造（占位）"""
    click.echo("🔧 adapt: TBD（将根据 org_rules 与依赖图生成改造计划）")
    if repo:
        click.echo(f"   输入 repo: {repo}")

@cli.command()
@click.option('--history-limit', default=100, help='历史窗口大小')
def drift(history_limit):
    """架构漂移扫描（占位）"""
    click.echo(f"🏗️  drift: TBD（history_limit={history_limit}）")

@cli.command()
def test():
    """回归测试（占位）"""
    click.echo("🧪 运行测试... (TBD)")
    click.echo("✅ 占位完成")

if __name__ == '__main__':
    cli()
