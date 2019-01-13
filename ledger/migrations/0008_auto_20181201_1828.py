# Generated by Django 2.0.4 on 2018-12-01 18:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ledger', '0007_transactiongroup_reference'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='statement',
            options={'ordering': ['-date']},
        ),
        migrations.AddField(
            model_name='transactiongroup',
            name='settled',
            field=models.DateTimeField(null=True),
        ),
    ]
