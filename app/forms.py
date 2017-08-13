from flask.ext.wtf import Form
from wtforms import HiddenField
from wtforms.validators import DataRequired



class SimpleMturkForm(Form):
    '''
    Form contains a dictionary <resp> of items entered in HIT page,
    plus associated details of time spent on page, worker it,
    assignment and hit id, and the location and nationality of the
    incoming IP address.
    '''
    resp = HiddenField('resp', validators = [DataRequired()])
    time = HiddenField('time', validators = [DataRequired()])
    worker = HiddenField('worker', validators = [DataRequired()])
    location = HiddenField('location')
    nationality = HiddenField('nationality')
    assignment_id = HiddenField('assignment_id')
    hit_id = HiddenField('hit_id')
