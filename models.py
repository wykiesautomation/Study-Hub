from datetime import datetime,timezone,date
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from sqlalchemy import UniqueConstraint,Index
from werkzeug.security import generate_password_hash,check_password_hash
import secrets

db=SQLAlchemy()
def now():return datetime.now(timezone.utc)
class Customer(db.Model):
 id=db.Column(db.Integer,primary_key=True);name=db.Column(db.String(140),nullable=False);slug=db.Column(db.String(90),unique=True,nullable=False);active=db.Column(db.Boolean,default=True);created_at=db.Column(db.DateTime(timezone=True),default=now)
class User(UserMixin,db.Model):
 id=db.Column(db.Integer,primary_key=True);customer_id=db.Column(db.Integer,db.ForeignKey('customer.id'),nullable=False,index=True);email=db.Column(db.String(180),unique=True,nullable=False);name=db.Column(db.String(120),nullable=False);password_hash=db.Column(db.String(255),nullable=False);role=db.Column(db.String(30),default='fleet_viewer');active=db.Column(db.Boolean,default=True);last_login=db.Column(db.DateTime(timezone=True))
 @property
 def is_active(self):return bool(self.active)
 def set_password(self,p):self.password_hash=generate_password_hash(p)
 def check_password(self,p):return check_password_hash(self.password_hash,p)
class Depot(db.Model):
 id=db.Column(db.Integer,primary_key=True);customer_id=db.Column(db.Integer,db.ForeignKey('customer.id'),nullable=False,index=True);name=db.Column(db.String(120),nullable=False);code=db.Column(db.String(40));latitude=db.Column(db.Float);longitude=db.Column(db.Float);radius_m=db.Column(db.Float,default=500);active=db.Column(db.Boolean,default=True)
 __table_args__=(UniqueConstraint('customer_id','name'),)
class FleetGroup(db.Model):
 id=db.Column(db.Integer,primary_key=True);customer_id=db.Column(db.Integer,nullable=False,index=True);name=db.Column(db.String(120),nullable=False);description=db.Column(db.Text);active=db.Column(db.Boolean,default=True)
 __table_args__=(UniqueConstraint('customer_id','name'),)
class Vehicle(db.Model):
 id=db.Column(db.Integer,primary_key=True);customer_id=db.Column(db.Integer,nullable=False,index=True);fleet_no=db.Column(db.String(50),nullable=False);registration=db.Column(db.String(40));vin=db.Column(db.String(80));make=db.Column(db.String(80));model=db.Column(db.String(80));year=db.Column(db.Integer);vehicle_class=db.Column(db.String(60),default='TRUCK');depot_id=db.Column(db.Integer,db.ForeignKey('depot.id'),index=True);group_id=db.Column(db.Integer,db.ForeignKey('fleet_group.id'),index=True);tank_capacity_l=db.Column(db.Float);odometer_km=db.Column(db.Float);engine_hours=db.Column(db.Float);status=db.Column(db.String(30),default='ACTIVE');created_at=db.Column(db.DateTime(timezone=True),default=now);updated_at=db.Column(db.DateTime(timezone=True),default=now,onupdate=now)
 depot=db.relationship('Depot');group=db.relationship('FleetGroup')
 __table_args__=(UniqueConstraint('customer_id','fleet_no'),UniqueConstraint('customer_id','registration'),UniqueConstraint('customer_id','vin'),Index('ix_vehicle_customer_status','customer_id','status'))
class Driver(db.Model):
 id=db.Column(db.Integer,primary_key=True);customer_id=db.Column(db.Integer,nullable=False,index=True);employee_no=db.Column(db.String(50),nullable=False);name=db.Column(db.String(120),nullable=False);phone=db.Column(db.String(40));email=db.Column(db.String(160));licence_no=db.Column(db.String(80));licence_code=db.Column(db.String(30));licence_expiry=db.Column(db.Date);training_expiry=db.Column(db.Date);active=db.Column(db.Boolean,default=True);driving_score=db.Column(db.Float)
 __table_args__=(UniqueConstraint('customer_id','employee_no'),)
