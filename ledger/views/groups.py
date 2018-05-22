from ..models import Account
from ..models import Transaction
from ..models import Transfer
from ..models import TransferItemParticipant
from ..models import TransactionGroup
from ..models import Person
from ..models import StatementRow

from datetime import date

from django import forms
from django.shortcuts import render
from django.shortcuts import redirect
from django.urls import reverse
from django.http import JsonResponse
from django.db import transaction
from django.db.models import Sum
from django.db.models import Count

import json

def edit(request, group_id):
    group = TransactionGroup.objects.get(id=group_id)
    data = {
        'name': group.name,
        'id': group.id,
        'transactions': [
            {
                'name': transaction.name + ' @ ' + str(transaction.date),
                'id': transaction.id,
            }
            for transaction in group.transactions.all()
        ]
    }

    return _show_form(request, reverse('save_group'), data)

def save(request):
    data = json.loads(request.body)
    with transaction.atomic():
        group = TransactionGroup.objects.get(id=data['id'])
        group.transactions.clear()
        _populate_group(group, data)

    return JsonResponse({
        'id': group.id,
        'edit_url': reverse('edit_group', args=[group.id]),
    })

def list(request):
    context = {
        'groups': TransactionGroup.objects.all().order_by('created'),
    }
    return render(request, 'groups_list.html', context)


def summary(request, group_id):
    group = TransactionGroup.objects.get(id=group_id)
    items = group.transfer_items.all()

    participants = TransferItemParticipant.objects.filter(transfer_item__group = group)
    persons = Person.objects.filter(transfers__in = participants).distinct().order_by('name')

    def calculate_cost(person, item):
        paid_in = 0
        if item.transfer.source.owner == person:
            paid_in = item.source_amount

        total_weight = sum(ip.weight for ip in item.participants.all())
        participated = item.participants.filter(person = person).first()
        gained = 0
        if participated:
            gained = item.source_amount * participated.weight / total_weight

        return round(gained, 2), paid_in or 0 

    costs = {
        item: {
            person: calculate_cost(person, item)
            for person in persons
        }
        for item in items
    }

    totals = {
        person: sum(
            item_cost[person][0] - item_cost[person][1]
            for item_cost in costs.values()
        )
        for person in persons
    }

    context = {
        'persons': persons,
        'group': group,
        'costs': [
            [
                item,
                [
                    item_persons[person]
                    for person in persons
                ]
            ]
            for item, item_persons in costs.items()
        ],
        'totals': [
            totals[person]
            for person in persons
        ]
    }
    return render(request, 'group_summary.html', context)

def _show_form(request, url, data):
    context = {
        'action_url': url,
        'data': data,
    }
    return render(request, 'group_form.html', context)

def _populate_group(group, data):
    group.name = data['name']
    group.save()
    for transaction_info in data['transactions']:
        transaction = Transaction.objects.get(id=transaction_info['id'])
        transaction.group = group
        transaction.save()

def create(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        with transaction.atomic():
            group = TransactionGroup()
            _populate_group(group, data)
        return JsonResponse({
            'id': group.id,
            'edit_url': reverse('edit_group', args=[group.id]),
        })
    else:
        return _show_form(request, reverse('create_group'), {})


def groups_match(request):
    query = json.loads(request.body)
    
    groups = TransactionGroup.objects.filter(name__contains=query['name'])
    return JsonResponse({
        'matches': [
            {
                'id': group.id,
                'name': group.name,
            }
            for group in groups
        ]
    })

