# -*- coding:utf-8 -*-
from peewee import *

db = SqliteDatabase('db.sqlite')


class EmailsData(Model):
    id = PrimaryKeyField()
    email = CharField(max_length=50)

    class Meta:
        database = db
        table_name = 'emails_data'


file = open('source/26550766.txt', 'r', encoding='utf-8')
r = open('source/2600w.txt', 'a+', encoding='utf-8')
temp = 1
for line in file:
    r.write(line.replace('qq.com\n', '@qq.com\n'))
    print(temp)
    temp += 1