class Device(db.Model):
 id=db.Column(db.Integer,primary_key=True);customer_id=db.Column(db.Integer,nullable=False,index=True);device_uid=db.Column(db.String(100),nullable=False);vehicle_id=db.Column(db.Integer,db.ForeignKey('vehicle.id'),index=True);device_type=db.Column(db.String(60),default='GENERIC_REST');imei=db.Column(db.String(40));iccid=db.Column(db.String(50));firmware=db.Column(db.String(60));token_hash=db.Column(db.String(255));capabilities=db.Column(db.JSON,default=dict);enabled=db.Column(db.Boolean,default=True);external_power=db.Column(db.Boolean);backup_battery_percent=db.Column(db.Float);last_seen=db.Column(db.DateTime(timezone=True));created_at=db.Column(db.DateTime(timezone=True),default=now)
 vehicle=db.relationship('Vehicle')
 __table_args__=(UniqueConstraint('customer_id','device_uid'),UniqueConstraint('customer_id','imei'),UniqueConstraint('customer_id','iccid'))
 def issue_token(self):
  raw=secrets.token_urlsafe(42);self.token_hash=generate_password_hash(raw);return raw
 def verify_token(self,raw):return bool(self.token_hash and check_password_hash(self.token_hash,raw))
class DriverAssignment(db.Model):
 id=db.Column(db.Integer,primary_key=True);customer_id=db.Column(db.Integer,nullable=False,index=True);vehicle_id=db.Column(db.Integer,db.ForeignKey('vehicle.id'),nullable=False,index=True);driver_id=db.Column(db.Integer,db.ForeignKey('driver.id'),nullable=False,index=True);started_at=db.Column(db.DateTime(timezone=True),default=now);ended_at=db.Column(db.DateTime(timezone=True));start_odometer_km=db.Column(db.Float);end_odometer_km=db.Column(db.Float);notes=db.Column(db.Text)
 vehicle=db.relationship('Vehicle');driver=db.relationship('Driver')
class Location(db.Model):
 id=db.Column(db.BigInteger,primary_key=True);customer_id=db.Column(db.Integer,nullable=False,index=True);vehicle_id=db.Column(db.Integer,db.ForeignKey('vehicle.id'),nullable=False,index=True);device_id=db.Column(db.Integer,db.ForeignKey('device.id'),nullable=False,index=True);sequence=db.Column(db.String(110),nullable=False);session_id=db.Column(db.String(100));sampled_at=db.Column(db.DateTime(timezone=True),nullable=False,index=True);latitude=db.Column(db.Float,nullable=False);longitude=db.Column(db.Float,nullable=False);accuracy_m=db.Column(db.Float);speed_kmh=db.Column(db.Float);heading_deg=db.Column(db.Float);altitude_m=db.Column(db.Float);ignition=db.Column(db.Boolean);quality=db.Column(db.String(20),default='GOOD');received_at=db.Column(db.DateTime(timezone=True),default=now)
 __table_args__=(UniqueConstraint('device_id','sequence'),Index('ix_location_vehicle_time','vehicle_id','sampled_at'))
class Trip(db.Model):
 id=db.Column(db.BigInteger,primary_key=True);customer_id=db.Column(db.Integer,nullable=False,index=True);vehicle_id=db.Column(db.Integer,db.ForeignKey('vehicle.id'),nullable=False,index=True);driver_id=db.Column(db.Integer,db.ForeignKey('driver.id'));started_at=db.Column(db.DateTime(timezone=True));ended_at=db.Column(db.DateTime(timezone=True));start_lat=db.Column(db.Float);start_lon=db.Column(db.Float);end_lat=db.Column(db.Float);end_lon=db.Column(db.Float);distance_km=db.Column(db.Float,default=0);max_speed_kmh=db.Column(db.Float,default=0);state=db.Column(db.String(30),default='OPEN');quality=db.Column(db.String(20),default='VALIDATED')
 vehicle=db.relationship('Vehicle');driver=db.relationship('Driver')
class Geofence(db.Model):
 id=db.Column(db.Integer,primary_key=True);customer_id=db.Column(db.Integer,nullable=False,index=True);name=db.Column(db.String(120),nullable=False);kind=db.Column(db.String(30),default='KEEP_IN');latitude=db.Column(db.Float,nullable=False);longitude=db.Column(db.Float,nullable=False);radius_m=db.Column(db.Float,default=500);active=db.Column(db.Boolean,default=True);severity=db.Column(db.String(20),default='WARNING')
 __table_args__=(UniqueConstraint('customer_id','name'),)
