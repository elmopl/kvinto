function LedgerGroupForm(form)
{
    let self = this;

    this.csrf_token = document.getElementsByName('csrfmiddlewaretoken')[0].value;
    this.form = form;

    this.group_id = null;

    this.name = document.createElement('input');
    this.name.type = 'text';
    this.name.name = 'name';
    this.form.appendChild(this.name);

    let container = document.createElement('div');
    container.style['padding-left'] = '3em';
    this.transactions = document.createElement('div');
    container.appendChild(this.transactions);
    let add = document.createElement('span');
    add.textContent = '[+]';
    add.addEventListener('click', function(){self.add_transaction();});

    container.appendChild(this.transactions);
    container.appendChild(add);
    this.form.appendChild(container);

    document.getElementsByName('submit')[0].addEventListener('click', this.submit.bind(this));
}

LedgerGroupForm.prototype.set_id = function(id)
{
    this.group_id = id;
}

LedgerGroupForm.prototype.submit = function(evt)
{
    evt.preventDefault();

    let data = this.data();

    var xhr = new XMLHttpRequest();
    xhr.open('POST', this.form.action, true);
    xhr.setRequestHeader('Content-Type', 'application/json; charset=UTF-8');
    xhr.setRequestHeader('X-CSRFToken', this.csrf_token);

    console.log(JSON.stringify(data));
  
    // send the collected data as JSON
    xhr.send(JSON.stringify(data));
  
    xhr.onloadend = function () {
        let info = JSON.parse(xhr.responseText);
        window.location.href = info.edit_url;
    };

    return false;
}

LedgerGroupForm.prototype.data = function()
{
    let transactions = [];
    for (let transaction of this.transactions.querySelectorAll('option:checked') || [])
    {
        transactions.push({
            'id': transaction.value,
            'name': transaction.textContent,
        });
    }

    return {
        id: this.group_id,
        name: this.form.querySelector('[name=name]').value,
        transactions: transactions,
    }
}

LedgerGroupForm.prototype.add_transaction = function(data)
{
    let csrf_token = this.csrf_token;
    let row = document.createElement('div');
    let transaction = document.createElement('input');
    transaction.name = 'transaction';
    let remove = make_remove_button(row);
    row.appendChild(transaction);
    row.appendChild(remove);

    this.transactions.appendChild(row);

    transaction.focus();

    new AutocompleteWidget(
        transaction,
        function(query, clb){
            get_matches(
                function(matches){
                    let reformatted = [];
                    for (match of matches)
                    {
                        reformatted.push({
                            'id': match.id,
                            'name': match.name + ' @ ' + match.date,
                        });
                    }
                    clb(reformatted);
                },
                '/transactions/match',
                csrf_token,
                query
            );
        },
        data
    );
}

document.addEventListener('DOMContentLoaded', function(){
    let form = new LedgerGroupForm(
        document.getElementsByTagName('form')[0]
    );

    console.log(JSON.stringify(initial_form_data));

    form.name.value = initial_form_data.name;
    form.set_id(initial_form_data.id);
    for (transaction of initial_form_data.transactions)
    {
        form.add_transaction(transaction);
    }
});
