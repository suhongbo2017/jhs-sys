# Docker 设置指南

本文档提供了设置和排查 Docker 问题的详细指南，特别是针对 Windows 环境下的 Docker Desktop 设置。

## 问题排查

如果你遇到以下错误：

```
error during connect: Get "http://%2F%2F.%2Fpipe%2FdockerDesktopLinuxEngine/v1.47/containers/json?all=1&filters=...": open //./pipe/dockerDesktopLinuxEngine: The system cannot find the file specified.
```

这表明 Docker 守护程序未运行或无法访问。以下是解决步骤：

## 1. 安装 Docker Desktop

如果尚未安装 Docker Desktop：

1. 从[官方网站](https://www.docker.com/products/docker-desktop/)下载 Docker Desktop
2. 按照安装向导完成安装
3. 安装过程中，确保选择「使用 WSL 2」选项

## 2. 启动 Docker Desktop

1. 从开始菜单或桌面快捷方式启动 Docker Desktop
2. 等待 Docker Desktop 完全启动（托盘图标变为稳定状态）
3. 首次启动可能需要几分钟时间

## 3. 验证 Docker 是否正常运行

打开 PowerShell 或命令提示符，运行：

```powershell
docker info
```

如果显示 Docker 信息，则表示 Docker 已正常运行。

## 4. WSL 2 相关问题

Docker Desktop 在 Windows 上依赖 WSL 2。如果遇到问题：

1. 确保已安装 WSL 2。在管理员 PowerShell 中运行：

```powershell
wsl --status
```

2. 如果 WSL 未安装或需要更新，运行：

```powershell
wsl --install
```

或

```powershell
wsl --update
```

3. 确保 Docker Desktop 设置中启用了 WSL 2 集成：
   - 打开 Docker Desktop
   - 点击右上角的齿轮图标（设置）
   - 选择「Resources」>「WSL Integration」
   - 确保已启用 WSL 2 集成

## 5. 防火墙/杀毒软件问题

有时防火墙或杀毒软件会阻止 Docker：

1. 临时禁用防火墙或杀毒软件，测试 Docker 是否正常工作
2. 如果正常工作，则在防火墙/杀毒软件中添加 Docker 相关程序的例外

## 6. Docker 服务未运行

如果 Docker 服务未运行：

1. 打开「服务」应用程序（按 Win+R，输入 services.msc）
2. 找到「Docker Desktop Service」
3. 右键点击并选择「启动」

## 7. 重启 Docker 和计算机

如果以上方法都不起作用：

1. 完全退出 Docker Desktop
2. 重启计算机
3. 启动 Docker Desktop

## 8. 重新安装 Docker

如果问题仍然存在：

1. 卸载 Docker Desktop
2. 重启计算机
3. 重新安装最新版本的 Docker Desktop

## 使用 Docker 的提示

成功设置 Docker 后，可以使用以下命令来管理容器：

```powershell
# 构建并启动容器
docker-compose up -d

# 查看容器日志
docker-compose logs -f

# 停止并移除容器
docker-compose down
```

## 需要更多帮助？

如果以上步骤都不能解决问题，请参考：

- [Docker Desktop 官方文档](https://docs.docker.com/desktop/windows/)
- [Docker Desktop WSL 2 后端](https://docs.docker.com/desktop/windows/wsl/)
- [Docker Desktop 故障排除](https://docs.docker.com/desktop/troubleshoot/overview/)