class SecurityPolicy(db.Model):
 id=db.Column(db.Integer,primary_key=True);customer_id=db.Column(db.Integer,nullable=False,index=True);name=db.Column(db.String(120),nullable=False);group_id=db.Column(db.Integer,db.ForeignKey('fleet_group.id'));unauthorized_movement=db.Column(db.Boolean,default=True);after_hours=db.Column(db.Boolean,default=True);power_loss=db.Column(db.Boolean,default=True);tamper=db.Column(db.Boolean,default=True);offline_minutes=db.Column(db.Integer,default=15);movement_distance_m=db.Column(db.Float,default=80);start_hour=db.Column(db.Integer,default=5);end_hour=db.Column(db.Integer,default=22);active=db.Column(db.Boolean,default=True)
class SecurityEvent(db.Model):
 id=db.Column(db.BigInteger,primary_key=True);customer_id=db.Column(db.Integer,nullable=False,index=True);vehicle_id=db.Column(db.Integer,db.ForeignKey('vehicle.id'),nullable=False,index=True);device_id=db.Column(db.Integer,db.ForeignKey('device.id'));event_type=db.Column(db.String(80),nullable=False);state=db.Column(db.String(30),default='CANDIDATE');severity=db.Column(db.String(20),default='WARNING');confidence=db.Column(db.Float);latitude=db.Column(db.Float);longitude=db.Column(db.Float);detail=db.Column(db.JSON,default=dict);created_at=db.Column(db.DateTime(timezone=True),default=now,index=True);acknowledged_at=db.Column(db.DateTime(timezone=True));acknowledged_by=db.Column(db.Integer,db.ForeignKey('user.id'));resolved_at=db.Column(db.DateTime(timezone=True));resolution=db.Column(db.Text)
 vehicle=db.relationship('Vehicle');device=db.relationship('Device')
class FuelObservation(db.Model):
 id=db.Column(db.BigInteger,primary_key=True);customer_id=db.Column(db.Integer,nullable=False,index=True);vehicle_id=db.Column(db.Integer,db.ForeignKey('vehicle.id'),nullable=False,index=True);device_id=db.Column(db.Integer,db.ForeignKey('device.id'));sequence=db.Column(db.String(110));sampled_at=db.Column(db.DateTime(timezone=True),nullable=False,index=True);litres=db.Column(db.Float);percent=db.Column(db.Float);source=db.Column(db.String(40));quality=db.Column(db.String(20),default='GOOD');ignition=db.Column(db.Boolean);speed_kmh=db.Column(db.Float);received_at=db.Column(db.DateTime(timezone=True),default=now)
 __table_args__=(UniqueConstraint('device_id','sequence'),)
class FuelTransaction(db.Model):
 id=db.Column(db.BigInteger,primary_key=True);customer_id=db.Column(db.Integer,nullable=False,index=True);vehicle_id=db.Column(db.Integer,db.ForeignKey('vehicle.id'),nullable=False,index=True);driver_id=db.Column(db.Integer,db.ForeignKey('driver.id'));occurred_at=db.Column(db.DateTime(timezone=True),nullable=False);litres=db.Column(db.Float,nullable=False);amount=db.Column(db.Float);vendor=db.Column(db.String(160));reference=db.Column(db.String(100));odometer_km=db.Column(db.Float);verified=db.Column(db.Boolean,default=False)
class Diagnostic(db.Model):
 id=db.Column(db.BigInteger,primary_key=True);customer_id=db.Column(db.Integer,nullable=False,index=True);vehicle_id=db.Column(db.Integer,db.ForeignKey('vehicle.id'),nullable=False,index=True);device_id=db.Column(db.Integer,db.ForeignKey('device.id'));sampled_at=db.Column(db.DateTime(timezone=True),nullable=False,index=True);odometer_km=db.Column(db.Float);engine_hours=db.Column(db.Float);rpm=db.Column(db.Float);coolant_c=db.Column(db.Float);oil_pressure_kpa=db.Column(db.Float);battery_v=db.Column(db.Float);fuel_used_l=db.Column(db.Float);idle_fuel_l=db.Column(db.Float);faults=db.Column(db.JSON,default=list)
