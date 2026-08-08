import uvicorn

from config import settings

if __name__ == '__main__':
    print(f"Server running at: http://localhost:{settings.port}/")
    uvicorn.run(
        "app.controller.controller:app",
        host=settings.host,
        port=settings.port,
        reload=True,
    )
