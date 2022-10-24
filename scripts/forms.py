from datetime import datetime

from flask_wtf import FlaskForm
from wtforms import DateField, RadioField, SubmitField
from wtforms.validators import DataRequired


class FormBookDesk(FlaskForm):
    booking_date = DateField(
        label="What day would you like to book?", default=datetime.today, validators=[DataRequired()]
    )

    booking_time = RadioField(
        "Choose time",
        validators=[DataRequired()],
        choices=[
            ("AMPM", "Whole Day"),
            ("AM", "Morning only"),
            ("PM", "Afternoon only"),
        ],
        default="AMPM"
    )

    submit = SubmitField("Submit")
