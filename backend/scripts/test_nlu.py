

import asyncio

import os

import sys

sys.path.append(os.path.abspath("."))

from app.chatbot.nlu import parse_message

async def test():

    msg = "find salons in vijayawada"

    res = await parse_message(msg)

    print(f"Message: {msg}")

    print(f"Intent: {res.intent}")

    print(f"Category: {res.category}")

    print(f"Location: {res.location_text}")

if __name__ == "__main__":

    asyncio.run(test())

