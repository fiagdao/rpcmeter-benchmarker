from peewee import *
import os

HOST=os.environ["POSTGRES_HOST"]
DATABASE=os.environ["POSTGRES_DATABASE"]
USER=os.environ["POSTGRES_USER"]
PORT=os.environ["POSTGRES_PORT"]
PASSWORD=os.environ["POSTGRES_PASSWORD"]
REGION=os.environ["REGION"]

db = PostgresqlDatabase(DATABASE, user=USER, port=PORT, password=PASSWORD, host=HOST)

class Region(Model):
    name = CharField()
    code = CharField()

    class Meta:
        database=db

class Chain(Model):
    name = CharField()
    chain_id = CharField()

    class Meta:
        database = db


class Provider(Model):
    name = CharField()
    url = CharField()
    symbol = CharField()
    chain = ForeignKeyField(Chain, backref="chain")

    class Meta:
        database = db


class Benchmark(Model):
    provider = ForeignKeyField(Provider, backref="provider")
    timestamp = DateTimeField()
    p25 = FloatField()
    p50 = FloatField()
    p75 = FloatField()
    p90 = FloatField()
    p99 = FloatField()
    mean = FloatField()

    region = ForeignKeyField(Region, backref="region")

    class Meta:
        database = db


db.connect()
db.create_tables([Region, Chain, Provider, Benchmark])

# if REGION does not exist, create it
if not Region.select().where(Region.name==REGION).exists():
    region_code = REGION[:3]
    Region.create(name=REGION, code=region_code)
