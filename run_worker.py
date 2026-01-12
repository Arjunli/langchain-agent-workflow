"""启动Worker脚本"""
import uvicorn
from app.queue.startup import main
import asyncio

if __name__ == "__main__":
    asyncio.run(main())



