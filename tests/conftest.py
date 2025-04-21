import os
import subprocess
import time
from pathlib import Path
from typing import Callable
from unittest.mock import create_autospec

import docker
import httpx
import pytest
from docker.models.containers import Container
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from telegram import Bot as TGBot
from telegram.ext import ContextTypes

from db.manager import DBManager
from db.models import Account, Category, Currency, Rate, UserAccount
from db.queries import AsyncQuerier

BASE_DIR = Path(__file__).parent.parent


class DBSetupError(Exception):
    pass


def run_db_container() -> Container:
    db_port = int(os.getenv("DATABASE_PORT", ""))
    db_password = os.getenv("DATABASE_PASSWORD", "")
    client = docker.from_env()
    return client.containers.run(
        "postgres:17.4",
        ports={"5432/tcp": db_port},
        environment=[f"POSTGRES_PASSWORD={db_password}"],
        detach=True,
        user="postgres",
    )


def wait_until_db_is_healthy(container: Container):
    # Didn't find approach how to use built-in healthcheck and wait until
    # container becomes healthy
    timeout = 10
    time_ts = time.time()
    while container.exec_run("pg_isready").exit_code != 0:
        time.sleep(0.1)

        if time.time() - time_ts > timeout:
            msg = "DB healthcheck takes too long"
            raise DBSetupError(msg)


def apply_migrations():
    migration_db_url = os.getenv("MIGRATION_DATABASE_URL", "")
    _ = subprocess.run(  # noqa: S603
        [
            "/usr/local/bin/dbmate",
            "--url",
            migration_db_url,
            "--migrations-dir",
            f"{BASE_DIR}/src/db/migrations",
            "migrate",
        ],
        check=True,
    )


@pytest.fixture(autouse=True, scope="session")
def db():
    container = run_db_container()

    try:
        wait_until_db_is_healthy(container)
        apply_migrations()
    except Exception:
        container.kill()
        container.remove(v=True)

    yield

    container.kill()
    container.remove(v=True)


@pytest.fixture
def db_manager(engine: AsyncEngine) -> DBManager:
    return DBManager(engine)


@pytest.fixture
def engine() -> AsyncEngine:
    db_url = os.getenv(
        "DATABASE_URL",
        "",
    )
    return create_async_engine(db_url)


@pytest.fixture
def httpx_client() -> Callable:
    def inner(response: httpx.Response) -> httpx.AsyncClient:
        return httpx.AsyncClient(
            transport=httpx.MockTransport(
                lambda request: response,  # noqa: ARG005
            ),
        )

    return inner


@pytest.fixture
def context_mock():
    context_mock = create_autospec(ContextTypes.DEFAULT_TYPE)
    context_mock.bot = create_autospec(TGBot)
    return context_mock


@pytest.fixture
def create_currency(engine: AsyncEngine) -> Callable:
    async def wrapper(name: str, iso_code: str, symbol: str) -> Currency:
        async with engine.begin() as conn:
            querier = AsyncQuerier(conn)
            currency = await querier.create_currency(
                name=name,
                iso_code=iso_code,
                symbol=symbol,
            )
            assert currency is not None
        return currency

    return wrapper


@pytest.fixture
def get_user(engine: AsyncEngine) -> Callable:
    async def wrapper(user_tg_id: int) -> UserAccount | None:
        async with engine.connect() as conn:
            querier = AsyncQuerier(conn)
            return await querier.get_user(user_tg_id=user_tg_id)

    return wrapper


@pytest.fixture
def get_accounts(engine: AsyncEngine) -> Callable:
    async def wrapper(user_id: int) -> list[Account]:
        async with engine.connect() as conn:
            querier = AsyncQuerier(conn)
            return [a async for a in querier.get_accounts(user_id=user_id)]

    return wrapper


@pytest.fixture
def get_user_categories(engine: AsyncEngine) -> Callable:
    async def wrapper(user_id: int) -> list[Category]:
        async with engine.connect() as conn:
            querier = AsyncQuerier(conn)
            return [
                c async for c in querier.get_user_categories(user_id=user_id)
            ]

    return wrapper


@pytest.fixture
def get_rate(engine: AsyncEngine) -> Callable:
    async def wrapper(from_currency_id: int, to_currency_id: int) -> Rate:
        async with engine.connect() as conn:
            querier = AsyncQuerier(conn)
            rate = await querier.get_rate(
                from_currency=from_currency_id,
                to_currency=to_currency_id,
            )
            assert rate is not None
            return rate

    return wrapper


@pytest.fixture
def get_currency(engine: AsyncEngine) -> Callable:
    async def wrapper(iso_code: str) -> Currency | None:
        async with engine.connect() as conn:
            querier = AsyncQuerier(conn)
            return await querier.get_currency(iso_code=iso_code)

    return wrapper
