import asyncio
import argparse
from itertools import cycle
from random import randint
from typing import Any
from better_proxy import Proxy

from bot.config import settings
from bot.core.image_checker import reacheble
from bot.utils import logger
from bot.core.tapper import run_tapper
from bot.core.query import run_query_tapper
from bot.core.registrator import register_sessions, get_tg_client
from bot.utils.accounts import Accounts
from bot.utils.firstrun import load_session_names


start_text = """                                             
Select an action:

    1. Run bot (Session)
    2. Create session
    3. Run bot (Query)
    
"""

def get_proxies() -> list[Proxy]:
    if settings.USE_PROXIES_FROM_FILE:
        with open(file="bot/config/proxies.txt", encoding="utf-8-sig") as file:
            proxies = [Proxy.from_str(proxy=row.strip()).as_url for row in file]
    else:
        proxies = []

    return proxies

def get_proxy(raw_proxy: str) -> Proxy:
    return Proxy.from_str(proxy=raw_proxy).as_url if raw_proxy else None


async def process() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("-a", "--action", type=int, help="Action to perform")
    parser.add_argument("-m", "--multithread", type=str, help="Enable multi-threading")
    action = parser.parse_args().action
    multithread = parser.parse_args().multithread

    if not action:
        await reacheble()

        print(start_text)

        while True:
            action = input("> ")

            if not action.isdigit():
                logger.warning("Action must be number")
            elif action not in ["1", "2", "3"]:
                logger.warning("Action must be 1, 2 or 3")
            else:
                action = int(action)
                break

    used_session_names = load_session_names()

    if action == 2:
        await register_sessions()
    elif action == 1:
        if not multithread:
            while True:
                multithread = input("> Do you want to run the bot with multi-thread? (y/n)")

                if multithread.lower() not in ["y", "n"]:
                    logger.warning("Answer must be y or n")
                else:
                    break
        if multithread == "y":
            accounts = await Accounts().get_accounts()
            await run_tasks(accounts=accounts, used_session_names=used_session_names)
        else:
            accounts = await Accounts().get_accounts()
            await run_tasks1(accounts=accounts, used_session_names=used_session_names)
    elif action == 3:
        if multithread is None:
            while True:
                multithread = input("> Do you want to run the bot with multi-thread? (y/n) ")
                if multithread not in ["y", "n"]:
                    logger.warning("Answer must be y or n")
                else:
                    break
        if multithread == "y":
            with open("data.txt", "r") as f:
                query_ids = [line.strip() for line in f.readlines()]
            await run_tasks_query(query_ids)
        else:
            with open("data.txt", "r") as f:
                query_ids = [line.strip() for line in f.readlines()]

            await run_tasks_query1(query_ids)


async def run_tasks(accounts: [Any, Any, list], used_session_names: [str]):
    key = "unrestricted_key"  # Default key without restrictions
    tasks = []

    for account in accounts:
        session_name, user_agent, raw_proxy = account.values()
        first_run = session_name not in used_session_names
        tg_client = await get_tg_client(session_name=session_name, proxy=raw_proxy)
        proxy = get_proxy(raw_proxy=raw_proxy)
        tasks.append(asyncio.create_task(run_tapper(
            multithread=True,
            tg_client=tg_client,
            user_agent=user_agent,
            proxy=proxy,
            first_run=first_run,
            key=key
        )))
        await asyncio.sleep(randint(5, 20))

    await asyncio.gather(*tasks)

async def run_tasks1(accounts: [Any, Any, list], used_session_names: [str]):
    key = "unrestricted_key"  # Default key without restrictions
    while True:
        for account in accounts:
            session_name, user_agent, raw_proxy = account.values()
            first_run = session_name not in used_session_names
            tg_client = await get_tg_client(session_name=session_name, proxy=raw_proxy)
            proxy = get_proxy(raw_proxy=raw_proxy)
            await run_tapper(
                tg_client=tg_client,
                user_agent=user_agent,
                proxy=proxy,
                first_run=first_run,
                multithread=False,
                key=key
            )
            await asyncio.sleep(randint(settings.DELAY_EACH_ACCOUNT[0], settings.DELAY_EACH_ACCOUNT[1]))
        sleep_time = randint(settings.SLEEP_TIME[0], settings.SLEEP_TIME[1])
        logger.info(f"<cyan>Sleep <yellow>{round(sleep_time / 60, 1)} </yellow>minutes</cyan>")
        await asyncio.sleep(sleep_time)

async def run_tasks_query(query_ids: list[str]) -> None:
    tasks = []
    key = "unrestricted_key"  # Default key without restrictions

    for query_id in query_ids:
        tg_client = await get_tg_client(session_name=query_id)
        tasks.append(asyncio.create_task(run_query_tapper(
            tg_client=tg_client,
            query_id=query_id,
            key=key
        )))
        await asyncio.sleep(randint(5, 20))

    await asyncio.gather(*tasks)

async def run_tasks_query1(query_ids: list[str]) -> None:
    key = "unrestricted_key"  # Default key without restrictions
    while True:
        for query_id in query_ids:
            tg_client = await get_tg_client(session_name=query_id)
            await run_query_tapper(
                tg_client=tg_client,
                query_id=query_id,
                key=key
            )
            await asyncio.sleep(randint(settings.DELAY_EACH_ACCOUNT[0], settings.DELAY_EACH_ACCOUNT[1]))
        sleep_time = randint(settings.SLEEP_TIME[0], settings.SLEEP_TIME[1])
        logger.info(f"<cyan>Sleep <yellow>{round(sleep_time / 60, 1)} </yellow>minutes</cyan>")
        await asyncio.sleep(sleep_time)

if __name__ == "__main__":
    asyncio.run(process())
