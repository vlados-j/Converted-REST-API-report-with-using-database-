import datetime
from models import RacerTable, ReportTable
from peewee import *

MODELS = [RacerTable, ReportTable]

test_db = SqliteDatabase(':memory:')


def setup_db():
    test_db.bind(MODELS, bind_refs=False, bind_backrefs=False)

    test_db.connect()
    test_db.create_tables(MODELS)


def tear_down_db():
    test_db.drop_tables(MODELS)
    test_db.close()


def test_RacerTable():
    setup_db()
    racer = RacerTable.create(abbreviation='SVF', name='Sebastian Vettel', team='FERRARI',
                              start_time=datetime.datetime(2018, 5, 24, 12, 2, 58, 917),
                              finish_time=datetime.datetime(2018, 5, 24, 12, 2, 3, 332),
                              lap_time=datetime.time(0, 1, 4, 415000))
    assert racer.abbreviation == 'SVF'
    assert racer.name == 'Sebastian Vettel'
    assert racer.team == 'FERRARI'
    assert racer.start_time == datetime.datetime(2018, 5, 24, 12, 2, 58, 917)
    assert racer.finish_time == datetime.datetime(2018, 5, 24, 12, 2, 3, 332)
    assert racer.lap_time == datetime.time(minute=1, second=4, microsecond=415000)
    assert racer.lap_time_str() == '1:04:415'
    tear_down_db()


def test_ReportTable():
    setup_db()
    RacerTable.create(abbreviation='SVF', name='Sebastian Vettel', team='FERRARI',
                      start_time=datetime.datetime(2018, 5, 24, 12, 2, 58, 917),
                      finish_time=datetime.datetime(2018, 5, 24, 12, 2, 3, 332),
                      lap_time=datetime.time(0, 1, 4, 415000))
    racers_report_data = ReportTable.create(abbreviation='SVF', place=1)
    assert isinstance(racers_report_data.abbreviation, RacerTable)
    assert racers_report_data.place == 1
    tear_down_db()
