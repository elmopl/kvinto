# Generated by Django 2.0.4 on 2018-05-12 21:39

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ledger', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='transferparticipant',
            old_name='item',
            new_name='transfer',
        ),
    ]
