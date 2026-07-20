from typing import Any, Sequence, Mapping
from dotenv import load_dotenv
from sqlalchemy import Engine, Row, Table, create_engine, text, insert
from os import getenv

load_dotenv()


class MissingEnvironmentError(Exception):
    pass


_engine = None


def _create_engine() -> Engine:
    url = getenv("DATABASE_URL")
    if url:
        return create_engine(str(url))
    raise MissingEnvironmentError("DATABASE_URL is not defined in .env file")


def get_engine() -> Engine:
    global _engine
    if _engine is None:
        _engine = _create_engine()
    return _engine


def execute_statement(
    statement: str, params: Mapping[str, Any] = {}, engine: Engine = get_engine()
) -> None:
    """Function to allow execution of statements that do not return any results
    such as create and insert"""
    with engine.connect() as conn:
        conn.execute(text(statement), params)
        conn.commit()


def execute_query(
    query: str, params: Mapping[str, Any] = {}, engine: Engine = get_engine()
) -> Sequence[Row[Any]]:
    """Funciton to allow execution of queries that return results"""
    with engine.connect() as conn:
        data = conn.execute(text(query), params)
        return data.fetchall()


def execute_bulk_insert(
    table: Table, values: list[dict[str, Any]], engine: Engine = get_engine()
) -> None:
    with engine.begin() as conn:
        conn.execute(insert(table), values)
