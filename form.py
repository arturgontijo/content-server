from wtforms import Form, BooleanField, StringField, PasswordField, validators


class LoginForm(Form):
    uid = StringField('UID', [validators.Length(min=4, max=25)])
