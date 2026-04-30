# Noobot Index Research

这是一个独立的指数研究助手项目，第一阶段目标是跑通：

- 纳斯达克综合指数
- 标普500指数
- 沪深300指数
- 上证指数

当前功能：

- 拉取指数日线行情
- 保存到本地 SQLite 数据库
- 计算 MA20 / MA60 / MA120
- 计算 20 日年化波动率
- 计算历史回撤
- Streamlit 前端展示
- 自动生成 Markdown 指数研究简报

## 1. 创建虚拟环境

```bash
python -m venv .venv