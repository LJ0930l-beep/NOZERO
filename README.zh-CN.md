# NO ZERO（中文版）

NO ZERO 是一个本地优先、安全优先的室内训练系统，面向 18–64 岁健康成年人。它用确定性规则负责安全、恢复、动作限制、负荷、进阶和计划；本地 Qwen 只负责解释与建议，不能绕过安全或训练规则。

## 当前版本

`1.0.0-rc2`。本版本修复了 V1 验收任务中的日期窗口、Progression 持久化、动作限制、肌群负荷、计划执行率、周有氧剂量、数据库迁移和前端中文界面问题。

## 快速开始

```powershell
python -m pip install -e ".[dev]"
Set-Location frontend
npm ci
npm run dev
```

另开终端启动 API：

```powershell
uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

浏览器打开 `http://127.0.0.1:3000`。未完成基础资料时会展示可浏览的演示数据；完成基础资料和评估后，页面会使用本地 API 数据。

## 产品边界

- 计划恢复日是成功执行，不会伪造训练 session。
- ZERO 是设备模式，也可以作为执行状态 `ZERO` 记录；`FULL/MINIMUM/RECOVERY/ZERO` 是执行状态，完整/救援/最小是剂量选择。
- 摄像头当前仅做本地预览；后端姿态合约支持校准、置信度和无法判断状态，但浏览器端自动计数尚未在 rc2 中宣称完成。
- 原始视频默认不保存、不上传。

完整的修复清单与调用链见 [`docs/ACCEPTANCE-FIX-REPORT.md`](docs/ACCEPTANCE-FIX-REPORT.md)，规则证据见 [`docs/EVIDENCE.md`](docs/EVIDENCE.md)。

## 测试

```powershell
python -m pytest -q
python -m ruff check backend ai pose scripts
python -m compileall -q backend ai pose scripts
Set-Location frontend
npm run test
npx tsc --noEmit
npm run lint
npm run build
npm run e2e
```
