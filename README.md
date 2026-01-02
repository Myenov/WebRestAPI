# WebRestAPI - Легковестный проект

WebRestAPI - это проект созданный от лени изучать fastapi 
просто проект от скуки

Пример кода:

```python
import asyncio
from WebRestAPI import (
    APIServer, APIConfiguration,
    Router, HTTPResponse
)

route_1 = Router(prefix="1")
route_2 = Router(prefix="2")
cfg = APIConfiguration(debug=True, routes=[route_1, route_2])
app = APIServer(cfg=cfg)


@route_1.get("/test/")
async def func_root_test():
    return HTTPResponse.build_response(
        {
            "status_code": 200,
            "status_text": "OK.",
            "html": "<h1>Hello route_1</h1>"
        }
    )


@route_2.get("/test/")
async def func_delete():
    return HTTPResponse.build_response(
        {
            "status_code": 200,
            "status_text": "OK.",
            "html": "<h1>hello route_2</h1>"
        }
    )


async def main():
    await app.run()

if __name__ == '__main__':
    asyncio.run(main())
```

