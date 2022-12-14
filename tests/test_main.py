import pytest
from application_vlados import Racer
import datetime
from unittest.mock import patch
from main import info_for_output, from_files_to_db, generate_output_data, app
from models import ReportTable, RacerTable
from peewee import *
from flask import Response

MODELS = [RacerTable, ReportTable]

test_db = SqliteDatabase(':memory:')


def setup_db():
    test_db.bind(MODELS, bind_refs=False, bind_backrefs=False)

    test_db.connect()
    test_db.create_tables(MODELS)


def tear_down_db():
    test_db.drop_tables(MODELS)
    test_db.close()


@patch('main.processing_data')
def test_from_files_to_db(mocked_processing_data):
    setup_db()
    mocked_processing_data.return_value = {'Sebastian Vettel':
                                               Racer('Sebastian Vettel', 'SVF', 'FERRARI',
                                                     datetime.datetime(2018, 5, 24, 12, 2, 58, 917),
                                                     datetime.datetime(2018, 5, 24, 12, 4, 3, 332)),
                                           'Daniel Ricciardo':
                                               Racer('Daniel Ricciardo', 'DRR', 'RED BULL RACING TAG HEUER',
                                                     datetime.datetime(2018, 5, 24, 12, 14, 12, 54),
                                                     datetime.datetime(2018, 5, 24, 12, 11, 24, 67))}
    from_files_to_db('fake/file/path', 'fake/file/path', 'fake/file/path')
    assert RacerTable.get(RacerTable.abbreviation == 'SVF').name == 'Sebastian Vettel'
    tear_down_db()


def test_generate_output_data_with_xml():
    info_for_api = [
        {'Sebastian Vettel': {'lap_time': '1:04:415',
                              'name': 'Sebastian Vettel',
                              'place': 1,
                              'team': 'FERRARI'}},
        {'Valtteri Bottas': {'lap_time': '1:12:434',
                             'name': 'Valtteri Bottas',
                             'place': 2,
                             'team': 'MERCEDES'}}
    ]
    actual_output = generate_output_data(info_for_api, 'xml')
    assert isinstance(actual_output, Response)
    assert actual_output.status_code == 200
    assert actual_output.mimetype == 'application/xml'
    assert actual_output.data == (b'<racers>\n  <Sebastian_Vettel>\n    <lap_time>1:04:415</lap_time>\n    '
                                  b'<name>Sebastian Vettel</name>\n    <place>1</place>\n    <team>FERRARI</team>\n  '
                                  b'</Sebastian_Vettel>\n</racers>\n<racers>\n  <Valtteri_Bottas>\n    '
                                  b'<lap_time>1:12:434</lap_time>\n    <name>Valtteri Bottas</name>\n    '
                                  b'<place>2</place>\n    <team>MERCEDES</team>\n  </Valtteri_Bottas>\n</racers>')


def test_generate_output_data_with_json():
    info_for_api = [
        {'Sebastian Vettel': {'lap_time': '1:04:415',
                              'name': 'Sebastian Vettel',
                              'place': 1,
                              'team': 'FERRARI'}},
        {'Valtteri Bottas': {'lap_time': '1:12:434',
                             'name': 'Valtteri Bottas',
                             'place': 2,
                             'team': 'MERCEDES'}}
    ]
    with app.app_context():
        actual_output = generate_output_data(info_for_api, 'json')
        assert isinstance(actual_output, Response)
        assert actual_output.status_code == 200
        assert actual_output.mimetype == 'application/json'
        assert actual_output.data == b'[{"Sebastian Vettel":{"lap_time":"1:04:415","name":"Sebastian Vettel",' \
                                     b'"place":1,"team":"FERRARI"}},{"Valtteri Bottas":{"lap_time":"1:12:434",' \
                                     b'"name":"Valtteri Bottas","place":2,"team":"MERCEDES"}}]\n'


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


