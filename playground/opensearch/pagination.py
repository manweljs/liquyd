import asyncio

from config import LIQUYD_CONFIG
from documents import PlaygroundLog
from liquyd import Liquyd


async def main() -> None:
    runtime_config = dict(LIQUYD_CONFIG["default"])
    runtime_config.pop("documents", None)

    runtime = Liquyd(config=runtime_config)
    await runtime.start()
    try:
        result = await (
            PlaygroundLog.filter()
            .order_by("project_name", "id")
            .paginate(page=1, page_size=5)
        )
        print(
            {
                "page": result.page,
                "page_size": result.page_size,
                "total": result.total,
                "total_pages": result.total_pages,
                "items": len(result.items),
            }
        )
    finally:
        await runtime.close()


if __name__ == "__main__":
    asyncio.run(main())
