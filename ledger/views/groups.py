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
from django.db.models import Q

import json

def edit(request, group_id):
    group = TransactionGroup.objects.get(id=group_id)
    settled = group.settled
    data = {
        'name': group.name,
        'id': group.id,
        'reference': group.reference,
        'settled': settled.isoformat() if settled else None,
        'transfers': [
            {
                'name': item.name,
                'id': item.id,
                'transaction': {
                    'id': item.transfer.transaction.id,
                    'name': item.transfer.transaction.name,
                    'link': reverse('edit_transaction', args=[item.transfer.transaction.id]),
                    'date': str(item.transfer.transaction.date),
                },
                'source_amount': item.source_amount,
                'destination_amount': item.destination_amount,
                'participants': [
                    {
                        'id': participant.person.id,
                        'name': participant.person.name,
                    }
                    for participant in item.participants.all()
                ],
                'source_account': {
                    'id': item.transfer.source.id,
                    'name': item.transfer.source.full_name,
                }
            }
            for item in group.transfer_items.all()
        ]
    }

    return _show_form(request, reverse('save_group'), data)

def save(request):
    data = json.loads(request.body)
    with transaction.atomic():
        group = TransactionGroup.objects.get(id=data['id'])
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

def _group_costs(group):
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

        return round(gained / 100, 2), round((paid_in or 0) / 100, 2)

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

    return {
        'group': group,
        'persons': persons,
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

def unsettled(request):
    groups = TransactionGroup.objects.filter(settled=None)
    groups = groups.order_by('name')

    context = {
        'groups': [
            _group_costs(group)
            for group in groups
        ]
    }

    return render(request, 'groups_summary.html', context)

def summary(request, group_id):
    group = TransactionGroup.objects.get(id=group_id)

    context = _group_costs(group)

    return render(request, 'group_summary.html', context)

def _show_form(request, url, data):
    context = {
        'action_url': url,
        'data': json.dumps(data),
        'group_id': data['id'],
    }
    return render(request, 'group_form.html', context)

def _populate_group(group, data):
    group.name = data['name'].strip()
    group.reference = data['reference'].strip()
    if data['settled']:
        group.settled = data['settled']
    else:
        group.settled = None
    group.save()

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
    
    name = query['name']
    groups = TransactionGroup.objects.filter(Q(name__contains=name) | Q(reference__contains=name))
    return JsonResponse({
        'matches': [
            {
                'id': group.id,
                'name': '{} - {}'.format(group.reference, group.name),
            }
            for group in groups
        ]
    })

