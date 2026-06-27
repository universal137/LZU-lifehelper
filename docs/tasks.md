# 兰大生活助手 - 升级任务清单

> 基于全盘代码审计，分阶段执行。
> 对应 Spec: `docs/spec-upgrade.md`。

---

## 任务总览

- [x] Task 1: 密码哈希升级（SHA-256 → PBKDF2）
- [x] Task 2: HTML 内容 XSS 转义
- [x] Task 3: 数据库索引添加
- [x] Task 4: Schema 迁移机制
- [x] Task 5: 校车购票事务竞态修复
- [x] Task 6: 输入校验加固
- [x] Task 7: 个人中心状态颜色修复

---

## Task 1: 密码哈希升级

**文件**: `desktop/models.py`
**当前问题**: `hash_password()` 使用裸 SHA-256 无盐哈希（第37行），彩虹表可秒破。
**目标**: 使用 `hashlib.pbkdf2_hmac` + 随机盐值 + 10万次迭代。

### 实施步骤
1. 修改 `hash_password(password, salt=None)` 函数：
   - 生成16字节随机盐值
   - 使用 `hashlib.pbkdf2_hmac('sha256', password, salt, 100000)`
   - 返回格式: `{salt_hex}:{hash_hex}`
2. 新增 `verify_password(password, stored_hash)` 函数：
   - 解析存储的盐值和哈希
   - 重新计算并比较
3. 修改 `authenticate()` 方法调用 `verify_password`
4. 修改 `seed_demo_data()` 中的密码使用新格式
5. 新增一次性迁移函数：检测旧格式（32位hex）自动升级为新格式

### 验证
- 用学生/老师/管理员账号登录均正常
- 旧密码格式可自动迁移

---

## Task 2: HTML 内容 XSS 转义

**文件**: `desktop/views.py`
**当前问题**: 14处 f-string HTML 直接拼接用户输入，存在 XSS 风险。

### 实施步骤
1. 在文件顶部 `import html`
2. 创建辅助函数 `def esc(text) -> str: return html.escape(str(text))`
3. 在以下位置对用户输入调用 `esc()`：
   - `refresh_home()` 中 `p["title"]`、`p["seller_name"]`、`a["title"]`
   - `open_activity_detail()` 中 `detail["title"]`、`detail["summary"]`
   - `open_moment_detail()` 中 `detail["content"]`、`c["content"]`、`c["display_name"]`
   - `refresh_profile()` 中用户信息字段
   - 管理后台详情中的商品描述、动态内容
   - `DetailDialog.add_section()` 中的内容

### 验证
- 在商品标题中输入 `<b>test</b>` 确认被正确转义显示为纯文本

---

## Task 3: 数据库索引添加

**文件**: `desktop/models.py`
**当前问题**: 13张表无任何索引，高频查询将随数据增长变慢。

### 实施步骤
1. 在 `initialize()` 方法的 `CREATE TABLE` 语句后添加索引创建
2. 使用 `CREATE INDEX IF NOT EXISTS` 避免重复创建
3. 添加的索引：
   - `idx_products_status_category` ON products(status, category)
   - `idx_products_seller` ON products(seller_id)
   - `idx_bookings_user_status` ON bookings(user_id, status)
   - `idx_bookings_slot` ON bookings(slot_id, status)
   - `idx_shuttle_tickets_route_date` ON shuttle_tickets(route_id, ride_date)
   - `idx_shuttle_tickets_user` ON shuttle_tickets(user_id, status)
   - `idx_activities_status` ON activities(status)
   - `idx_activity_registrations_user` ON activity_registrations(user_id, status)
   - `idx_moments_category_status` ON moments(category, status)
   - `idx_moment_comments_moment` ON moment_comments(moment_id)
   - `idx_moment_likes_moment` ON moment_likes(moment_id)

### 验证
- 启动应用后用 `PRAGMA index_list('products')` 确认索引存在

---

## Task 4: Schema 迁移机制

**文件**: `desktop/models.py`
**当前问题**: 版本号变化直接删库重建（第74-96行），用户数据全部丢失。

### 实施步骤
1. 定义 `MIGRATIONS` 字典：`{版本号: [SQL语句列表]}`
2. 修改 `initialize()` 中的版本检查逻辑：
   - 旧版本 < 新版本时，按顺序执行迁移 SQL
   - 每执行一条迁移更新 `schema_version`
   - 仅在完全无法恢复时（如核心表结构变更）才允许 reset
3. 第一版迁移内容：添加 Task 3 中的索引
4. 保留 `reset_database()` 作为紧急恢复手段，但需用户确认

### 验证
- 删除数据库后重建正常
- 已有数据库升级时不丢失数据

---

## Task 5: 校车购票事务竞态修复

**文件**: `desktop/models.py`
**当前问题**: `create_shuttle_ticket()`（第741-759行）检查余票和插入票不在同一事务。

### 实施步骤
1. 修改 `create_shuttle_ticket()` 使用 `BEGIN IMMEDIATE` 事务
2. 在事务内直接查询 `shuttle_routes` 获取余票（而非调用 `list_shuttle_routes` 重新开连接）
3. 在同一事务内完成：检查重复购票 → 检查余票 → 插入票 → 扣减余量
4. 与 `create_booking()` 保持一致的事务模式

### 验证
- 正常购票流程正常
- 余票为0时购票失败
- 重复购票被拒绝

---

## Task 6: 输入校验加固

**文件**: `desktop/models.py`
**当前问题**: 商品/活动输入无长度和格式校验。

