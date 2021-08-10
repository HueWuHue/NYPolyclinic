from wtforms import Form, StringField, TextAreaField, DecimalField, validators, IntegerField, BooleanField, SubmitField, \
    SelectField, PasswordField
from wtforms.validators import DataRequired, Length, Email, ValidationError
from wtforms.fields.html5 import DateField, EmailField
from flask_wtf import FlaskForm
import shelve
from datetime import date


# Pharmacy Forms
class CreateItemForm(Form):
    name = StringField('Name: ', [validators.Length(min=1, max=25), validators.DataRequired()], default='')
    price = DecimalField('Price($): ', [validators.NumberRange(min=1), validators.DataRequired()], default=0, places=2)
    have = IntegerField('Amount we have in stock: ', [validators.NumberRange(min=1), validators.DataRequired()],
                        default=0)
    picture = StringField('Picture (link): ', [validators.Length(min=1, max=500), validators.DataRequired()],
                          default='')
    bio = TextAreaField('Item Description: ', [validators.DataRequired()], default='')
    prescription = BooleanField('Prescription', default=False)


class BuyItemForm(Form):
    want = IntegerField('Quantity: ', [validators.NumberRange(min=1), validators.DataRequired()], default=0)


class CheckoutForm(Form):
    # Could use user profiles instead
    address = StringField('Address: ', [validators.Length(min=1, max=150), validators.DataRequired()], default='')
    # Use Sting field as Postal Code needs to be saved as string as integer removes front 0 i.e 081456 = 81456
    postal_code = StringField('Postal Code: ', [validators.Length(min=6, max=6), validators.DataRequired()], default='')


# ContactUs Forms
class ContactForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired(), Length(min=2, max=150)])
    email = StringField("Email", validators=[DataRequired(), Email()])
    subject = StringField("Subject", validators=[DataRequired()])
    enquiries = TextAreaField("Enquiries ", validators=[DataRequired()])
    submit = SubmitField("Submit")


class FAQ(Form):
    question = StringField('Question', [validators.Length(min=1), validators.DataRequired()])
    answer = TextAreaField('Answer', [validators.Length(min=1), validators.DataRequired()])
    date = DateField('Date', [validators.DataRequired()], format='%Y-%m-%d')


class SearchBar(Form):
    search = StringField('')

    def validate_search(form, field):
        for char in field.data:
            if char not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890':
                raise ValidationError('Invalid input! Please do not use special characters')


class CreateApplicationForm(Form):
    fname = StringField('First Name', [validators.Length(min=1, max=150), validators.DataRequired()])
    lname = StringField('Last Name', [validators.Length(min=1, max=150), validators.DataRequired()])
    nric = StringField('NRIC / FIN', [validators.Length(min=9, max=9,
                                                        message="NRIC/FIN should only consists of 2 Letters and 7 digits. e.g.S1234567A"),
                                      validators.DataRequired()])  # need to validate
    email = EmailField('Email', [validators.Length(min=1, max=150), validators.DataRequired(), validators.Email()])
    age = IntegerField('Age', [validators.number_range(min=1, max=150), validators.DataRequired()])
    address = StringField('Address', [validators.Length(min=1, max=150), validators.DataRequired()])
    gender = SelectField('Gender', [validators.DataRequired()],
                         choices=[('', 'Select'), ('Male', 'Male'), ('Female', 'Female')], default='')
    nationality = StringField('Nationality', [validators.Length(min=1, max=150), validators.DataRequired()])
    language = StringField('Language', [validators.Length(min=1, max=150), validators.DataRequired()])
    phoneno = IntegerField('Phone Number',
                           [validators.number_range(min=60000000, max=999999999,
                                                    message="Singapore's Phone Number must be 8 numbers only"),
                            validators.DataRequired()])  # need to validate
    quali = SelectField('Highest Qualification', [validators.DataRequired()],
                        choices=[('', 'Select'), ("O'Levels", "O'Levels"), ("N'Levels", "N'Levels"),
                                 ("A'Levels", "A'Levels"), ('Diploma', 'Diploma'), ('Bachelor', 'Bachelor'),
                                 ('Master', 'Master')], default='')
    industry = SelectField('Industry', [validators.DataRequired()], choices=[('', 'Select'), ("Tourism", "Toursim"), (
        "BioMedical Science", "BioMedical Science"),
                                                                             ("Logistics", "Logistics"),
                                                                             ('Banking & Finance', 'Banking & Finance'),
                                                                             ('Chemicals', 'Chemicals'),
                                                                             ('Construction', 'Construction'),
                                                                             ('Casino', 'Casino'),
                                                                             ('Healthcare', 'Healthcare'),
                                                                             ('Education', 'Education'),
                                                                             ('ICT & Media', 'ICT & Media'),
                                                                             ('Null', 'Null')], default='')
    comp1 = StringField('Company', [validators.Length(min=1, max=150), validators.DataRequired()])
    posi1 = StringField('Position', [validators.Length(min=1, max=150), validators.DataRequired()])
    comp2 = StringField('Company (optional)', [validators.Length(min=1, max=150), validators.optional()])
    posi2 = StringField('Position (optional)', [validators.Length(min=1, max=150), validators.optional()])
    empty1 = StringField('empty', [validators.Length(min=1, max=150), validators.optional()])
    empty2 = StringField('empty', [validators.Length(min=1, max=150), validators.optional()])


