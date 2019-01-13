# Generated by Django 2.0.4 on 2018-05-12 21:16

from django.db import migrations, models
import django.db.models.deletion
import ledger.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Account',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('currency', models.CharField(max_length=10)),
            ],
        ),
        migrations.CreateModel(
            name='Person',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name='Statement',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('source', models.FileField(upload_to=ledger.models.statement_upload_filename)),
                ('date', models.DateField()),
                ('account', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='statements', to='ledger.Account')),
            ],
        ),
        migrations.CreateModel(
            name='StatementRow',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=250)),
                ('amount', models.IntegerField()),
                ('transaction_date', models.DateField()),
                ('billing_date', models.DateField()),
                ('statement', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='rows', to='ledger.Statement')),
            ],
        ),
        migrations.CreateModel(
            name='Transaction',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('date', models.DateField()),
            ],
        ),
        migrations.CreateModel(
            name='TransactionGroup',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=150)),
            ],
        ),
        migrations.CreateModel(
            name='Transfer',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('source_amount', models.IntegerField()),
                ('destination_amount', models.IntegerField()),
                ('destination', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='in_transfers', to='ledger.Account')),
                ('source', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='out_transfers', to='ledger.Account')),
                ('statement_position', models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, related_name='transfer', to='ledger.StatementRow')),
                ('transaction', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='ledger.Transaction')),
            ],
        ),
        migrations.CreateModel(
            name='TransferParticipant',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('weight', models.IntegerField(default=1)),
                ('item', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='participants', to='ledger.Transfer')),
                ('person', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='transfer_items', to='ledger.Person')),
            ],
        ),
        migrations.AddField(
            model_name='transaction',
            name='group',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='ledger.TransactionGroup'),
        ),
        migrations.AddField(
            model_name='account',
            name='owner',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='ledger.Person'),
        ),
    ]