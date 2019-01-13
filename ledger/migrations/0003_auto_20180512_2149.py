# Generated by Django 2.0.4 on 2018-05-12 21:49

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('ledger', '0002_auto_20180512_2139'),
    ]

    operations = [
        migrations.AlterField(
            model_name='transfer',
            name='statement_position',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, related_name='transfers', to='ledger.StatementRow'),
        ),
    ]