# User Forms
class RegisterForm(Form):
    NRIC = StringField("NRIC", [validators.DataRequired(), validators.Length(min=9, max=9)])
    FirstName = StringField("First Name", [validators.DataRequired()])
    LastName = StringField("Last Name", [validators.DataRequired()])
    Gender = SelectField('Gender', [validators.DataRequired()],
                         choices=[('', 'Select'), ('F', 'Female'), ('M', 'Male')], default='')
    Dob = DateField('Date of Birth', [validators.DataRequired()])
    Email = StringField("Email", [validators.DataRequired(), validators.Email()])
    Password = PasswordField("Password", [validators.DataRequired(), validators.Length(min=8)])
    Confirm = PasswordField("Confirm Password", [validators.DataRequired(), validators.EqualTo("Password")])
    URL = StringField("URL", [validators.optional()])
    specialization = StringField("Specialization", [validators.optional()])

    def validate_Password(form, field):
        lower = False
        upper = False
        num = False
        spchar = False
        for char in field.data:
            if char in 'abcdefghijklmnopqrstuvwxyz':
                lower = True
            elif char in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
                upper = True
            elif char in '1234567890':
                num = True
            else:
                spchar = True
        if not (lower and upper and num and spchar):
            raise ValidationError(
                'Password should have a combination of uppercase and lower case letters,numbers and special characters.')


class LoginForm(Form):
    NRIC = StringField("NRIC", [validators.DataRequired(), validators.Length(min=9, max=9)])
    Password = PasswordField("Password", [validators.DataRequired()])

    def validate_NRIC(form, field):
        for char in field.data:
            if char not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890':
                raise ValidationError(
                    'Invalid input!Please do not use any special characters')


class UpdateProfileForm(Form):
    Email = StringField("Email", [validators.DataRequired(), validators.Email()])
    Dob = DateField('Date of Birth', [validators.DataRequired()])


class ChangePasswordForm(Form):
    Password = PasswordField("Password", [validators.DataRequired()])
    Confirm = PasswordField("Confirm Password", [validators.DataRequired(), validators.EqualTo("Password")])


class ResetPasswordForm(Form):
    Email = StringField("Email", [validators.DataRequired(), validators.Email()])


class AdminUpdateForm(Form):
    Email = StringField("Email", [validators.DataRequired(), validators.Email()])
    Password = PasswordField("Password", [validators.DataRequired()])
    URL = StringField("URL", [validators.optional()])


# Appointment Form
class AppointmentForm(Form):
    Department = SelectField("Department", [validators.DataRequired()],
                             choices=[('', 'Select'), ('Cardiology', 'Cardiology'),
                                      ('Gastroenterology', 'Gastroenterology'),
                                      ('Haematology', 'Haematology')])
    Date = DateField("Appointment Date", [validators.DataRequired()], format='%Y-%m-%d')
    Time = SelectField("Appointment Time", [validators.DataRequired()],
                       choices=[('', 'Select'), ('8:00:00', '8AM'), ('10:00:00', '10AM'), ('12:00:00', '12PM'),
                                ('14:00:00', '2PM'), ('16:00:00', '4PM'),
                                ('18:00:00', '6PM'), ('20:00:00', '8PM'), ('22:00:00', '10PM')], default='')
    Type = SelectField("Appointment Type", [validators.DataRequired()],
                       choices=[('', 'Select'), ('E-Doctor', 'E-Doctor'), ('Visit', 'Visit')])


db = shelve.open('storage.db', 'c')
user_dict = db["Users"]
patient_list = [('', 'Select')]
for key in user_dict:
    if user_dict[key].get_role() == "Patient":
        patient_info = (user_dict[key].get_name(), user_dict[key].get_name())
        patient_list.append(patient_info)


class DocAppointmentForm(Form):
    Department = SelectField("Department", [validators.DataRequired()],
                             choices=[('', 'Select'), ('Cardiology', 'Cardiology'),
                                      ('Gastroenterology', 'Gastroenterology'),
                                      ('Haematology', 'Haematology')])
    Date = DateField("Appointment Date", [validators.DataRequired()], format='%Y-%m-%d')
    Time = SelectField("Appointment Time", [validators.DataRequired()],
                       choices=[('', 'Select'), ('8:00:00', '8AM'), ('10:00:00', '10AM'), ('12:00:00', '12PM'),
                                ('14:00:00', '2PM'), ('16:00:00', '4PM'),
                                ('18:00:00', '6PM'), ('20:00:00', '8PM'), ('22:00:00', '10PM')], default='')
    Type = SelectField("Appointment Type", [validators.DataRequired()],
                       choices=[('', 'Select'), ('E-Doctor', 'E-Doctor'), ('Visit', 'Visit')])
    Patient = SelectField("Patient", [validators.DataRequired()], choices=patient_list, default='')


class DocCommentForm(Form):
    Department = SelectField("Department", [validators.DataRequired()],
                             choices=[('', 'Select'), ('Cardiology', 'Cardiology'),
                                      ('Gastroenterology', 'Gastroenterology'),
                                      ('Haematology', 'Haematology')])
    Date = DateField("Appointment Date", [validators.DataRequired()], format='%Y-%m-%d')
    Time = SelectField("Appointment Time", [validators.DataRequired()],
                       choices=[('', 'Select'), ('8:00:00', '8AM'), ('10:00:00', '10AM'), ('12:00:00', '12PM'),
                                ('14:00:00', '2PM'), ('16:00:00', '4PM'),
                                ('18:00:00', '6PM'), ('20:00:00', '8PM'), ('22:00:00', '10PM')], default='')
    Type = SelectField("Appointment Type", [validators.DataRequired()],
                       choices=[('', 'Select'), ('E-Doctor', 'E-Doctor'), ('Visit', 'Visit')])
    Patient = SelectField("Patient", [validators.DataRequired()], choices=patient_list, default='')
    Comment = StringField("Comments", [validators.Optional()])
