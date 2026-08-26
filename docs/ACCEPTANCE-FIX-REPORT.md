# NO ZERO V1 Acceptance Fix（中文版）

版本：`1.0.0-rc2`  
分支：`fix/v1-acceptance`

## 本轮已修复

- Progression：新增 `progression_states` 持久化；读取最近三次同动作表现，连续两次高质量完成后才推进一个变量，单次异常不会直接改写长期动作变式。
- Safety / Restriction：结构化红旗项进入安全筛查；动作疼痛会解析为膝、腕、肩、腰背等标签；禁忌动作被排除，限制动作会降级、缩小剂量或使用替代动作。
- Recovery / 日期：统一使用本地训练日的包含式日期窗口，修复用最近 N 条记录冒充最近 N 天的问题。
- Training Load：按主要肌群 1.0 组、次要肌群 0.5 组计算，分别输出肌群、动作模式、训练分钟和有氧分钟；最近 48 小时的高负荷模式会影响下一份计划。
- Plan Adherence：新增 `plan_executions`；按到期计划日计算，计划恢复日自动结算为 `RECOVERY`，不再要求伪造训练 session。
- 有氧剂量：按目标和评估基线生成每周目标，训练中的心肺活动与日常活动都可以计入进度。
- Week-to-week：四周计划展示 Adaptation/Base、Progress、Progress、Consolidation/Reassessment，并对组数、次数或持续时间做渐进变化。
- 数据库兼容：加入 `schema_meta` 和增量迁移；保留旧用户、评估、周期、session、wellness、memory 数据，并有旧 schema→rc2 自动化测试。
- 前端：默认中文 UI；完整/救援/最小剂量与 FULL/MINIMUM/RECOVERY/ZERO 执行状态分开；最小剂量提交真实执行的动作和时长。
- CI / E2E / 证据：加入 GitHub Actions、完整用户流、安全阻断、最小训练三组 Playwright 文件及 Evidence Registry。

## Pose 版本声明

当前浏览器摄像头仍是“本地预览”能力，后端已经具备校准、姿态分析和 `UNABLE_TO_DETERMINE` 合约，但前端尚未捆绑浏览器端 MediaPipe 推理模型。因此本 rc2 不把浏览器自动计数宣称为已验收能力；低可见度、缺 landmark 或未校准状态不会增加次数，手动模式始终可用。

## 关键调用链

```text
Onboarding
  → Safety Screening
  → Restriction Resolver
  → Exercise Filter
  → Training Engine
  → ApplicationService
  → SQLiteRepository
```

```text
Workout Feedback
  → Recovery + Training Load
  → workout session / plan execution
  → Progression State
  → future plan adjustment
  → Dashboard Plan Adherence / aerobic dose
```

## 验证命令

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

`P0-06` 是显式降级声明，不作为“浏览器自动计数已完成”通过；其余 P0 以真实调用链、迁移测试和回归测试为准。
