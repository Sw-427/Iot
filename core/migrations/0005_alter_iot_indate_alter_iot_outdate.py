# Generated by Django 4.1.2 on 2022-10-31 09:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_alter_iot_indate_alter_iot_outdate'),
    ]

    operations = [
        migrations.AlterField(
            model_name='iot',
            name='indate',
            field=models.DateTimeField(auto_now_add=True),
        ),
        migrations.AlterField(
            model_name='iot',
            name='outdate',
            field=models.DateTimeField(auto_now_add=True),
        ),
    ]
