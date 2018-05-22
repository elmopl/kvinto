from ..models import Account
from ..models import Transaction
from ..models import Transfer
from ..models import TransactionGroup
from ..models import TransferItem
from ..models import TransferItemParticipant
from ..models import Person
from ..models import StatementRow

from .widgets import LedgerWidget

from datetime import date

from django import forms
from django.shortcuts import render
from django.shortcuts import redirect
from django.urls import reverse
from django.http import JsonResponse
from django.db import transaction

import json

class MultipleTransactionWidget(LedgerWidget):
    template_name = 'transaction_widget.html'

class TransactionForm(forms.Form):
    transaction_id = forms.IntegerField(widget=forms.HiddenInput())
    name = forms.CharField()
    transfers = forms.models.ModelMultipleChoiceField(
        queryset=Transfer.objects.all(),
        widget=MultipleTransactionWidget,
    )

def _populate_transaction(trns, data):
    trns.name = data['name']
    trns.date = date.today()
    trns.save()
    for transfer_info in data['transfers']:
        row = None
        row_id = transfer_info.get('statement_row')
        if row_id is not None:
            row = StatementRow.objects.get(id=row_id)
        transfer = Transfer(
            transaction = trns,
            source = Account.objects.get(id=transfer_info['source_account']['id']),
            destination = Account.objects.get(id=transfer_info['destination_account']['id']),
            statement_position = row
        )
        transfer.save()
        for item_info in transfer_info['items']:
            item = TransferItem(
                name = item_info['name'],
                source_amount = item_info['source_amount'],
                destination_amount = item_info['destination_amount'],
            )
            item.transfer = transfer
            group_id = item_info.get('group', {}).get('id')
            if group_id is not None:
                group = TransactionGroup.objects.get(id=group_id)
                item.group = group
            item.save()
            for participant_info in item_info['participants']:
                participant = TransferItemParticipant()
                participant.transfer_item = item
                participant.person = Person.objects.get(id=participant_info['id'])
                participant.weight = participant_info['weight']
                participant.transfer = transfer
                participant.save()

def save(request):
    data = json.loads(request.body)
    with transaction.atomic():
        trns = Transaction.objects.get(id=data['id'])
        trns.transfers.all().delete()
        _populate_transaction(trns, data)

    return JsonResponse({
        'id': trns.id,
        'edit_url': reverse('edit_transaction', args=[trns.id]),
    })


def _show_form(request, url, data=None):
    form = TransactionForm()
    context = {
        'transaction_form': form,
        'action_url': url,
        'data': data or {},
    }
    return render(request, 'transaction.html', context)

def edit(request, transaction_id):
    trns = Transaction.objects.get(id=transaction_id)
    data = {
        'name': trns.name,
        'id': trns.id,
        'transfers': [
            {
                'statement_row': transfer.statement_position and transfer.statement_position.id,
                'id': transfer.id,
                'source_account': {
                    'id': transfer.source.id,
                    'name': transfer.source.name,
                },
                'destination_account': {
                    'id': transfer.destination.id,
                    'name': transfer.destination.name,
                },
                'items': [
                    {
                        'name': item.name,
                        'source_amount': item.source_amount,
                        'destination_amount': item.destination_amount,
                        'group': {
                            'id': item.group and item.group.id,
                            'name': item.group and item.group.name,
                        },
                        'participants': [
                            {
                                'id': participant.person.id,
                                'name': participant.person.name,
                                'weight': participant.weight,
                            }
                            for participant in item.participants.all()
                        ]
                    }
                    for item in transfer.items.all()
                ]
            }
            for transfer in trns.transfers.all()
        ]
    }
    return _show_form(request, reverse('save_transaction'), data)

def create(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        with transaction.atomic():
            trns = Transaction()
            _populate_transaction(trns, data)
        return JsonResponse({
            'id': trns.id,
            'edit_url': reverse('edit_transaction', args=[trns.id]),
        })
    else:
        return _show_form(request, reverse('create_transaction'))

def create_for_statement_item(request, statement_row_id):
    info = StatementRow.objects.get(id=statement_row_id)
    data = {
        'name': info.name,
        'transfers': [
            {
                'statement_row': info.id,
                'source_account': {
                    'id': info.statement.account.id,
                    'name': info.statement.account.name,
                },
                'items': [
                    {
                        'name': info.name,
                        'source_amount': -info.amount,
                        'destination_amount': -info.amount,
                        'group': {
                            'id': info.group and info.group.id,
                            'name': info.group and info.group.name,
                        },
                        'participants': [
                            {
                                'weight': 1,
                                'id': info.statement.account.owner.id,
                                'name': info.statement.account.owner.name,
                            },
                        ]
                    },
                ]
            }
        ],
    }
    return _show_form(request, reverse('create_transaction'), data)

def view(request, transaction_id):
    form = TransactionForm()
    context = {
        'transaction_form': form,
    }
    return render(request, 'transaction.html', context)

def list_transactions(request):
    transactions = Transaction.objects.all().order_by('date')
    context = {
        'transactions': transactions,
    }
    return render(request, 'transactions.html', context)


def transactions_match(request):
    query = json.loads(request.body)
    
    transactions = Transaction.objects.filter(name__contains=query['name'])
    return JsonResponse({
        'matches': [
            {
                'id': trns.id,
                'name': trns.name,
                'date': trns.date,
            }
            for trns in transactions
        ]
    })

