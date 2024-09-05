"""A simple muid key server supports registering a key and fetching key
that hasn't been used by anybody before
"""

import http
import logging as log
import os
import sys

import databases
import muid
import sqlalchemy
from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel

MIN_DIFFICULTY = 9
DEFAULT_FORMAT = '%(asctime)s.%(msecs)03d %(levelname)s %(name)s::%(funcName)s: %(message)s'

log.basicConfig(stream=sys.stderr, level=log.INFO,
                format=DEFAULT_FORMAT )


DATABASE_URL = "sqlite:///./keys.db"

database = databases.Database(DATABASE_URL)

metadata = sqlalchemy.MetaData()

keys_tbl = sqlalchemy.Table(
    "keys",
    metadata,
    sqlalchemy.Column("key", sqlalchemy.String, primary_key=True),
    sqlalchemy.Column("difficulty", sqlalchemy.Integer, nullable=False),
    sqlalchemy.Column("hash", sqlalchemy.String, nullable=False),
    sqlalchemy.Column("animal", sqlalchemy.String, nullable=False),
    sqlalchemy.Column("used_by", sqlalchemy.String),
)


engine = sqlalchemy.create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False},
)

metadata.create_all(engine)
# %%


class Key(BaseModel):
    """a key as provided to /keys/save endpoint"""

    key: str


app = FastAPI()


@app.on_event("startup")
async def _startup():
    log.info(f'Connectiing to db: {DATABASE_URL}: pwd: {os.getcwd()}')
    await database.connect()


@app.on_event("shutdown")
async def _shutdown():
    await database.disconnect()


@app.get("/keys")
async def _all_keys():
    query = keys_tbl.select()
    return await database.fetch_all(query)


@app.get("/keys.txt")
async def _all_keys(difficulty: int = None):
    query = keys_tbl.select()
    recs = await database.fetch_all(query)
    result = []
    for rec in recs:
        dic = dict( rec )
        if difficulty is not None and dic['difficulty'] != difficulty:
            continue
        result.append( f"{dic['animal']:17s} | {dic['difficulty']:2d} | {dic['key']}" )

    return Response( "\n".join( result ), media_type="text/plain" )


# @app.get("/drop_keys_tbl")
# async def _drop_keys_tbl():
#    query = "drop table if exists keys"
#    await database.execute(query)
#    return "OK"


@app.get("/keys_tbl_def")
async def _keys_tbl_def():
    return await database.fetch_all("""
        SELECT sql
        FROM sqlite_master
        WHERE name = 'keys'
    """)


@app.post("/keys/save")
async def _save_key(key_obj: Key):
    log.info(f"key_obj: {key_obj}")
    return await _save_key0(key_obj.key)


@app.get("/keys/save/{key}")
async def _save_key0(key: str):
    await _validate( key )

    query = _save_query(key)
    # log.info(f'\n{query}')
    # last_record_id = await database.execute(query)
    await database.execute(query)

    return await database.fetch_one( "select * from keys where key=:key", values={'key': key} )

    # return {**key_obj.dict(), "id": last_record_id}


@app.get("/keys/unused_report")
async def _unused_report():
    query = """select
                    difficulty,
                    count(*) as cnt
               from keys group by difficulty"""

    recs = await database.fetch_all(query)

    by_diff = []
    for rec in recs:
        dic = dict( rec )
        dic['budget'] = dic['cnt'] * 16 ** (dic['difficulty'] - 9)
        by_diff.append(dic)

    total_budget = sum( dic['budget'] for dic in by_diff )

    return dict(total_budget=total_budget, by_difficulty=by_diff)


@app.get("/keys/purge_by_diff")
async def _purge_by_diff(min_diff: int):
    query = f"""delete from keys where difficulty < {min_diff}"""
    return await database.execute(query)


async def _validate( key: str):
    if not muid.validate( key ):
        raise HTTPException( status_code=http.HTTPStatus.BAD_REQUEST, detail='Invalid key' )

    record = await database.fetch_one("select * from keys where key=:key", values={'key': key})

    if record is not None:
        raise HTTPException( status_code=http.HTTPStatus.ALREADY_REPORTED,
                             detail=f'key already in db: {record}' )


def _save_query(key: str) -> str:
    key_bytes = key.encode('ascii')
    difficulty = muid.difficulty(key)

    if difficulty < MIN_DIFFICULTY:
        detail = f'key is of difficulty {difficulty} < MIN_DIFFICULTY={MIN_DIFFICULTY}'
        raise HTTPException( http.HTTPStatus.EXPECTATION_FAILED, detail=detail )

    bhash = muid.bhash( key_bytes ).decode('ascii')
    animal = muid.animal(key_bytes )

    log.info(f"bhash={bhash!r}, difficulty={difficulty!r}, animal={animal!r}")

    query = keys_tbl.insert().values(key=key, difficulty=difficulty, hash=bhash,
                                     animal=animal, used_by=None)
    return query


@app.get("/key")
async def _get_key(client_name: str, difficulty: int):
    query = "select * from keys where used_by is null and difficulty=:diff"
    record = await database.fetch_one(query, values={'diff': difficulty})
    key_found = record['key']
    log.info(f"{record}")

    update = "update keys set used_by=:client_name where key = :key"
    log.info(f'update={update}')

    await database.execute( update, values=dict(client_name=client_name, key=key_found))

    final_query = "select * from keys where key=:key"
    record2 = await database.fetch_one(final_query, values={'key': key_found})

    return record2

# @app.get("/key")
# def get_key(client_name: str):
