from ..models import Person
from django.shortcuts import render
from django.http import JsonResponse
import json

def persons_match(request):
    query = json.loads(request.body)
    persons = Person.objects.all()
    if query.get('name'):
        persons = persons.filter(name__contains=query['name'])
    if query.get('ids'):
        persons = persons.filter(id__in=query['ids'])
    return JsonResponse({
        'matches': [
            {
                'id': person.id,
                'name': person.name,
            }
            for person in persons
        ]
    })
