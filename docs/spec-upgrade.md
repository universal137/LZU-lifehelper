# 兰大生活助手 - 全面升级规格文档

> 基于 2026-06-27 全盘代码审计，覆盖 UI/UX、系统核心功能、架构、安全四个维度。
> 审计对象：models.py (1220行)、views.py (2266行)、style.qss (737行)。

---

## 一、现状评估总览

| 维度 | 评分 | 核心问题 |
|------|------|----------|
| **安全性** | 差 | SHA-256无盐哈希、XSS注入、密码硬编码、无文件校验 |
| **架构** | 差 | 两文件承载全部逻辑、无分层、无模块拆分 |
| **数据库** | 中 | 13表结构合理，但无索引、无迁移、降级即删库 |
| **UI/UX** | 中 | 视觉尚可，但无加载状态、无异步、有状态颜色逻辑bug |
| **代码质量** | 差 | 巨型类1450行70+方法、大量重复代码、无测试无日志 |
| **性能** | 中偏下 | 主线程同步阻塞、无连接池、重复查询 |

---

## 二、升级维度 A：系统核心功能

### A1. 安全加固（P0 优先级）

**[A1-1] 密码哈希升级**
- 当前：裸 `hashlib.sha256` 无盐（models.py:37）
- 目标：使用 `hashlib.pbkdf2_hmac`（标准库自带，无需第三方依赖），加随机盐值，迭代10万次
- 影响：`hash_password()`、`authenticate()`、seed 数据库密码
- 兼容：需提供一次性迁移脚本将旧密码转换为新格式

**[A1-2] HTML 内容转义（XSS 防护）**
- 当前：views.py 中所有 f-string HTML 直接拼接用户输入（14处）
- 目标：统一使用 `html.escape()` 对所有用户输入做转义
- 影响：首页商品列表、活动详情、生活圈详情、个人中心、管理后台详情

**[A1-3] 演示密码脱敏**
- 当前：密码明文写在 views.py:747-751
- 目标：密码仅在 models.py seed 时生成，UI 层只显示账号，密码从配置或环境变量读取

**[A1-4] 输入校验加固**
- 商品/活动标题：最大50字符
- 描述/内容：最大2000字符
- 价格：必须 > 0
- 活动时间：正则校验 `YYYY-MM-DD HH:MM` 格式

### A2. 数据库健壮性（P0 优先级）

**[A2-1] 添加数据库索引**
```sql
CREATE INDEX idx_products_status ON products(status);
CREATE INDEX idx_products_category ON products(category);
CREATE INDEX idx_bookings_user ON bookings(user_id, status);
CREATE INDEX idx_bookings_slot ON bookings(slot_id, status);
CREATE INDEX idx_shuttle_tickets_route ON shuttle_tickets(route_id, ride_date);
CREATE INDEX idx_shuttle_tickets_user ON shuttle_tickets(user_id, status);
CREATE INDEX idx_activities_status ON activities(status);
CREATE INDEX idx_activity_registrations_user ON activity_registrations(user_id, status);
CREATE INDEX idx_moments_category ON moments(category, status);
CREATE INDEX idx_moment_comments_moment ON moment_comments(moment_id);
CREATE INDEX idx_moment_likes_moment ON moment_likes(moment_id);
```

**[A2-2] Schema 迁移机制**
- 当前：版本变化直接删库重建（models.py:74-96）
- 目标：基于版本号的增量迁移，保留现有数据
- 实现：维护 `MIGRATIONS` 字典，按版本号依次执行 ALTER TABLE / CREATE INDEX

**[A2-3] 校车购票事务修复**
- 当前：`create_shuttle_ticket` 检查余票和插入票不在同一事务（models.py:741-759）
- 目标：使用 `BEGIN IMMEDIATE` + 单事务完成检查+插入，与 `create_booking` 保持一致

### A3. 功能增强（P1 优先级）

**[A3-1] CSV 导出修复**
- 当前：手动拼接字符串，逗号会破坏格式（models.py:908-917）
- 目标：使用 Python `csv` 模块，正确处理引号和转义

**[A3-2] 图片上传校验**
- 当前：仅检查文件后缀（models.py:512-521）
- 目标：校验文件魔数（magic bytes）、限制大小（5MB）、限制实际 MIME 类型

**[A3-3] 管理员日志事务一致性**
- 当前：状态更新和日志写入分两个事务（models.py:1098-1112）
- 目标：在同一事务中完成状态更新+日志写入

**[A3-4] 个人中心预约状态颜色修复**
- 当前：判断 `status == "normal"` 但实际值是 `"active"`（views.py:1921）
- 目标：修正判断逻辑

---

## 三、升级维度 B：UI/UX 体验

### B1. 交互体验优化（P1 优先级）

**[B1-1] 登录页拆分**
- 当前：登录和注册在同一页面，注册表单始终可见
- 目标：登录/注册分 Tab 切换，默认显示登录

