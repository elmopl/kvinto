let expenses_account = {
    'id': 1,
    'name': 'Expenses',
};

function match_query(callback, url, csrf_token, query)
{
    let xmlhttp = new XMLHttpRequest();
    xmlhttp.open('POST', url);
    xmlhttp.setRequestHeader('Content-Type', 'application/json');
    xmlhttp.setRequestHeader('X-CSRFToken', csrf_token);
    xmlhttp.send(JSON.stringify(query));
    xmlhttp.onreadystatechange = function(){
        if (xmlhttp.readyState == 4)
        {
            callback(JSON.parse(xmlhttp.response).matches);
        }
    };
}

function get_matches(callback, url, csrf_token, name)
{
    match_query(callback, url, csrf_token, {'name': name});
}

function AutocompleteWidget(widget, lookup, initial_selection)
{
    this.input_widget = widget;
    this.select_widget = document.createElement('select');
    this.timeout = null;
    this.lookup = lookup;
    this.delay_before_lookup = 450;

    this.select_widget.name = widget.name;

    this.select_widget.addEventListener('keydown', this.start_typing.bind(this));
    // This makes first click on "select" the drop-down, not open it
    // This way we can just start typing.
    this.select_widget.addEventListener('mousedown', function(evt){
        if (document.activeElement != this)
        {
            evt.preventDefault();
            this.focus();
            return false;
        }
    });
    this.input_widget.addEventListener('keyup', this.restart_timer.bind(this));
    
    if (initial_selection)
    {
        this.stop_typing();
        this.update_options([initial_selection]);
    }
}

AutocompleteWidget.prototype.restart_timer = function()
{
    clearTimeout(this.timer);
    if (this.input_widget.value.length > 1)
    {
        this.timer = setTimeout(this.stopped_typing.bind(this), this.delay_before_lookup);
    }
}

AutocompleteWidget.prototype.stopped_typing = function()
{
    this.stop_typing();
    let self = this;

    this.input_widget.classList.add('pending-matches');

    function update(options)
    {
        self.update_options(options);
    }

    this.lookup(
        this.input_widget.value,
        update
    );
}

AutocompleteWidget.prototype.start_typing = function(evt)
{
    this.input_widget.classList.remove('no-matches', 'pending-matches');

    let modifier = evt.getModifierState('Alt') || evt.getModifierState('Shift') || evt.getModifierState('Ctrl');
    if (!modifier && (evt.key.length == 1 || evt.key == 'Backspace'))
    {
        this.select_widget.replaceWith(this.input_widget);
        this.input_widget.focus();
        this.restart_timer();
    }
}

AutocompleteWidget.prototype.update_options = function(options)
{
    if (options.length == 0)
    {
        this.input_widget.classList.remove('pending-matches');
        this.input_widget.classList.add('no-matches');
        return;
    }

    this.input_widget.replaceWith(this.select_widget);
    this.select_widget.focus();

    this.select_widget.textContent = '';
    for (let option of options)
    {
        let option_widget = document.createElement('option');
        option_widget.value = option.id;
        option_widget.textContent = option.name;
        this.select_widget.appendChild(option_widget);
    }
    this.select_widget.focus();
}

AutocompleteWidget.prototype.stop_typing = function()
{
    while (this.input_widget.firstChild)
    {
        this.input_widget.firstChild.remove();
    }
}

LedgerTransfersWidget = function(container, csrf_token)
{
    this.container = container;
    this.accounts_url = container.getAttribute('data-accounts-fetch-url');
    this.persons_url = container.getAttribute('data-persons-fetch-url');
    this.groups_url = container.getAttribute('data-groups-fetch-url');
    this.transfers_container = container.getElementsByClassName('transfers')[0];
    this.csrf_token = csrf_token;
    this.container.getElementsByClassName('ledger-transaction-add')[0].addEventListener(
        'click',
        this.clone_last.bind(this)
    );
}

LedgerTransfersWidget.prototype.clone_last = function()
{
    let data = this.data();
    this.add(data[data.length-1] || {});
}

function account_match_label(match)
{
    return match.name + ' @ ' + match.owner;
}

function make_remove_button(widget)
{
    let remove = document.createElement('span');
    remove.textContent = '[-]';
    remove.addEventListener('mouseover', function(){
        widget.classList.add('ledger-remove-highlight');
    });
    remove.addEventListener('mouseout', function(){
        widget.classList.remove('ledger-remove-highlight');
    });
    remove.addEventListener('click', function(){
        widget.remove();
    });
    return remove;
}

LedgerTransfersWidget.prototype.data = function()
{
    let transfers = [];
    for (let transfer of this.transfers_container.getElementsByClassName('ledger-transfer-widget'))
    {
        let items = [];
        for (let item of transfer.getElementsByClassName('ledger-transfer-item-widget'))
        {
            let participants = [];
            for (let participant of item.getElementsByClassName('ledger-participant-info'))
            {
                participants.push({
                    id: parseInt(participant.querySelector('[name=person]').value),
                    name: participant.querySelector('[name=person]').textContent,
                    weight: parseInt(participant.querySelector('[name=weight]').value),
                });
            }
            items.push({
                name: item.querySelector('[name=name]').value,
                group: {
                    id: parseInt(item.querySelector('[name=group]').value),
                    name: item.querySelector('[name=group]').textContent,
                },
                source_amount: parseInt(transfer.querySelector('[name=source_amount]').value),
                destination_amount: parseInt(transfer.querySelector('[name=destination_amount]').value),
                participants: participants,
            });
        }

        transfers.push({
            statement_row: parseInt(transfer.querySelector('[name=statement_row]').value),
            source_account: {
                id: parseInt(transfer.querySelector('[name=source_account]').value),
                name: transfer.querySelector('[name=source_account]').textContent,
            },
            destination_account: {
                id: parseInt(transfer.querySelector('[name=destination_account]').value),
                name: transfer.querySelector('[name=destination_account]').textContent,
            },
            items: items,
        });
    }

    return transfers;
}

