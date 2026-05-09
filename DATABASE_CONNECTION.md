# 数据库连接指南

本文档提供了如何配置和连接到实际SQL Server数据库的详细说明。

## Docker环境中连接实际数据库

### 1. 修改docker-compose.yml文件

已经为您修改了`docker-compose.yml`文件，启用了实际数据库连接：

```yaml
environment:
  - DEV_MODE=False  # 关闭开发模式，使用实际数据库连接
  - DB_SERVER=192.168.0.234
  - DB_DATABASE=AIS20191210135722
  - DB_USERNAME=sa
  - DB_PASSWORD=Jhs16888
```

### 2. 确保SQL Server可访问

请确保：

1. SQL Server实例(192.168.0.234)正在运行
2. 该服务器允许远程连接
3. 防火墙已开放SQL Server端口(默认为1433)
4. 用户名和密码正确

### 3. 重启Docker容器

修改配置后，需要重新构建并启动容器：

```bash
docker-compose down
docker-compose up -d
```

## 连接问题排查

如果连接失败，请检查以下几点：

### 1. 网络连通性

确保Docker容器可以访问SQL Server：

```bash
docker-compose exec web ping 192.168.0.234
```

### 2. SQL Server配置

- 确认SQL Server已启用TCP/IP协议
- 确认SQL Server已允许混合模式认证(SQL Server和Windows认证)
- 确认SQL Server已允许远程连接

### 3. 检查日志

查看应用日志以获取详细错误信息：

```bash
docker-compose logs -f
```

### 4. ODBC驱动程序

应用程序已配置尝试多种ODBC驱动程序，但如果仍有问题，可能需要确认Docker容器中已正确安装SQL Server ODBC驱动程序。

## 临时使用开发模式

如果需要临时使用开发模式(模拟数据库连接)，可以修改`docker-compose.yml`文件：

```yaml
environment:
  - DEV_MODE=True  # 开发模式，使用模拟数据库连接
```

然后重启容器：

```bash
docker-compose down
docker-compose up -d
```

## 数据库连接实现说明

应用程序使用以下策略连接数据库：

1. 首先检查`DEV_MODE`环境变量，如果为`True`则使用模拟连接
2. 如果为`False`，则尝试使用多种SQL Server ODBC驱动程序连接
3. 如果所有驱动程序都失败，则尝试使用DSN连接
4. 如果所有方法都失败，则提供详细的错误信息和安装指南

这种实现方式确保了应用程序在不同环境下的灵活性和稳定性。