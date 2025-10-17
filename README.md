# 代码仓库分析系统

基于可插拔 Flow/Node 的代码仓库分析框架

## 特性
- 🎯 Common vs Custom Nodes 清晰分离
- 📦 Scenario 真正可插拔
- 🚀 支持并行/异步（引擎可后续扩展）
- 📊 可输出报告与指标

## 快速开始
```bash
# 安装依赖
pip install -r requirements.txt

# 生成本地快照（示例）
python cli.py snapshot --patterns "**/*.py"

# 分析开源项目（占位）
python cli.py adapt https://github.com/example/repo

# 回归测试（占位）
python cli.py test

# 扫描架构漂移（占位）
python cli.py drift --history-limit 100
```

## 项目结构
```
repo-analysis/
├── nodes/                # Node 定义
│   ├── common/           # 通用节点
│   └── custom/           # 企业定制节点
├── scenarios/            # 场景定义
├── utils/                # 工具函数
├── configs/              # 配置文件
├── templates/            # 报告模板
├── docs/                 # 文档
├── tests/                # 单元测试
└── cli.py                # CLI 入口
```
