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

    this.reference = document.createElement('input');
    this.reference.type = 'text';
    this.reference.name = 'reference';
    this.form.appendChild(this.reference);

    this.form.appendChild(document.createElement('br'));

    this.settled = document.createElement('input');
    this.settled.type = 'datetime-local';
    this.settled.name = 'settled';
    this.form.appendChild(this.settled);

    this.form.appendChild(document.createElement('br'));

    this.transfers = document.createElement('table');
    this.form.appendChild(this.transfers);

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
    return {
        id: this.group_id,
        name: this.form.querySelector('[name=name]').value,
        reference: this.form.querySelector('[name=reference]').value,
        settled: this.form.querySelector('[name=settled]').value,
    }
}

LedgerGroupForm.prototype.add_transfer = function(data)
{
    let csrf_token = this.csrf_token;
    let row = this.transfers.insertRow();

    let cell = row.insertCell();
    let link = document.createElement('a');
    link.text = data.transaction.name + ' ('+data.name+')';
    link.href = data.transaction.link;
    cell.appendChild(link);

    cell = row.insertCell();
    cell.innerHTML = data.transaction.date;

    cell = row.insertCell();
    cell.innerHTML = data.source_amount;

    cell = row.insertCell();
    cell.innerHTML = data.source_account.name;

    cell = row.insertCell();
    let participant_names = [];
    for (let participant of data.participants)
    {
        participant_names.push(participant.name);
    }
    cell.innerHTML = participant_names.join(', ');
}

document.addEventListener('DOMContentLoaded', function(){
    let form = new LedgerGroupForm(
        document.getElementsByTagName('form')[0]
    );

    console.log(initial_form_data);

    form.name.value = initial_form_data.name || '';
    form.reference.value = initial_form_data.reference || '';
    form.settled.value = (initial_form_data.settled || '').split('+')[0];
    form.set_id(initial_form_data.id);
    for (transaction of initial_form_data.transfers)
    {
        form.add_transfer(transaction);
    }
});
