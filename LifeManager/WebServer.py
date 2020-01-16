import json
from flask import Flask, render_template, request
from LifeManager.dbutil import get_session
from LifeManager.Events import Action, Tag


app = Flask(__name__)


@app.route('/')
def home():

    return render_template('welcome.html')


@app.route('/actions')
def actions():
    session = get_session()
    db_actions = Action.select_all(session)
    db_actions.sort(key=lambda a: a.time, reverse=True)

    return render_template('actions.html', actions=db_actions)


@app.route('/add_action', methods=['GET', 'POST'])
def add_action():
    result = None
    new_action_id = None
    session = get_session()
    db_event_titles = [et[0] for et in Action.get_titles(session)]
    db_event_dates = [ed[0] for ed in Tag.get_tags_by_type(session, 'Date')]

    if request.method == 'POST':
        # form data is passed as an immutable multi-dict and needs to be coerced into a more usable type
        form_data = {x: request.form[x] for x in request.form}
        new_action = Action(**form_data)
        if new_action.add_to_db(session):
            result = "The action '{}' was added to the database.".format(new_action.title)
            new_action_id = new_action.id
        else:
            result = "ERROR: The action '{}' could not be added to the database.".format(new_action.title)

    return render_template('add_action.html', result=result, new_action_id=new_action_id, action_titles=db_event_titles,
                           event_dates=db_event_dates)


@app.route('/duplicate_action', methods=['GET', 'POST'])
def duplicate_action():
    result = None
    new_action_id = None
    session = get_session()
    db_event_titles = [et[0] for et in Action.get_titles(session)]
    db_event_dates = [ed[0] for ed in Tag.get_tags_by_type(session, 'Date')]

    if request.method == 'POST':
        # form data is passed as an immutable multi-dict and needs to be coerced into a more usable type
        form_data = {x: request.form[x] for x in request.form}
        old_action = Action.select_one(session, title=form_data['title'])
        if form_data['time']:
            new_action = old_action.duplicate(session, replacement_tags={'Date': form_data['time']}, skip_tags=['Date'])
        else:
            new_action = old_action.duplicate(session, skip_tags=['Date'])

        if new_action.add_to_db(session):
            result = "The action '{}' was duplicated in the database.".format(new_action.title)
            new_action_id = new_action.id
        else:
            result = "ERROR: The action '{}' could not be duplicated in the database.".format(new_action.title)

    return render_template('duplicate_action.html', result=result, new_action_id=new_action_id,
                           action_titles=db_event_titles, event_dates=db_event_dates)


@app.route('/actions/<event_id>', methods=['GET', 'POST'])
def single_action(event_id):
    session = get_session()
    db_action = Action.select_one(session, id=event_id)
    db_tag_types = [tt[0] for tt in Tag.get_types(session)]
    result = None
    if request.method == 'POST':
        # form data is passed as an immutable multi-dict and needs to be coerced into a more usable type
        form_data = {x: request.form[x] for x in request.form}
        db_action.add_tag(session, **form_data)
        result = 'Added tag.'

    return render_template('single_action.html', action=db_action, result=result, tag_types=db_tag_types)


@app.route('/tag_types')
def tag_types():
    session = get_session()
    db_tag_types = Tag.get_types_count(session)

    return render_template('tag_types.html', tag_types=db_tag_types)


@app.route('/tags/<tag_type>')
def tags_by_type(tag_type):
    session = get_session()
    db_tags = Tag.get_tags_count_by_type(session, tag_type)

    return render_template('tags_by_type.html', tag_type=tag_type, tags=db_tags)


@app.route('/tags/<tag_type>/<tag_value>/actions')
def actions_by_tag(tag_type, tag_value):
    session = get_session()

    db_actions = Action.select_some_by_tag(session, tag_type, tag_value).all()
    db_actions.sort(key=lambda a: a.time, reverse=True)

    return render_template('actions_by_tag.html', actions=db_actions)


@app.route('/api/1/actions', methods=['GET'])
def api_get_actions():
    session = get_session()
    db_actions = Action.select_all(session)

    ret = []
    for a in db_actions:
        ret.append(a.to_json())

    return json.dumps(ret), 200, {'Content-Type': 'application/json'}


@app.route('/api/1/actions/<event_id>', methods=['GET'])
def api_get_single_action(event_id):
    session = get_session()
    action = Action.select_one(session, id=event_id)

    return json.dumps(action.to_json()), 200, {'Content-Type': 'application/json'}


@app.route('/api/1/actions', methods=['POST'])
def api_add_action():

    content = request.json
    new_action = Action(**content)

    session = get_session()
    new_action.add_to_db(session)

    return json.dumps({'success': True}), 201, {'Content-Type': 'application/json'}


@app.route('/api/1/tag_types', methods=['GET'])
def api_get_tag_types():

    session = get_session()
    db_tag_types = Tag.get_types(session)

    ret = []
    for t in db_tag_types:
        ret.append(t[0])

    return json.dumps(ret), 200, {'Content-Type': 'application/json'}


@app.route('/api/1/tag_types/<tag_type>/tags', methods=['GET'])
def api_get_tags_by_type(tag_type):

    session = get_session()
    db_tags = Tag.get_tags_by_type(session, tag_type)

    ret = []
    for t in db_tags:
        ret.append(t[0])

    return json.dumps(ret), 200, {'Content-Type': 'application/json'}


@app.route('/api/1/actions/<event_id>', methods=['PUT'])
def api_update_action(event_id):

    raise NotImplementedError