class MaintenanceIssue(db.Model):
 id=db.Column(db.BigInteger,primary_key=True);customer_id=db.Column(db.Integer,nullable=False,index=True);vehicle_id=db.Column(db.Integer,db.ForeignKey('vehicle.id'),nullable=False,index=True);title=db.Column(db.String(180),nullable=False);description=db.Column(db.Text);severity=db.Column(db.String(20),default='WARNING');state=db.Column(db.String(30),default='OPEN');source=db.Column(db.String(40),default='MANUAL');due_at=db.Column(db.DateTime(timezone=True));created_at=db.Column(db.DateTime(timezone=True),default=now);resolved_at=db.Column(db.DateTime(timezone=True))
 vehicle=db.relationship('Vehicle')
class Inspection(db.Model):
 id=db.Column(db.BigInteger,primary_key=True);customer_id=db.Column(db.Integer,nullable=False,index=True);vehicle_id=db.Column(db.Integer,db.ForeignKey('vehicle.id'),nullable=False,index=True);driver_id=db.Column(db.Integer,db.ForeignKey('driver.id'));kind=db.Column(db.String(30),default='PRE_TRIP');status=db.Column(db.String(30),default='DRAFT');items=db.Column(db.JSON,default=list);notes=db.Column(db.Text);submitted_at=db.Column(db.DateTime(timezone=True));created_at=db.Column(db.DateTime(timezone=True),default=now)
class NotificationPolicy(db.Model):
 id=db.Column(db.Integer,primary_key=True);customer_id=db.Column(db.Integer,nullable=False,index=True);name=db.Column(db.String(120));event_types=db.Column(db.JSON,default=list);email_to=db.Column(db.JSON,default=list);webhook_ids=db.Column(db.JSON,default=list);escalation_minutes=db.Column(db.Integer,default=5);active=db.Column(db.Boolean,default=True)
class Webhook(db.Model):
 id=db.Column(db.Integer,primary_key=True);customer_id=db.Column(db.Integer,nullable=False,index=True);name=db.Column(db.String(120));url=db.Column(db.String(500),nullable=False);secret=db.Column(db.String(160));events=db.Column(db.JSON,default=list);enabled=db.Column(db.Boolean,default=True);created_at=db.Column(db.DateTime(timezone=True),default=now)
class WebhookDelivery(db.Model):
 id=db.Column(db.BigInteger,primary_key=True);customer_id=db.Column(db.Integer,nullable=False,index=True);webhook_id=db.Column(db.Integer,db.ForeignKey('webhook.id'),nullable=False,index=True);event_type=db.Column(db.String(100));event_id=db.Column(db.String(100));payload=db.Column(db.JSON,default=dict);state=db.Column(db.String(30),default='PENDING');attempt_count=db.Column(db.Integer,default=0);http_status=db.Column(db.Integer);last_error=db.Column(db.Text);created_at=db.Column(db.DateTime(timezone=True),default=now);delivered_at=db.Column(db.DateTime(timezone=True))
class ApiCredential(db.Model):
 id=db.Column(db.Integer,primary_key=True);customer_id=db.Column(db.Integer,nullable=False,index=True);name=db.Column(db.String(120));key_prefix=db.Column(db.String(20));key_hash=db.Column(db.String(255));scopes=db.Column(db.JSON,default=list);enabled=db.Column(db.Boolean,default=True);last_used=db.Column(db.DateTime(timezone=True));created_at=db.Column(db.DateTime(timezone=True),default=now)
class ImportJob(db.Model):
 id=db.Column(db.Integer,primary_key=True);customer_id=db.Column(db.Integer,nullable=False,index=True);kind=db.Column(db.String(40));filename=db.Column(db.String(180));state=db.Column(db.String(30),default='PENDING');total_rows=db.Column(db.Integer,default=0);accepted_rows=db.Column(db.Integer,default=0);rejected_rows=db.Column(db.Integer,default=0);errors=db.Column(db.JSON,default=list);created_at=db.Column(db.DateTime(timezone=True),default=now)
def seed_demo():
 if Customer.query.first():return
 c=Customer(name='Demo Fleet',slug='demo');db.session.add(c);db.session.flush();u=User(customer_id=c.id,email='admin@fleettrack.local',name='Fleet Administrator',role='fleet_admin',password_hash='');u.set_password('ChangeMe123!');db.session.add(u);d=Depot(customer_id=c.id,name='Main Depot',code='MAIN');g=FleetGroup(customer_id=c.id,name='Long-Haul Trucks');db.session.add_all([d,g]);db.session.commit()
