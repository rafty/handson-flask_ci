import os
import uuid
import random
from flask import Flask, render_template, redirect, url_for, jsonify
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
import boto3
import logging

# 環境変数からバックエンドサービスのURLを取得
region_name = os.getenv('AWS_DEFAULT_REGION', 'ap-northeast-1')
table_name = os.getenv('DYNAMODB_TABLE_NAME', 'messages')

db = boto3.resource('dynamodb', region_name=region_name)
table = db.Table(table_name)

app = Flask(__name__)

logging.basicConfig(level=logging.DEBUG)

app.config['SECRET_KEY'] = os.urandom(24)
app.config['JSON_AS_ASCII'] = False  # jsonifyの日本語文字化け対策


class MessageForm(FlaskForm):
    message = StringField(validators=[DataRequired()])
    submit = SubmitField()


@app.route('/', methods=['GET'])
def home_page():
    app.logger.info('home_page()')

    form = MessageForm()

    db_response = table.scan()
    message_item = db_response['Items']
    app.logger.info(f'home_page() - message_item: {message_item}')

    return render_template('home.html', items=message_item, form=form)


@app.route('/', methods=['POST'])
def post_message():
    app.logger.info('post_message()')

    form = MessageForm()
    if form.validate_on_submit():  # Validation OK
        item = {
            'uuid': str(uuid.uuid4()),
            'message': form.message.data,
        }
        db_response = table.put_item(Item=item)

        app.logger.info(f'post_message() - db_response: {db_response}')

        return redirect(url_for('home_page'))  # home_page()にredirect

    return render_template('home.html', form=form)


# ---------------------------------------------------------------------------
# REST Api Test
# curl -X POST https://flask.xxxxxxxx.tk/2469dbc9-6eb8-8afa-a328-bb7bdd79922a
# ---------------------------------------------------------------------------
@app.route('/<message_uuid>', methods=['POST'])
def create_message(message_uuid):
    app.logger.info('create_message()')

    chars = ('a', 'b', 'c', 'd', 'e', 'f', 'g', '1', '2', '3', '4', '5', 'X', 'Y', 'Z')
    message = ''.join(random.choices(chars, k=8))
    item = {
        'uuid': message_uuid,
        'message': message,
    }
    db_response = table.put_item(Item=item)
    app.logger.info(f'create_message() - db_response: {db_response}')

    return jsonify(item)


# ---------------------------------------------------------------------------
# REST Api Test
# curl -X GET https://flask.xxxxxxxx.tk/2469dbc9-6eb8-8afa-a328-bb7bdd79922a
# ---------------------------------------------------------------------------
@app.route('/<message_uuid>', methods=['GET'])
def get_message(message_uuid):
    app.logger.info(f'get_message() - message_uuid: {message_uuid}')

    db_response = table.get_item(
        Key={
            'uuid': message_uuid
        }
    )
    app.logger.info(f'get_message() - db_response: {db_response}')

    message_item = db_response['Item']
    return jsonify(message_item)


@app.route('/healthz', methods=['GET'])
def health_check():
    return 'OK'


def health_check_dummy(data: str):
    app.logger.info(f'health_check_dummy() - data: {data}')
    return data + 'bar'


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
