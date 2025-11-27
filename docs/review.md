# Django 项目代码审查报告

## 核心判断

✅ **值得做 Docker 化**：项目结构清晰，但存在多个生产环境安全隐患，Docker 化可以强制修复这些问题。

❌ **不值得直接部署**：当前代码存在严重安全漏洞和可移植性问题，必须修复后才能部署。

## 关键洞察

### 数据结构
- 核心数据流：前端表单 → `sqlparse()` → SQL 拼接 → pandas DataFrame → 图表/表格
- 数据所有权：SQL Server 数据库拥有原始数据，Django 仅做查询和展示
- 数据转换：大量使用 pandas 进行数据透视和格式化，内存占用可能较大

### 复杂度
- SQL 拼接逻辑重复出现在多个 views.py 中（chpa_data, potential, internal_sales, retail）
- 每个模块都有自己的 `sqlparse()` 函数，这是典型的代码重复
- 数据透视逻辑分散，难以统一维护

### 风险点
- **SQL 注入风险**：字符串拼接 SQL，且允许用户输入自定义 SQL
- **硬编码密钥**：SECRET_KEY 直接写在代码中
- **生产环境配置错误**：DEBUG=True, ALLOWED_HOSTS=["*"]
- **Windows 路径硬编码**：缓存路径 `E:/cached`，字体路径 `C:/Windows/Fonts`
- **缺少错误处理**：数据库连接失败、SQL 执行错误等没有异常捕获

## 致命问题

### 1. SQL 注入漏洞（严重）

**位置**：
- `chpa_data/views.py:266-294` - `sqlparse()` 函数
- `potential/views.py:852-893` - `sqlparse()` 函数
- `internal_sales/views.py:615-640` - `sqlparse()` 函数
- `retail/views.py:195-216` - `sqlparse()` 函数

**问题代码**：
```python
sql = "Select * from %s Where PERIOD = '%s' And UNIT = '%s'" % (
    DB_TABLE,
    context["PERIOD_select"],
    context["UNIT_select"],
)
```

**更严重的是**：
```python
if context["customized_sql"] == "":
    # ... 拼接逻辑
else:
    sql = context["customized_sql"]  # 直接使用用户输入的 SQL！
```

**Linus 式方案**：
"这是在解决不存在的问题。真正的问题是：为什么允许用户直接输入 SQL？"

**修复建议**：
1. 立即禁用 `customized_sql` 功能，或至少添加严格的权限检查
2. 使用 Django ORM 或参数化查询替代字符串拼接
3. 如果必须保留，至少使用 `sqlparse` 库验证 SQL 语法

### 2. 硬编码密钥（严重）

**位置**：`datasite/settings.py:23`

```python
SECRET_KEY = "qteh2xx_xz#z#keg0%*++%yo%)n2nn27!ogxk5#2z%4*k57^s)"
```

**Linus 式方案**：
"好代码没有特殊情况。密钥应该从环境变量读取，没有例外。"

**修复建议**：
```python
SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-key-only')
```

### 3. 生产环境配置错误（严重）

**位置**：`datasite/settings.py:26-28`

```python
DEBUG = True
ALLOWED_HOSTS = ["*"]
```

**Linus 式方案**：
"Never break userspace，但也不能让攻击者破坏你的服务器。"

**修复建议**：
```python
DEBUG = os.environ.get('DEBUG', 'False') == 'True'
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '').split(',')
```

### 4. Windows 路径硬编码（中等）

**位置**：
- `datasite/settings.py:96` - `"LOCATION": "E:/cached"`
- `chpa_data/charts.py:16` - `fname="C:/Windows/Fonts/msyh.ttc"`
- `potential/chart_class.py:32` - `fname="C:/Windows/Fonts/msyh.ttc"`

**Linus 式方案**：
"好代码没有特殊情况。路径应该用 `os.path.join()` 或环境变量，消除平台依赖。"

**修复建议**：
```python
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.filebased.FileBasedCache",
        "LOCATION": os.environ.get('CACHE_LOCATION', os.path.join(BASE_DIR, 'cache')),
    }
}
```

字体路径可以通过环境变量或配置文件指定。

### 5. 缺少错误处理（中等）

**位置**：多个 views.py 中的数据库查询

**问题代码**：
```python
df = pd.read_sql_query(sql, ENGINE)  # 没有 try-except
```

**Linus 式方案**：
"如果数据库连接失败，用户应该看到错误信息，而不是 500 错误页面。"

**修复建议**：
```python
try:
    df = pd.read_sql_query(sql, ENGINE)
except Exception as e:
    logger.error(f"Database query failed: {e}")
    return HttpResponse(json.dumps({"error": "查询失败"}), status=500)
```

### 6. 代码重复（轻微）

**位置**：多个模块都有 `sqlparse()` 函数

**Linus 式方案**：
"这 10 行可以变成 3 行。把 `sqlparse()` 移到 `datasite/commons.py`，所有模块共享。"

**修复建议**：
在 `datasite/commons.py` 中创建统一的 `sqlparse()` 函数，接受配置参数。

## 性能问题

### 1. 大数据集内存占用

**位置**：`chpa_data/views.py:297-375` - `get_df()` 函数

**问题**：
- 使用 `pd.read_sql_query()` 一次性加载所有数据到内存
- 数据透视操作 `pd.pivot_table()` 可能产生巨大的 DataFrame
- 没有分页或限制查询结果数量

**建议**：
- 添加查询结果数量限制
- 对于大数据集，考虑使用数据库层面的聚合而不是 pandas

### 2. 缓存配置不当

**位置**：`datasite/settings.py:92-99`

**问题**：
- 使用文件缓存，但路径硬编码为 Windows 路径
- 没有设置缓存过期时间
- 缓存可能占用大量磁盘空间

**建议**：
- Docker 环境中使用 Redis 或 Memcached
- 设置合理的缓存过期时间

## Docker 化需要的代码改动

### 必须修改（阻塞部署）
1. ✅ `SECRET_KEY` 从环境变量读取
2. ✅ `DEBUG` 从环境变量读取
3. ✅ `ALLOWED_HOSTS` 从环境变量读取
4. ✅ `CACHES['LOCATION']` 使用环境变量或相对路径
5. ✅ 字体路径使用环境变量

### 强烈建议修改（安全风险）
1. ⚠️ 禁用或限制 `customized_sql` 功能
2. ⚠️ 使用参数化查询替代字符串拼接
3. ⚠️ 添加数据库查询错误处理

### 可选修改（代码质量）
1. 统一 `sqlparse()` 函数到 `commons.py`
2. 添加查询结果数量限制
3. 使用 Redis 替代文件缓存

## 总结

**品味评分**：🟡 凑合

**致命问题**：
- SQL 注入漏洞（允许用户输入自定义 SQL）
- 硬编码密钥和配置
- Windows 路径硬编码

**改进方向**：
1. "把这个特殊情况消除掉" - 统一 SQL 解析逻辑
2. "这 10 行可以变成 3 行" - 使用环境变量替代硬编码
3. "数据结构错了，应该是..." - 使用参数化查询替代字符串拼接

**部署建议**：
- Docker 化可以强制修复配置问题（通过环境变量）
- 但 SQL 注入漏洞必须在代码层面修复
- 建议在 Docker 化后立即进行安全审计

