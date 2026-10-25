import peewee
import datetime

db = peewee.SqliteDatabase('history.db')

class History(peewee.Model):

    user_id = peewee.IntegerField()
    command = peewee.CharField()
    year = peewee.CharField()
    rating = peewee.CharField()
    genres = peewee.CharField()
    poster = peewee.CharField()
    query = peewee.CharField()
    result = peewee.CharField()
    created_at = peewee.DateTimeField(default=datetime.datetime.now)

    class Meta:
        database = db

db.connect()
db.create_tables([History], safe=True)