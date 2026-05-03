# 兰大生活助手

当前仓库同时包含两个基础版本：

- `desktop_app.py`：桌面版，使用 `PySide6 (Qt)`，更贴近“电脑软件 / exe / 快捷方式”方向
- `src/server` + `public`：Web 版原型，保留给后续前后端拆分或接口联调

## 桌面版运行

```bash
python desktop_app.py
```

也可以直接双击：

- `run_desktop.bat`

创建桌面快捷方式：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\create_shortcut.ps1
```

执行后会在项目根目录生成 `兰大生活助手.lnk`，双击即可启动。

## 打包为 exe

当前环境已安装 `pyinstaller`，可直接执行：

```bash
pyinstaller --noconfirm --onefile --windowed --name 兰大生活助手 desktop_app.py
```

生成的 `exe` 默认位于 `dist\兰大生活助手.exe`。

## 当前实现

- 登录页 + 桌面工作台双层结构
- 左侧主导航 + 顶部内容横幅 + 模块内二级导航的多级 UI
- 参考校园服务平台、闲置交易产品和社区产品的信息组织方式
- 五个核心业务模块的 Qt 桌面标签页
- 商品发布、筛选、留言
- 场馆未来 3 天时段展示、预约与取消
- 校车余票预订与共享单车站点显示
- 活动发布、报名、名单导出
- 生活圈动态发布与标签筛选
- 三类演示账号登录与密码修改

## 后续建议

- 将内存数据改为 SQLite 持久化
- 补登录、用户角色与管理员权限
- 再接入图片、本地数据备份与正式安装包
