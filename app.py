from flask import Flask, render_template, request, jsonify
from flask_mail import Mail, Message
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import and_
from datetime import datetime
import requests


app = Flask(__name__)
CORS(app,resources={r"/*":{"origins":"*"}})

HOLIDAY_API_URL = "https://holidayapi.com/v1/holidays"
API_KEY = "fc14d6ff-335d-4f7c-ac04-633d3619be06"


app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///event.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


# Configure Flask-Mail
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USERNAME'] = 'sunnykasalawat007@gmail.com'
app.config['MAIL_PASSWORD'] = 'xzjj yipz fuxl ptkj'
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False

mail = Mail(app)



class Event(db.Model):
    sn=db.Column(db.Integer, primary_key=True, autoincrement=True)
    title=db.Column(db.String(200), nullable=False)
    description=db.Column(db.String(500), nullable=False)
    start_date=db.Column(db.Date, nullable=False)
    end_date=db.Column(db.Date, nullable=False)
    created_at=db.Column(db.DateTime, default=datetime.utcnow())
    emails=db.Column(db.Text)

    def __repr__(self) -> str:
        return f"{self.sn} - {self.tile}"



def sendmail(title,description,start_date,end_date,email_recipient):
    # Send email notification
    msg = Message('New Event Created',
                      sender='your_email@gmail.com',
                      recipients=[email_recipient])
    msg.body = f"""
        A new event has been created:
        
        Title: {title}
        Description: {description}
        Start Date: {start_date}
        End Date: {end_date}
        """

    mail.send(msg)

    return jsonify({'message': 'Event created and email sent.'}), 201

@app.route('/api/events', methods=['POST'])
def create_event():

    data = request.get_json()
    try:
        start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
        end_date = datetime.strptime(data['end_date'], '%Y-%m-%d').date()

        # Check for overlapping events
        overlapping_event = Event.query.filter(
            and_(
                Event.start_date <= end_date,
                Event.end_date >= start_date
            )
        ).first()

        if overlapping_event:
            return jsonify({'error': 'An event already exists within the selected date range.'}), 400

        new_event = Event(
            title=data['title'],
            description=data['description'],
            start_date=start_date,
            end_date=end_date,
            emails=data['emails']
        )

        db.session.add(new_event)
        db.session.commit()
          # Add emails
        for email in data['emails'].split(','):
            print(email)
            sendmail(new_event.title,new_event.description,new_event.start_date,new_event.end_date,email)


        return jsonify({'message': 'Event created successfully', 'event': {
            'title': new_event.title,
            'description': new_event.description,
            'start_date': new_event.start_date.strftime('%Y-%m-%d'),
            'end_date': new_event.end_date.strftime('%Y-%m-%d'),
            'emails': new_event.emails
        }}), 201

    except ValueError:
        return jsonify({'error': 'Date format should be YYYY-MM-DD'}), 400



@app.route('/api/events', methods=['GET'])
def get_events():
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    if start_date and end_date:
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        events = Event.query.filter(Event.start_date <= end_date, Event.end_date >= start_date).all()
    else:
        events = Event.query.all()
    
    events_list = [{
        'sn': event.sn,
        'title': event.title,
        'description': event.description,
        'start_date': event.start_date.strftime('%Y-%m-%d'),
        'end_date': event.end_date.strftime('%Y-%m-%d'),
        'emails':event.emails
    } for event in events]  
    print(events_list)
    
    return jsonify(events_list)

@app.route('/api/events/<date>', methods=['GET'])
def get_eventsday(date):
    date = date
    print(date)
    
    if date:
        events = Event.query.filter(start_date =date).all()
    else:
        events = Event.query.all()
    
    events_list = [{
        'sn': event.sn,
        'title': event.title,
        'description': event.description,
        'start_date': event.start_date.strftime('%Y-%m-%d'),
        'end_date': event.end_date.strftime('%Y-%m-%d')
    } for event in events]
    
    return jsonify(events_list)


@app.route('/api/events/<int:event_id>', methods=['PUT'])
def update_event(event_id):
    data = request.get_json()
    event = Event.query.get(event_id)

    if not event:
        return jsonify({'error': 'Event not found'}), 404

    try:
        new_start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
        new_end_date = datetime.strptime(data['end_date'], '%Y-%m-%d').date()

        # Check for overlapping events, excluding the current event
        overlapping_event = Event.query.filter(
            and_(
                Event.sn!= event_id,  # Exclude the current event
                Event.start_date <= new_end_date,
                Event.end_date >= new_start_date
            )
        ).first()

        if overlapping_event:
            return jsonify({
                'error': 'Overlapping event exists',
                'overlapping_event': {
                    'sn': overlapping_event.sn,
                    'title': overlapping_event.title,
                    'start_date': overlapping_event.start_date.strftime('%Y-%m-%d'),
                    'end_date': overlapping_event.end_date.strftime('%Y-%m-%d')
                }
            }), 409

        # Update the event
        event.title = data['title']
        event.description = data['description']
        event.start_date = new_start_date
        event.end_date = new_end_date
        event.emails = data['emails']
    except ValueError:
        return jsonify({'error': 'Date format should be YYYY-MM-DD'}), 400

    db.session.commit()
    for email in data['emails'].split(','):
            print(email)
            sendmail(event.title,event.description,event.start_date,event.end_date,email)


    return jsonify({
        'message': 'Event updated successfully',
        'event': {
            'sn': event.sn,
            'title': event.title,
            'description': event.description,
            'start_date': event.start_date.strftime('%Y-%m-%d'),
            'end_date': event.end_date.strftime('%Y-%m-%d'),
            'emails': event.emails
        }
    }), 200


@app.route('/api/events/<int:event_id>', methods=['DELETE'])
def delete_event(event_id):
    event = Event.query.get(event_id)
    if event:
       
        db.session.delete(event)
        db.session.commit()

        return jsonify({'message': 'Event deleted successfully'})
    else:
        return jsonify({'error': 'Event not found'}), 404
    











@app.route('/api/events/<int:event_id>', methods=['GET'])
def get_event(event_id):
    event = Event.query.filter_by(sn=event_id).first()
    if event:
        event_data = {
            'sn': event.sn,
            'title': event.title,
            'description': event.description,
            'start_date': event.start_date.strftime('%Y-%m-%d'),
            'end_date': event.end_date.strftime('%Y-%m-%d')
        }
        return jsonify(event_data)
    else:
        return jsonify({'error': 'Event not found'}), 404

@app.route('/api/events/Email/<int:event_id>', methods=['GET'])
def get_eventemail(event_id):
    event_emails = Email.query.filter_by(event_id=event_id).all()

    if event_emails:
        # Convert the list of email objects to a list of dictionaries
        emails_data = [{'email_address': email.email_address} for email in event_emails]
        return jsonify(emails_data)
    else:
        return jsonify({'error': 'No emails found for this event'}), 404


@app.route('/api/holidays', methods=['GET'])
def get_holidays():
    country = request.args.get('country', 'US')
    year = request.args.get('year', '2024')
    url = f'https://date.nager.at/Api/v2/PublicHolidays/{year}/{country}'
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        holidays_list = [{'name': holiday['name'], 'date': holiday['date']} for holiday in data]
        
        return jsonify(holidays_list)
    
    except requests.exceptions.HTTPError as http_err:
        return jsonify({'error': f'HTTP error occurred: {http_err}'}), 400
    except Exception as err:
        return jsonify({'error': f'Other error occurred: {err}'}), 500


if __name__ == '__main__':
    app.run(debug=True)


if __name__=="__main__":
    app.run(debug=True)