from flask import Flask, request, jsonify, Response
from flask_restful import Api, Resource
from application_vlados import processing_data
from dict2xml import dict2xml
from flasgger import Swagger
from models import db, RacerTable, ReportTable
from peewee import IntegrityError
from itertools import chain

app = Flask(__name__)
api = Api(app)
swagger = Swagger(app)


def create_tables():
    with db:
        db.create_tables([RacerTable, ReportTable])


# @app.before_request
# def before_request():
#     db.connect()
#
#
# @app.after_request
# def after_request(response):
#     db.close()
#     return response


def from_files_to_db(start_path, finish_path, abbreviations_path):
    """
    The function transfer data from files directly to the database. If the data was transferred earlier, the function
    will handle the error IntegrityError, and the function won't be process anything.
    """
    try:
        structured_info = processing_data(start_path, finish_path, abbreviations_path)
        sorted_info = sorted(structured_info.values())
        number_of_valid_racers = len([None for racer in sorted_info if racer.lap_time])
        racer_number_sequence = iter(range(1, number_of_valid_racers + 1))
        for racer in sorted_info:
            driver = RacerTable.create(abbreviation=racer.abbreviation, name=racer.name, team=racer.team,
                                       start_time=racer.start_time, finish_time=racer.finish_time,
                                       lap_time=racer.lap_time)
            if racer.lap_time:
                racer.place = next(racer_number_sequence)
                ReportTable.create(abbreviation=driver, place=racer.place)
            else:
                ReportTable.create(abbreviation=driver, place=None)
    except IntegrityError:
        pass


class Report(Resource):
    def get(self):
        """
        Example endpoint returning report with the F1 racers.
        ---
        parameters:
          - name: order
            in: query
            type: string
            required: false
            description: ordering for racers in report
          - name: format
            in: query
            type: string
            required: false
            description: format of data (xml or json)
        responses:
          200:
            description: Racers report
        """
        args = request.args
        prepared_info_for_report = info_for_output(args.get("order"))
        return generate_output_data(prepared_info_for_report, args.get("format"))


class Drivers(Resource):
    def get(self):
        """
        Example endpoint returning report with the F1 racers with a possibility to execute data about particular racer
        ---
        parameters:
          - name: order
            in: query
            type: string
            required: false
            description: ordering for racers in report
          - name: format
            in: query
            type: string
            required: false
            description: format of data (xml or json)
          - name: abbreviation
            in: query
            type: string
            required: false
            description: abbreviation of the racer (SVF for example)
        responses:
          200:
            description: Racers report
        """
        args = request.args
        if args.get("abbreviation"):
            racer = RacerTable.get(RacerTable.abbreviation == args.get("abbreviation"))
            info_about_racer = {racer.name: {'name': racer.name,
                                             'team': racer.team,
                                             'lap_time': racer.lap_time.strftime("%-M:%S:%f")[:-3]
                                             if racer.lap_time else None}}
            return generate_output_data(info_about_racer, args.get("format"))
        prepared_info_for_report = info_for_output(args.get("order"))
        return generate_output_data(prepared_info_for_report, args.get("format"))


def generate_output_data(info_for_api, format_for_output):
    if format_for_output == 'xml':
        return Response(dict2xml(info_for_api, wrap="racers", indent="  "), mimetype='application/xml')
    else:
        return jsonify(info_for_api)


def info_for_output(ordering):
    query_for_valid_racers = ReportTable.select().join(RacerTable).where(RacerTable.lap_time != None)
    if ordering == 'desc':
        query_for_valid_racers = query_for_valid_racers.order_by(ReportTable.place.desc())
    query_for_other_racers = ReportTable.select().join(RacerTable).where(RacerTable.lap_time == None)
    info_for_api = [
        {racer.abbreviation.name: {'place': racer.place,
                                   'name': racer.abbreviation.name,
                                   'team': racer.abbreviation.team,
                                   'lap_time': racer.abbreviation.lap_time_str()}}
        for racer in chain(query_for_valid_racers, query_for_other_racers)
    ]
    return info_for_api


api.add_resource(Report, '/api/v1/report/')
api.add_resource(Drivers, '/api/v1/report/drivers/')

if __name__ == '__main__':
    create_tables()
    from_files_to_db('files/start.log', 'files/end.log', 'files/abbreviations.txt')
    app.run(debug=True)
