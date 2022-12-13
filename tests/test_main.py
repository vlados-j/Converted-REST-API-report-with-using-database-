import pytest
from application_vlados import Racer
import datetime
from unittest.mock import patch
from main import info_for_output, from_files_to_db
from models import ReportTable, RacerTable
from peewee import *

"""
The list of test functions:
from_files_to_db<<<<<<<<<<<<<<<<
Report
Drivers
generate_output_data
create_tables
"""

MODELS = [RacerTable, ReportTable]

test_db = SqliteDatabase(':memory:')


# @pytest.fixture(autouse=True, scope='session')
def setup_db():
    test_db.bind(MODELS, bind_refs=False, bind_backrefs=False)

    test_db.connect()
    test_db.create_tables(MODELS)


def tear_down_db():
    test_db.drop_tables(MODELS)
    test_db.close()


@pytest.fixture()
def client():
    from main import app
    app.config['TESTING'] = True
    return app.test_client()


@patch('main.processing_data')
def test_from_files_to_db(mocked_processing_data):
    setup_db()
    mocked_processing_data.return_value = {'Sebastian Vettel':
                                               Racer('Sebastian Vettel', 'SVF', 'FERRARI',
                                                     datetime.datetime(2018, 5, 24, 12, 2, 58, 917),
                                                     datetime.datetime(2018, 5, 24, 12, 4, 3, 332)),
                                           'Daniel Ricciardo':
                                               Racer('Daniel Ricciardo', 'DRR', 'RED BULL RACING TAG HEUER', None,
                                                     None)}
    from_files_to_db('fake/file/path', 'fake/file/path', 'fake/file/path')
    RacerTable.create(abbreviation='QWE', name='SSSebastian Vettel', team='FERRARI',
                      start_time=datetime.datetime(2018, 5, 24, 12, 2, 58, 917),
                      finish_time=datetime.datetime(2018, 5, 24, 12, 2, 3, 332),
                      lap_time=datetime.time(0, 1, 4, 415000))
    assert RacerTable.get(RacerTable.abbreviation == 'QWEe').name == 'SSSebastian Vettel'
    tear_down_db()


def test_report():
    pass


def test_drivers():
    pass


def test_generate_output_data():
    pass


@pytest.mark.parametrize("ordering, expected_result", [('desc', [{'Valtteri Bottas': {'lap_time': '1:12:434',
                                                                                      'name': 'Valtteri Bottas',
                                                                                      'place': 2,
                                                                                      'team': 'MERCEDES'}},
                                                                 {'Sebastian Vettel': {'lap_time': '1:04:415',
                                                                                       'name': 'Sebastian Vettel',
                                                                                       'place': 1,
                                                                                       'team': 'FERRARI'}}]),
                                                       ('asc', [{'Sebastian Vettel': {'lap_time': '1:04:415',
                                                                                      'name': 'Sebastian Vettel',
                                                                                      'place': 1,
                                                                                      'team': 'FERRARI'}},
                                                                {'Valtteri Bottas': {'lap_time': '1:12:434',
                                                                                     'name': 'Valtteri Bottas',
                                                                                     'place': 2,
                                                                                     'team': 'MERCEDES'}}]),
                                                       ('', [{'Sebastian Vettel': {'lap_time': '1:04:415',
                                                                                   'name': 'Sebastian Vettel',
                                                                                   'place': 1,
                                                                                   'team': 'FERRARI'}},
                                                             {'Valtteri Bottas': {'lap_time': '1:12:434',
                                                                                  'name': 'Valtteri Bottas',
                                                                                  'place': 2,
                                                                                  'team': 'MERCEDES'}}])])
def test_info_for_output(ordering, expected_result):
    setup_db()
    RacerTable.create(abbreviation='SVF', name='Sebastian Vettel', team='FERRARI',
                      start_time=datetime.datetime(2018, 5, 24, 12, 2, 58, 917),
                      finish_time=datetime.datetime(2018, 5, 24, 12, 2, 3, 332),
                      lap_time=datetime.time(0, 1, 4, 415000))
    RacerTable.create(abbreviation='VBM', name='Valtteri Bottas', team='MERCEDES',
                      start_time=datetime.datetime(2018, 5, 24, 12),
                      finish_time=datetime.datetime(2018, 5, 24, 12, 1, 12, 434),
                      lap_time=datetime.time(0, 1, 12, 434000))
    ReportTable.create(abbreviation='SVF', place=1)
    ReportTable.create(abbreviation='VBM', place=2)
    assert info_for_output(ordering) == expected_result
    tear_down_db()


def test_create_tables():
    pass
