from django.db import models

def statement_upload_filename(instance, filename):
    return 'statements/user_{}/account_{}/{}'.format(
        instance.account.owner.id,
        instance.account.id,
        filename
    )

class Person(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Account(models.Model):
    owner = models.ForeignKey(Person, on_delete=models.PROTECT)
    name = models.CharField(max_length=100)
    currency = models.CharField(max_length=10)

    def __str__(self):
        return '{} [{}]'.format(self.name, self.currency)

class Statement(models.Model):
    account = models.ForeignKey(Account, on_delete=models.PROTECT, related_name='statements')
    source = models.FileField(upload_to=statement_upload_filename)
    date = models.DateField()

class StatementRow(models.Model):
    statement = models.ForeignKey(Statement, on_delete=models.CASCADE, related_name='rows')
    name = models.CharField(max_length=250)
    amount = models.IntegerField()
    transaction_date = models.DateField()
    billing_date = models.DateField()

class TransactionGroup(models.Model):
    created = models.DateTimeField(auto_now=True)
    name = models.CharField(max_length=150)

class Transaction(models.Model):
    name = models.CharField(max_length=100)
    date = models.DateField()

class Transfer(models.Model):
    transaction = models.ForeignKey(
        Transaction,
        on_delete=models.PROTECT,
        related_name='transfers'
    )
    source = models.ForeignKey(
        Account,
        on_delete=models.PROTECT,
        related_name='out_transfers',
        blank=False,
        null=False,
    )
    destination = models.ForeignKey(
        Account,
        on_delete=models.PROTECT,
        related_name='in_transfers',
        blank=False,
        null=False,
    )
    statement_position = models.OneToOneField(
        StatementRow,
        on_delete=models.PROTECT,
        related_name='transfer',
        null=True
    )

class TransferItem(models.Model):
    group = models.ForeignKey(
        TransactionGroup,
        blank=True,
        null=True,
        on_delete=models.PROTECT,
        related_name='transfer_items',
    )
    name = models.CharField(max_length=100)
    transfer = models.ForeignKey(
        Transfer,
        on_delete=models.CASCADE,
        related_name='items',
        blank=False,
        null=False,
    )
    source_amount = models.IntegerField()
    destination_amount = models.IntegerField()

class TransferItemParticipant(models.Model):
    transfer_item = models.ForeignKey(
        TransferItem,
        related_name='participants',
        on_delete=models.CASCADE,
        blank=False,
        null=False,
    )
    person = models.ForeignKey(
        Person,
        related_name='transfers',
        on_delete=models.PROTECT,
        blank=False,
        null=False,
    )
    weight = models.IntegerField(default=1)


