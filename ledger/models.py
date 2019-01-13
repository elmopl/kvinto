from django.db import models
from django.db.models import Sum

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
    number = models.CharField(max_length=50, null=True)
    open_date = models.DateTimeField(null=True)
    close_date = models.DateTimeField(null=True)

    @property
    def full_name(self):
        return '{} - {}'.format(self.owner.name, self.name)

    def __str__(self):
        return '{} [{}]'.format(self.name, self.currency)

    def balance(self, date):
        return self.statements.filter(date__lte = date).aggregate(Sum('rows__amount'))['rows__amount__sum']

class Statement(models.Model):
    class Meta:
        ordering = ['-date']
    account = models.ForeignKey(Account, on_delete=models.PROTECT, related_name='statements')
    source = models.FileField(upload_to=statement_upload_filename)
    date = models.DateField()

    @property
    def closing_balance(self):
        return self.account.balance(self.date)

class StatementRow(models.Model):
    statement = models.ForeignKey(Statement, on_delete=models.CASCADE, related_name='rows')
    name = models.CharField(max_length=250)
    amount = models.IntegerField()
    transaction_date = models.DateField()
    billing_date = models.DateField()

class TransactionGroup(models.Model):
    created = models.DateTimeField(auto_now=True)
    settled = models.DateTimeField(null=True)
    reference = models.CharField(max_length=20, unique=True)
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

    @property
    def groups(self):
        group_ids = [
            item.group.id
            for item in self.items.all()
            if item.group is not None
        ]
        return TransactionGroup.objects.filter(id__in = group_ids).distinct()

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


