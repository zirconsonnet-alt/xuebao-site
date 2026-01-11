# 逻辑 Bingo（FastAPI + Jinja2 + HTMX）

## 目录结构
- `main.py`: FastAPI 入口
- `logic.py`: 逻辑 Bingo 生成器（最简版本）
- `apps/logic-bingo`: 模板与静态资源

## 运行方式
1. 安装依赖：`fastapi`, `uvicorn`, `numpy`
2. 启动：
   ```bash
   uvicorn main:app --reload
   ```
3. 访问：`http://127.0.0.1:8000/logic-bingo/`

## 复制到网站 apps 目录
将 `logic-bingo-web/apps/logic-bingo` 拷贝到目标站点的 `apps` 目录。
若需要更改路由前缀，请修改 `main.py` 中的 `APP_SLUG` 与 `BASE_PATH`。
