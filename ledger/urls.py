from django.urls import path

from . import views

urlpatterns = [
    path('statements/list', views.statements.statements_list, name='list_statements'),
    path('statements/view/<int:statement_id>', views.statements.show, name='view_statement'),
    path('statements/items/<int:year>', views.statements.show_year_positions, name='statement_year_positions'),
    path('statements/items/<int:year>/<int:month>/<int:day>/<int:end_year>/<int:end_month>/<int:end_day>', views.statements.show_positions, name='statement_positions'),
    path('statements/upload', views.statements.upload, name='upload_statement'),
    path('statements/download/<int:statement_id>', views.statements.download, name='download_statement'),
    path('statements/destroy/<int:statement_id>', views.statements.destroy, name='destroy_statement'),

    path('accounts/list', views.accounts.accounts_list, name='list_accounts'),
    path('accounts/match', views.accounts.accounts_match, name='match_accounts'),

    path('persons/match', views.persons.persons_match, name='match_persons'),

    path('transactions/create', views.transactions.create, name='create_transaction'),
    path('transactions/edit/<int:transaction_id>', views.transactions.edit, name='edit_transaction'),
    path('transactions/save', views.transactions.save, name='save_transaction'),
    path('transactions/create_for_statement_item/<int:statement_row_id>', views.transactions.create_for_statement_item, name='create_transaction_for_statement_item'),
    path('transactions/view/<int:transaction_id>', views.transactions.view, name='view_transaction'),
    path('transactions/match', views.transactions.transactions_match, name='match_transaction'),
    path('transactions/list', views.transactions.list_transactions, name='list_transactions'),

    path('groups/create', views.groups.create, name='create_group'),
    path('groups/list', views.groups.list, name='list_groups'),
    path('groups/edit/<int:group_id>', views.groups.edit, name='edit_group'),
    path('groups/summary/<int:group_id>', views.groups.summary, name='group_summary'),
    path('groups/save', views.groups.save, name='save_group'),
    path('groups/match', views.groups.groups_match, name='match_groups'),
]
