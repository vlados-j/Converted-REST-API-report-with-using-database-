from peewee import *
import datetime


db = SqliteDatabase('database.db')


class BaseModel(Model):
    class Meta:
        database = db


class RacerTable(BaseModel):
    abbreviation = CharField(unique=True, primary_key=True)
    name = CharField()
    team = CharField()
    start_time = DateTimeField()
    finish_time = DateTimeField()
    lap_time = TimeField(null=True)

    class Meta:
        db_table = 'Racers'

    def lap_time_str(self):
        return self.lap_time.strftime("%-M:%S:%f")[:-3] if self.lap_time else '-'


class ReportTable(BaseModel):
    abbreviation = ForeignKeyField(RacerTable, backref='report', unique=True, primary_key=True)
    place = IntegerField(null=True)

    class Meta:
        db_table = 'Report'