function LedgerTransfersParticipantsWidget(participants_widget, persons_url, csrf_token)
{
    this.csrf_token = csrf_token;
    this.persons_url = persons_url;
    this.container = participants_widget;

    participants_widget.classList.add('ledger-participants-widget');

    this.participants_list = document.createElement('div');

    let add_participant = document.createElement('span');
    add_participant.textContent = '[+]';
    add_participant.classList.add('ledger-person-add');
    let self = this;
    add_participant.addEventListener('click', function(ev){self.add()});
    participants_widget.appendChild(this.participants_list);
    participants_widget.appendChild(add_participant);
}


LedgerTransfersParticipantsWidget.prototype.add = function(data)
{
    let persons_url = this.persons_url;
    let csrf_token = this.csrf_token;

    // Add participant row
    let participants_info = document.createElement('div');
    participants_info.classList.add('ledger-participant-info');
    let input = document.createElement('input');
    input.classList.add('autocomplete-widget');
    input.name = 'person';

    let weight = document.createElement('input');
    weight.classList.add('ledger-weight-input');
    weight.value = data && data.weight || 1;
    weight.name = 'weight';

    participants_info.appendChild(input);
    participants_info.appendChild(weight);
    participants_info.appendChild(make_remove_button(participants_info));

    this.participants_list.appendChild(participants_info);

    input.focus();

    new AutocompleteWidget(
        input,
        function(name, callback){
            get_matches(
                callback,
                persons_url,
                csrf_token,
                name
            );
        },
        data
    );
}

function LedgerTransfersItemsWidget(items_widget, groups_url, persons_url, csrf_token)
{
    this.csrf_token = csrf_token;
    this.persons_url = persons_url;
    this.groups_url = groups_url;

    this.container = document.createElement('div');
    items_widget.appendChild(this.container);

    let add_item = document.createElement('span');
    add_item.textContent = '[+]';
    add_item.classList.add('ledger-transfer-item-add');
    let self = this;
    add_item.addEventListener('click', function(ev){self.add()});
    items_widget.appendChild(add_item);
}

LedgerTransfersItemsWidget.prototype.add = function(data)
{
    data = data || {};
    let name = document.createElement('input');
    name.name = 'name';
    name.value = data.name || '';

    let group = document.createElement('input');
    group.name = 'group';

    let destination_amount = document.createElement('input');
    destination_amount.name = 'destination_amount';
    destination_amount.value = data.source_amount || '';
    destination_amount.classList.add('amount');

    let source_amount = document.createElement('input');
    source_amount.classList.add('amount');
    source_amount.name = 'source_amount';
    source_amount.value = data.source_amount || '';
    source_amount.addEventListener('keyup', function(){
        destination_amount.value = source_amount.value;
    });

    // Participants section
    let participants_container = document.createElement('div');
    participants_widget = new LedgerTransfersParticipantsWidget(
        participants_container,
        this.persons_url,
        this.csrf_token
    );

    for (let participant of data.participants || [])
    {
        participants_widget.add(participant);
    }

    let item_container = document.createElement('div');
    item_container.classList.add('ledger-transfer-item-widget');
    item_container.appendChild(name);
    item_container.appendChild(group);
    item_container.appendChild(source_amount);
    item_container.appendChild(destination_amount);
    item_container.appendChild(participants_container);
    item_container.appendChild(make_remove_button(item_container));

    this.container.appendChild(item_container);

    let groups_url = this.groups_url;
    let csrf_token = this.csrf_token;
    new AutocompleteWidget(
        group,
        function(name, callback){
            get_matches(
                callback,
                groups_url,
                csrf_token,
                name
            );
        },
        data.group
    );
}

LedgerTransfersWidget.prototype.add = function(data)
{
    let accounts_url = this.accounts_url;
    let persons_url = this.persons_url;
    let groups_url = this.groups_url;
    let csrf_token = this.csrf_token;

    let transfer_container = document.createElement('div');
    transfer_container.classList.add('ledger-transfer-widget');

    // Fields for direct transfer properties
    let source_account = document.createElement('input');
    source_account.classList.add('autocomplete-widget');
    source_account.name = 'source_account';

    let destination_account = document.createElement('input');
    destination_account.name = 'destination_account';
    destination_account.classList.add('autocomplete-widget');

    let statement_row = document.createElement('input');
    statement_row.name = 'statement_row';
    statement_row.value = data.statement_row || '';

    transfer_container.appendChild(source_account);
    transfer_container.appendChild(document.createTextNode('->'));
    transfer_container.appendChild(destination_account);
    transfer_container.appendChild(statement_row);

    // Items section
    let items_container = document.createElement('div');
    items_container.style['margin-left'] = '1em';
    let items_widget = new LedgerTransfersItemsWidget(
        items_container,
        groups_url,
        persons_url,
        csrf_token
    );

    for (let item of data.items || [])
    {
        items_widget.add(item);
    }

    transfer_container.appendChild(items_container);

    // Transfer remove button
    transfer_container.appendChild(make_remove_button(transfer_container));

    this.transfers_container.appendChild(transfer_container);

    let account_matches = function(name, callback){
        get_matches(callback, accounts_url, csrf_token, name);
    };

    new AutocompleteWidget(
        source_account,
        account_matches,
        data.source_account
    );

    new AutocompleteWidget(
        destination_account,
        account_matches,
        data.destination_account || expenses_account
    );

    return transfer_container;
}