**[B1-2] 加载状态提示**
- 当前：数据库查询在主线程同步执行，UI 冻结
- 目标：在 refresh 方法开始时显示 loading 提示（QLabel 覆盖层），完成后隐藏

**[B1-3] 窗口自适应布局**
- 当前：最小尺寸 1100x700，商城固定3列
- 目标：根据窗口宽度动态计算网格列数（3列→2列→1列）

**[B1-4] 输入长度限制**
- 所有 QLineEdit/QTextEdit 设置 maxLength
- 提供字数统计提示

### B2. 代码架构重构（P1 优先级）

**[B2-1] views.py 模块拆分**
```
desktop/
  views.py          # 仅保留 MainWindow 骨架
  pages/
    __init__.py
    auth_page.py     # 登录注册
    user_home.py     # 首页概览
    user_market.py   # 二手市场
    user_booking.py  # 场馆预约
    user_transit.py  # 校园出行
    user_activity.py # 活动中心
    user_moment.py   # 生活圈
    user_profile.py  # 个人中心
    admin_overview.py
    admin_users.py
    admin_products.py
    admin_bookings.py
    admin_activities.py
    admin_moments.py
    admin_logs.py
  components/
    __init__.py
    dialogs.py       # 通用对话框（合并重复 Dialog）
    toast.py         # Toast 提示
    table.py         # 通用表格组件
    chart.py         # BarChart
```

**[B2-2] Dialog 类合并**
- 当前：ProductDialog、ActivityDialog、MomentDialog 结构几乎相同
- 目标：抽象为通用 `FormDialog(parent, title, fields_config)`

**[B2-3] 管理后台操作抽象**
- 当前：5个 admin_change_* 方法流程完全一致
- 目标：抽象为 `admin_operation(entity_type, action, label)`

**[B2-4] QSS 清理**
- 移除所有无效 CSS 属性：`box-shadow`、`text-shadow`、`letter-spacing`、`line-height`、`text-transform`
- 移除无效的 `show-grid: false`

### B3. 样式增强（P2 优先级）

**[B3-1] 商品卡片自适应网格**
- 根据窗口宽度动态调整列数
- 卡片 hover 时轻微放大动画

**[B3-2] 空状态插画**
- 各列表为空时显示分类相关的 emoji 插图 + 提示文字

**[B3-3] 表格行交替色增强**
- 当前仅 `alternate-background-color`，可增加 hover 渐变效果

---

## 四、升级维度 C：性能优化

### C1. 查询优化（P2 优先级）

**[C1-1] 连接复用**
- 当前：每次操作 `sqlite3.connect()`
- 目标：使用单连接 + WAL 模式，提高并发读性能

**[C1-2] 图标缓存**
- 当前：refresh_bookings/refresh_buses 每次为每行创建 QPixmap
- 目标：缓存固定图标到类变量，避免重复创建

**[C1-3] 刷新去重**
- 当前：refresh_moments 总是 setCurrentRow(0) 触发二次查询
- 目标：刷新后恢复之前的选中位置，避免不必要的 open_moment_detail 调用

---

## 五、升级优先级矩阵

| 优先级 | 编号 | 任务 | 影响范围 | 预估工作量 |
|--------|------|------|----------|------------|
| **P0** | A1-1 | 密码哈希升级 | models.py | 2h |
| **P0** | A1-2 | HTML转义 | views.py | 1h |
| **P0** | A2-1 | 数据库索引 | models.py | 30m |
| **P0** | A2-2 | Schema迁移 | models.py | 3h |
| **P0** | A2-3 | 校车购票事务 | models.py | 30m |
| **P0** | A1-4 | 输入校验 | models.py | 1h |
| **P1** | B2-1 | views.py拆分 | views.py | 8h |
| **P1** | B1-1 | 登录页拆分 | views.py | 2h |
| **P1** | B1-2 | 加载状态 | views.py | 2h |
| **P1** | B1-3 | 窗口自适应 | views.py | 2h |
| **P1** | B2-2 | Dialog合并 | views.py | 3h |
| **P1** | B2-3 | 管理操作抽象 | views.py | 2h |
| **P1** | A3-1 | CSV导出修复 | models.py | 30m |
| **P1** | A3-2 | 图片上传校验 | models.py | 1h |
| **P1** | A3-4 | 状态颜色修复 | views.py | 15m |
| **P2** | B3-1 | 自适应网格 | views.py | 2h |
| **P2** | C1-1 | 连接复用 | models.py | 1h |
| **P2** | C1-2 | 图标缓存 | views.py | 30m |
| **P2** | B2-4 | QSS清理 | style.qss | 30m |

---

## 六、执行策略

### 第一阶段：安全+稳定性（P0）
所有 P0 项，确保系统安全可靠。

### 第二阶段：架构+体验（P1）
模块拆分 + 交互优化，提升可维护性和用户体验。

### 第三阶段：性能+打磨（P2）
性能优化 + 样式清理，精益求精。
