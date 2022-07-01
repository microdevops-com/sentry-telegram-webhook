#!/usr/bin/env python3
import os
import json
import uvicorn
import aiohttp
import betterlogging
import textwrap
from fastapi import FastAPI, Request

app = FastAPI()
logger = betterlogging.get_colorized_logger("forwarder")

@app.post("/sentry-report")
async def handle_report(request: Request):
    resp = await request.json()

    tags = ""
    if "event" in resp and "tags" in resp["event"]:
        for tag in resp["event"]["tags"]:
            tags += "{key}: {value}\n".format(key=tag[0].replace("_", "\_").replace("*", "\*"), value=tag[1].replace("_", "\_").replace("*", "\*"))

    msg = textwrap.dedent(
        """\
        Project: {project}

        Message:
        ```
        {message}
        ```
        Tags:
        {tags}
        """
    ).format(
        project=resp["project"].replace("_", "\_").replace("*", "\*") if "project" in resp else "",
        message=resp["message"] if "message" in resp else "",
        tags=tags
    )

    s = aiohttp.ClientSession()
    url = "https://api.telegram.org/bot{token}/sendmessage".format(token=os.getenv("TOKEN"))
    data = {
        "chat_id": os.getenv("CHANNEL_ID"),
        "text": msg,
        "parse_mode": "Markdown",
        "reply_markup": {
            "inline_keyboard": [
                [
                    {
                        "text": "Open Issue",
                        "url": resp["url"]
                    }
                ]
            ]
        }
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url=url, json=data) as response:
            logger.info(await response.json())

    await s.close()

uvicorn.run(app, port=8000, host="127.0.0.1" if not os.getenv("DOCKER_MODE") else "0.0.0.0", log_level="trace")