@pytest.mark.parametrize("path, expected_output", [('/api/v1/report/', b'[{"Sebastian Vettel":{"lap_time":"1:04:415",'
                                                                       b'"name":"Sebastian Vettel","place":1,'
                                                                       b'"team":"FERRARI"}},'
                                                                       b'{"Valtteri Bottas":{"lap_time":"1:12:434",'
                                                                       b'"name":"Valtteri Bottas","place":2,'
                                                                       b'"team":"MERCEDES"}}]\n'),
                                                   ('/api/v1/report/?order=desc', b'[{"Valtteri Bottas":{'
                                                                                  b'"lap_time":"1:12:434",'
                                                                                  b'"name":"Valtteri Bottas",'
                                                                                  b'"place":2,"team":"MERCEDES"}},'
                                                                                  b'{"Sebastian Vettel":{'
                                                                                  b'"lap_time":"1:04:415","name":'
                                                                                  b'"Sebastian Vettel","place":1,'
                                                                                  b'"team":"FERRARI"}}]\n'),
                                                   ('/api/v1/report/?order=desc&format=xml', b'<racers>\n  <Valtteri_Bo'
                                                                                             b'ttas>\n    <lap_time>1:1'
                                                                                             b'2:434</lap_time>\n    <'
                                                                                             b'name>Valtteri Bottas</na'
                                                                                             b'me>\n    <place>2</plac'
                                                                                             b'e>\n    <team>MERCEDES<'
                                                                                             b'/team>\n  </Valtteri_Bot'
                                                                                             b'tas>\n</racers>\n<racers'
                                                                                             b'>\n  <Sebastian_Vettel>'
                                                                                             b'\n    <lap_time>1:04:415'
                                                                                             b'</lap_time>\n    <name>S'
                                                                                             b'ebastian Vettel</name>\n'
                                                                                             b'    <place>1</place>\n  '
                                                                                             b'  <team>FERRARI</team>\n'
                                                                                             b'  </Sebastian_Vettel>\n'
                                                                                             b'</racers>'),
                                                   ('/api/v1/report/?order=desc&format=json', b'[{"Valtteri Bottas":{"'
                                                                                              b'lap_time":"1:12:434","n'
                                                                                              b'ame":"Valtteri Bottas",'
                                                                                              b'"place":2,"team":"MERC'
                                                                                              b'EDES"}},{"Sebastian Ve'
                                                                                              b'ttel":{"lap_time":"1:04'
                                                                                              b':415","name":"Sebastian'
                                                                                              b' Vettel","place":1,"tea'
                                                                                              b'm":"FERRARI"}}]\n')])
def test_report(client, path, expected_output):
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
    response = client.get(path)
    assert response.status_code == 200
    assert response.data == expected_output
    tear_down_db()


@pytest.mark.parametrize("path, expected_output",
                         [('/api/v1/report/drivers/', b'[{"Sebastian Vettel":{"lap_time":"1:04:415","name":"Sebastian '
                                                      b'Vettel","place":1,"team":"FERRARI"}},{"Valtteri Bottas":{"lap_t'
                                                      b'ime":"1:12:434","name":"Valtteri Bottas","place":2,"team":"MER'
                                                      b'CEDES"}}]\n'),
                          ('/api/v1/report/drivers/?abbreviation=SVF', b'{"Sebastian Vettel":{"lap_time":"1:04:415",'
                                                                       b'"name":"Sebastian Vettel","team":"FERRARI"}}\n'),
                          ('/api/v1/report/drivers/?abbreviation=SVF&format=xml', b'<racers>\n  <Sebastian_Vettel>\n   '
                                                                                  b' <lap_time>1:04:415</lap_time>\n   '
                                                                                  b' <name>Sebastian Vettel</name>\n   '
                                                                                  b' <team>FERRARI</team>\n  </Sebastia'
                                                                                  b'n_Vettel>\n</racers>'),
                          ('/api/v1/report/drivers/?abbreviation=SVF&format=json', b'{"Sebastian Vettel":{"lap_time":'
                                                                                   b'"1:04:415","name":"Sebastian Vett'
                                                                                   b'el","team":"FERRARI"}}\n')])
def test_drivers(client, path, expected_output):
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
    response = client.get(path)
    assert response.status_code == 200
    assert response.data == expected_output
    tear_down_db()