### 实施步骤
1. 在 `create_product()` 中添加：
   - 标题长度 ≤ 50 字符
   - 描述长度 ≤ 2000 字符
   - 价格 > 0
2. 在 `create_activity()` 中添加：
   - 标题长度 ≤ 50 字符
   - 地点长度 ≤ 100 字符
   - 简介长度 ≤ 2000 字符
   - 时间格式校验：`datetime.strptime(start_time, "%Y-%m-%d %H:%M")`
3. 在 `create_moment()` 中添加：
   - 内容长度 ≤ 2000 字符
4. 在 `create_comment()` 中添加：
   - 内容长度 ≤ 500 字符

### 验证
- 输入超长标题时返回友好错误提示
- 输入非法时间格式时返回错误

---

## Task 7: 个人中心状态颜色修复

**文件**: `desktop/views.py`
**当前问题**: 预约状态判断 `status == "normal"` 但实际值是 `"active"`（第1921行）。

### 实施步骤
1. 定位 `refresh_profile()` 中的预约状态判断
2. 将 `b["status"] == "normal"` 改为 `b["status"] == "active"`
3. 确保车票状态判断也使用正确的值

### 验证
- 个人中心中正常预约显示绿色
- 已取消预约显示灰色/红色

---

## 执行顺序建议

```
Task 7 (5min) → Task 3 (30min) → Task 5 (30min) → Task 2 (1h)
→ Task 6 (1h) → Task 1 (2h) → Task 4 (3h)
```

---

## 第二阶段：架构+体验（P1）

- [x] B1: 登录页拆分（登录/注册 Tab 切换）
- [x] B1: 加载状态提示（refresh_user_all 时显示 loading overlay）
- [x] B1: 窗口自适应布局（商城网格动态列数）
- [x] B2: Dialog类合并（ProductDialog/ActivityDialog/MomentDialog → 通用 FormDialog）
- [x] B2: 管理后台操作抽象（5个 admin_change_* → 通用 _admin_operation）
- [x] A3: CSV导出修复（手动拼接 → csv 模块）
- [x] A3: 图片上传校验（文件魔数 + 5MB 大小限制）

---

## 第三阶段：性能+打磨（P2）

- [x] B2: QSS清理（移除47行无效CSS属性：box-shadow/text-shadow/letter-spacing/line-height/text-transform/show-grid）
- [x] C1: 数据库连接优化（启用 WAL journal_mode，提升并发读性能）
- [x] C1: 图标缓存（场馆emoji图标+校车图标缓存到类变量，避免每次刷新重复创建QPixmap）
- [x] C1: 刷新去重（moment列表刷新时恢复之前的选中位置，blockSignals避免触发不必要的二次查询）

---

## 第四阶段：工程质量（P3）

- [x] 入口异常处理（desktop_app.py 添加 try/except + QMessageBox + logging）
- [x] 空状态优化（表格空状态 📭 + moment列表空状态提示）
- [x] 日志系统（models.py 关键操作添加 logging：登录/商品发布/预约/购票/管理操作）
- [x] moment分类图标缓存（避免每次刷新重复创建 QPixmap）
- [ ] views.py 模块拆分（待实施：pages/ 目录已创建，需要将各页面构建方法提取为独立模块）

---

## 第五阶段：功能增强（P3续）

- [x] 表格排序（所有 QTableWidget 启用 setSortingEnabled）
- [x] 键盘快捷键（Ctrl+R / F5 刷新、Ctrl+Q 退出）
- [x] 商品图片匹配优化（扩展关键词库：新增手机/鼠标/耳机/充电/考研/英语/篮球/相机等20+关键词）
- [x] 管理日志页面增强（新增搜索筛选框，支持按操作/详情/管理员名搜索）

---

## 第六阶段：功能增强续（P3续）

- [x] 管理后台概览增强（新增活动总数+总预约数KPI，图表+日志左右布局）
- [x] 个人中心增强（新增有效预约/车票统计，XSS转义，空状态emoji）
- [x] 商品详情增强（留言列表HTML格式化显示，带用户名+时间+内容分层）
- [x] 活动报名进度可视化（详情面板增加分类/组织者/时间/地点元数据，百分比显示）

---

## 第七阶段：交互增强（P3续）

- [x] 商品实时搜索（输入关键词300ms防抖实时筛选，分类下拉联动刷新）
- [x] 生活圈评论增强（评论区显示用户彩色头像圆形标识，基于用户名首字母+avatar_color）
- [x] 场馆余量可视化（余量数字添加背景色：>5绿色底、1-5橙色底、0红色底，居中对齐）
- [x] 导航栏活跃状态增强（选中项边框加粗5px、字号放大、背景渐变更明显）
- [x] 导入avatar_color函数（修复views.py中评论头像的NameError）

---

## 第八阶段：界面细节（P3续）

- [x] 首页个性化欢迎（标题副标题显示"👋 欢迎回来，{用户名}！"）
- [x] 商品新品标签（24小时内发布的商品标题前显示🆕）
- [x] 动态列表头像（列表项显示作者彩色圆形头像，基于avatar_color+首字母）
- [x] 导入datetime（修复商品新品标签的NameError）

---

## 第九阶段：交互细节（P3续）

- [x] 首页KPI可点击（点击KPI卡片跳转到对应功能页面）
- [x] 图表数据标签（柱状图数值标签添加白色背景圆角框，更清晰）
- [x] 校车发车倒计时（新增"状态"列，显示"⏳ X分钟后"/"已发车"等）
- [x] 输入框字数统计（FormDialog文本框下方显示"0 / 2000"实时计数）

先修快速可见的 bug，再做安全加固，最后做架构级迁移。
