import asyncio
import random
from uuid import uuid4

import config
import documents
from liquyd import configure, Liquyd
from documents import PlaygroundLog
from config import LIQUYD_CONFIG


async def create_sample_data() -> None:

    methods = ["GET", "POST", "PUT", "PATCH", "DELETE"]
    endpoint_paths = [
        "/api/logs",
        "/api/health",
        "/api/auth/login",
        "/api/users",
        "/api/projects",
    ]
    project_names = ["playground", "central-obs", "liquyd"]
    status_codes = [200, 201, 400, 401, 403, 404, 500]

    for _ in range(10):
        log = PlaygroundLog(
            id=str(uuid4()),
            project_name=random.choice(project_names),
            endpoint_path=random.choice(endpoint_paths),
            status_code=random.choice(status_codes),
            method=random.choice(methods),
        )
        await log.save()
        print("saved:", log)


async def query_sample_data() -> None:
    logs = await PlaygroundLog.filter(project_name="playground").all()
    print("Queried logs:", logs)


async def main() -> None:
    client = Liquyd(config=LIQUYD_CONFIG["default"])
    await client.start()
    ...

    # first_log = await PlaygroundLog.filter(project_name="playground").first()
    # print("first_log:", first_log)

    # one_log = await PlaygroundLog.get(id="83678764-38e7-4603-8c43-c2181110d66b")
    # print("one_log:", one_log)

    # maybe_log = await PlaygroundLog.get_or_none(id="not-found")
    # print("maybe_log:", maybe_log)

    # if first_log is not None:
    #     await first_log.delete()
    #     print("deleted:", first_log)

    # await query_sample_data()
    try:
        # await create_sample_data()
        all_logs = await PlaygroundLog.filter(project_name="liquyd").all()
        print("total:", len(all_logs))
        print("all_logs:", all_logs)
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())
