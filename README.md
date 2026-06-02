# 科研通自动签到脚本

一个用于自动签到科研通（AbleSCI）平台的 Python 脚本。支持环境变量配置，可集成到定时任务框架（如青龙脚本框架）中运行。

## 功能特性

- ✅ **自动登录**：使用账号密码自动登录科研通平台
- ✅ **自动签到**：登录成功后自动进行每日签到
- ✅ **多平台支持**：支持 Windows、macOS、Linux 等多个操作系统
- ✅ **日志记录**：详细的操作日志记录
- ✅ **青龙集成**：完美支持青龙脚本框架的通知机制
- ✅ **随机延迟**：支持随机延迟执行，避免被识别为机器人
- ✅ **User-Agent 随机化**：使用多个浏览器 User-Agent 提高隐蔽性

## 环境要求

- Python 3.6+
- 无需第三方依赖（仅使用 Python 标准库）

## 安装

1. 克隆仓库：
```bash
git clone https://github.com/wqe134/keyantong_autosign.git
cd keyantong_autosign
```

2. 无需额外依赖安装，直接使用

## 使用方法

### 基础用法

设置环境变量 `ABLESCI_AUTH`，格式为 `账号#密码`，然后运行脚本：

```bash
export ABLESCI_AUTH="your_email@example.com#your_password"
python 科研通签到.py
```

### 配置环境变量

#### 方式1：Linux/macOS 命令行
```bash
export ABLESCI_AUTH="your_email@example.com#your_password"
python 科研通签到.py
```

#### 方式2：Windows 命令行
```cmd
set ABLESCI_AUTH=your_email@example.com#your_password
python 科研通签到.py
```

#### 方式3：Python 代码中设置
```python
import os
os.environ['ABLESCI_AUTH'] = 'your_email@example.com#your_password'
```

### 青龙脚本框架集成

在青龙脚本框架中添加环境变量：

1. 进入青龙面板 → 系统设置 → 环境变量
2. 添加环境变量：
   - 变量名：`ABLESCI_AUTH`
   - 变量值：`your_email@example.com#your_password`
3. 新建定时任务：
   ```
   0 8 * * * python /path/to/科研通签到.py
   ```

## 环境变量说明

| 环境变量 | 说明 | 格式 | 必需 |
|---------|------|------|------|
| ABLESCI_AUTH | 科研通账号和密码 | `account#password` | ✅ 是 |

**格式说明：**
- 账号和密码用 `#` 分隔
- 前后空格会自动去除
- 账号和密码都不能为空

## 脚本参数

该脚本无命令行参数，所有配置通过环境变量完成。

## 输出日志

脚本会生成日志文件 `ablesci_sign.log`，记录每次执行的结果：

```
[2026-06-02 08:30:15] code=0 msg=签到成功，已于 [08:30:15] 签到
[2026-06-02 08:31:20] code=-1 msg=登录失败，账号或密码错误
```

## 返回码说明

| 返回码 | 说明 |
|-------|------|
| 0 | 签到成功 |
| -1 | 响应错误或网络异常 |
| 其他 | 登录失败或其他错误 |

## 常见问题

### Q: 脚本提示"缺少环境变量 ABLESCI_AUTH"
**A:** 请确保已正确设置环境变量 `ABLESCI_AUTH`，格式为 `账号#密码`

### Q: 提示"账号或密码不能为空"
**A:** 检查环境变量格式，确保 `#` 前后都有账号和密码内容

### Q: 登录失败，返回"响应不是 JSON"
**A:** 可能是网络问题或科研通服务异常，请检查网络连接或稍后重试

### Q: 可以同时配置多个账号吗？
**A:** 当前版本只支持单个账号，如需多个账号可运行多个脚本实例

### Q: 脚本是否支持代理？
**A:** 当前版本不支持代理，如需代理可修改源代码的 `build_opener` 部分

## 脚本工作流程

```
1. 验证环境变量 ABLESCI_AUTH
   ↓
2. 可选的随机延迟（25% 概率延迟 60-180 秒）
   ↓
3. 解析账号和密码
   ↓
4. 获取登录页面，提取 CSRF token
   ↓
5. 使用账号密码提交登录请求
   ↓
6. 检查登录是否成功
   ↓
7. 发送签到请求
   ↓
8. 记录签到结果和日志
   ↓
9. 发送青龙通知（如果环境支持）
```

## 安全提示

- ⚠️ **不要**将账号密码硬编码在脚本中
- ⚠️ **不要**在公开场合泄露环境变量内容
- ⚠️ 建议使用**项目专用账号**而非主账号
- ⚠️ 定期检查日志中是否有异常登录信息
- ✅ 环境变量会通过标准库安全处理

## 支持的浏览器 User-Agent

脚本内置了多个浏览器的 User-Agent，每次请求会随机选择，以提高隐蔽性：

- Chrome (Windows 10, x64)
- Safari (macOS)
- Safari (iOS)
- Chrome (Android)

## 通知功能

脚本支持与青龙脚本框架集成，在以下场景发送通知：

- ✅ 签到成功
- ⚠️ 缺少环境变量
- ❌ 登录失败
- ❌ 网络异常或其他错误

## 许可证

MIT License

## 作者

- cjy

## 贡献

欢迎提交 Issue 和 Pull Request！

## 更新日志

### v1.0 (2026-06-02)
- 初始版本发布
- 支持自动登录和签到
- 集成青龙脚本框架通知
- 详细的日志记录

## 相关链接

- [科研通官网](https://www.ablesci.com/)
- [青龙脚本框架](https://github.com/whyour/qinglong)

---

**最后更新：** 2026-06-02  
**维护状态：** 活跃
