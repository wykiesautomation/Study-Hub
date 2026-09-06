import csv,io,secrets
from datetime import datetime,timezone,timedelta
from flask import Blueprint,render_template,request,redirect,url_for,flash,abort,send_file
from flask_login import login_user,logout_user,login_required,current_user
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from .models import *
from .services import route_segments
bp=Blueprint('main',__name__)
def tenant():return current_user.customer_id
@bp.route('/login',methods=['GET','POST'])
def login():
 if current_user.is_authenticated:return redirect(url_for('main.dashboard'))
 if request.method=='POST':
  u=User.query.filter(func.lower(User.email)==request.form.get('email','').strip().lower()).first()
  if u and u.check_password(request.form.get('password','')) and u.active:u.last_login=datetime.now(timezone.utc);db.session.commit();login_user(u);return redirect(url_for('main.dashboard'))
  flash('Invalid email or password.','error')
 return render_template('login.html')
@bp.get('/logout')
def logout():logout_user();return redirect(url_for('main.login'))
@bp.get('/')
@login_required
def dashboard():
 c=tenant();cut=datetime.now(timezone.utc)-timedelta(minutes=15);total=Vehicle.query.filter_by(customer_id=c,status='ACTIVE').count();online=Device.query.filter(Device.customer_id==c,Device.enabled.is_(True),Device.last_seen>=cut).count();offline=Device.query.filter(Device.customer_id==c,Device.enabled.is_(True)).count()-online;events=SecurityEvent.query.filter(SecurityEvent.customer_id==c,SecurityEvent.state.in_(['CANDIDATE','CONFIRMED','ACKNOWLEDGED'])).count();vehicles=Vehicle.query.filter_by(customer_id=c).order_by(Vehicle.fleet_no).limit(12).all();recent=SecurityEvent.query.filter_by(customer_id=c).order_by(SecurityEvent.created_at.desc()).limit(8).all();return render_template('dashboard.html',total=total,online=online,offline=offline,events=events,vehicles=vehicles,recent=recent)
@bp.route('/vehicles',methods=['GET','POST'])
@login_required
def vehicles():
 c=tenant()
 if request.method=='POST':
  v=Vehicle(customer_id=c,fleet_no=request.form['fleet_no'].strip(),registration=request.form.get('registration') or None,vin=request.form.get('vin') or None,make=request.form.get('make'),model=request.form.get('model'),year=request.form.get('year',type=int),vehicle_class=request.form.get('vehicle_class','TRUCK'),tank_capacity_l=request.form.get('tank_capacity_l',type=float),depot_id=request.form.get('depot_id',type=int),group_id=request.form.get('group_id',type=int));db.session.add(v)
  try:db.session.commit();flash('Vehicle added.','ok')
  except IntegrityError:db.session.rollback();flash('Fleet number, registration or VIN already exists.','error')
  return redirect(url_for('main.vehicles'))
 q=request.args.get('q','').strip();query=Vehicle.query.filter_by(customer_id=c)
 if q:query=query.filter(db.or_(Vehicle.fleet_no.ilike(f'%{q}%'),Vehicle.registration.ilike(f'%{q}%'),Vehicle.vin.ilike(f'%{q}%')))
 return render_template('vehicles.html',rows=query.order_by(Vehicle.fleet_no).all(),depots=Depot.query.filter_by(customer_id=c).all(),groups=FleetGroup.query.filter_by(customer_id=c).all())
@bp.get('/vehicles/<int:vehicle_id>')
@login_required
def vehicle_detail(vehicle_id):
 v=Vehicle.query.filter_by(id=vehicle_id,customer_id=tenant()).first_or_404();devices=Device.query.filter_by(customer_id=tenant(),vehicle_id=v.id).all();locations=Location.query.filter_by(customer_id=tenant(),vehicle_id=v.id).order_by(Location.sampled_at.desc()).limit(500).all();segments=route_segments(locations);events=SecurityEvent.query.filter_by(customer_id=tenant(),vehicle_id=v.id).order_by(SecurityEvent.created_at.desc()).limit(30);fuel=FuelObservation.query.filter_by(customer_id=tenant(),vehicle_id=v.id).order_by(FuelObservation.sampled_at.desc()).limit(30);diagnostics=Diagnostic.query.filter_by(customer_id=tenant(),vehicle_id=v.id).order_by(Diagnostic.sampled_at.desc()).first();assignment=DriverAssignment.query.filter_by(customer_id=tenant(),vehicle_id=v.id,ended_at=None).first();return render_template('vehicle_detail.html',v=v,devices=devices,locations=locations,segments=segments,events=events,fuel=fuel,diagnostics=diagnostics,assignment=assignment)
@bp.route('/drivers',methods=['GET','POST'])
@login_required
def drivers():
 if request.method=='POST':
  d=Driver(customer_id=tenant(),employee_no=request.form['employee_no'],name=request.form['name'],phone=request.form.get('phone'),licence_no=request.form.get('licence_no'),licence_code=request.form.get('licence_code'),licence_expiry=datetime.strptime(request.form['licence_expiry'],'%Y-%m-%d').date() if request.form.get('licence_expiry') else None);db.session.add(d)
  try:db.session.commit();flash('Driver added.','ok')
  except IntegrityError:db.session.rollback();flash('Employee number already exists.','error')
  return redirect(url_for('main.drivers'))
 rows=Driver.query.filter_by(customer_id=tenant()).order_by(Driver.name).all();active={x.driver_id:x for x in DriverAssignment.query.filter_by(customer_id=tenant(),ended_at=None)};return render_template('drivers.html',rows=rows,active=active)
@bp.route('/assignments',methods=['GET','POST'])
@login_required
def assignments():
 c=tenant()
 if request.method=='POST':
  vehicle_id=request.form.get('vehicle_id',type=int);driver_id=request.form.get('driver_id',type=int);DriverAssignment.query.filter_by(customer_id=c,vehicle_id=vehicle_id,ended_at=None).update({'ended_at':datetime.now(timezone.utc)});db.session.add(DriverAssignment(customer_id=c,vehicle_id=vehicle_id,driver_id=driver_id,start_odometer_km=request.form.get('start_odometer_km',type=float)));db.session.commit();flash('Driver assigned.','ok');return redirect(url_for('main.assignments'))
 rows=DriverAssignment.query.filter_by(customer_id=c).order_by(DriverAssignment.started_at.desc()).limit(200);return render_template('assignments.html',rows=rows,vehicles=Vehicle.query.filter_by(customer_id=c,status='ACTIVE').all(),drivers=Driver.query.filter_by(customer_id=c,active=True).all())
@bp.route('/devices',methods=['GET','POST'])
@login_required
def devices():
 c=tenant();new_token=None
 if request.method=='POST':
  caps={x:bool(request.form.get(x)) for x in ('location','ignition','external_power','backup_battery','tamper','fuel_level','can_j1939')};d=Device(customer_id=c,device_uid=request.form['device_uid'],vehicle_id=request.form.get('vehicle_id',type=int),device_type=request.form.get('device_type'),imei=request.form.get('imei') or None,iccid=request.form.get('iccid') or None,capabilities=caps);new_token=d.issue_token();db.session.add(d)
  try:db.session.commit();flash('Device registered. Copy the one-time token now.','ok')
  except IntegrityError:db.session.rollback();flash('Device UID, IMEI or ICCID already exists.','error');new_token=None
 rows=Device.query.filter_by(customer_id=c).order_by(Device.device_uid).all();return render_template('devices.html',rows=rows,vehicles=Vehicle.query.filter_by(customer_id=c).all(),new_token=new_token)
@bp.route('/geofences',methods=['GET','POST'])
@login_required
def geofences():
 if request.method=='POST':db.session.add(Geofence(customer_id=tenant(),name=request.form['name'],kind=request.form['kind'],latitude=request.form.get('latitude',type=float),longitude=request.form.get('longitude',type=float),radius_m=request.form.get('radius_m',type=float),severity=request.form.get('severity')));db.session.commit();flash('Geofence saved.','ok');return redirect(url_for('main.geofences'))
 return render_template('geofences.html',rows=Geofence.query.filter_by(customer_id=tenant()).all())
@bp.get('/tracking')
@login_required
def tracking():
 c=tenant();rows=[]
 for v in Vehicle.query.filter_by(customer_id=c,status='ACTIVE').order_by(Vehicle.fleet_no):
  p=Location.query.filter_by(customer_id=c,vehicle_id=v.id).order_by(Location.sampled_at.desc()).first();d=Device.query.filter_by(customer_id=c,vehicle_id=v.id,enabled=True).first();rows.append((v,p,d))
 return render_template('tracking.html',rows=rows)
@bp.route('/security',methods=['GET','POST'])
@login_required
def security():
 c=tenant()
 if request.method=='POST':
  x=SecurityEvent.query.filter_by(id=request.form.get('event_id',type=int),customer_id=c).first_or_404();action=request.form.get('action')
  if action=='ack':x.state='ACKNOWLEDGED';x.acknowledged_at=datetime.now(timezone.utc);x.acknowledged_by=current_user.id
  elif action=='resolve':x.state='RESOLVED';x.resolved_at=datetime.now(timezone.utc);x.resolution=request.form.get('resolution')
  elif action=='false':x.state='FALSE_ALARM';x.resolved_at=datetime.now(timezone.utc);x.resolution=request.form.get('resolution') or 'Marked false alarm'
  db.session.commit();return redirect(url_for('main.security'))
 rows=SecurityEvent.query.filter_by(customer_id=c).order_by(SecurityEvent.created_at.desc()).limit(500).all();return render_template('security.html',rows=rows)
@bp.route('/fuel',methods=['GET','POST'])
@login_required
def fuel():
 c=tenant()
 if request.method=='POST':db.session.add(FuelTransaction(customer_id=c,vehicle_id=request.form.get('vehicle_id',type=int),driver_id=request.form.get('driver_id',type=int),occurred_at=datetime.fromisoformat(request.form['occurred_at']),litres=request.form.get('litres',type=float),amount=request.form.get('amount',type=float),vendor=request.form.get('vendor'),reference=request.form.get('reference'),odometer_km=request.form.get('odometer_km',type=float)));db.session.commit();flash('Fuel transaction saved.','ok');return redirect(url_for('main.fuel'))
 obs=FuelObservation.query.filter_by(customer_id=c).order_by(FuelObservation.sampled_at.desc()).limit(300);tx=FuelTransaction.query.filter_by(customer_id=c).order_by(FuelTransaction.occurred_at.desc()).limit(300);return render_template('fuel.html',obs=obs,tx=tx,vehicles=Vehicle.query.filter_by(customer_id=c).all(),drivers=Driver.query.filter_by(customer_id=c,active=True).all())
@bp.route('/maintenance',methods=['GET','POST'])
@login_required
def maintenance():
 if request.method=='POST':db.session.add(MaintenanceIssue(customer_id=tenant(),vehicle_id=request.form.get('vehicle_id',type=int),title=request.form['title'],description=request.form.get('description'),severity=request.form.get('severity'),due_at=datetime.fromisoformat(request.form['due_at']) if request.form.get('due_at') else None));db.session.commit();return redirect(url_for('main.maintenance'))
 return render_template('maintenance.html',rows=MaintenanceIssue.query.filter_by(customer_id=tenant()).order_by(MaintenanceIssue.created_at.desc()).all(),vehicles=Vehicle.query.filter_by(customer_id=tenant()).all())
@bp.get('/diagnostics')
@login_required
def diagnostics():return render_template('diagnostics.html',rows=Diagnostic.query.filter_by(customer_id=tenant()).order_by(Diagnostic.sampled_at.desc()).limit(500).all())
@bp.get('/reports')
@login_required
def reports():return render_template('reports.html')
@bp.route('/api-studio',methods=['GET','POST'])
@login_required
def api_studio():
 c=tenant();new_key=None
 if request.method=='POST':
  raw='ft360_'+secrets.token_urlsafe(35);x=ApiCredential(customer_id=c,name=request.form['name'],key_prefix=raw[:10],key_hash=generate_password_hash(raw),scopes=request.form.getlist('scopes'));db.session.add(x);db.session.commit();new_key=raw
 return render_template('api_studio.html',credentials=ApiCredential.query.filter_by(customer_id=c).all(),webhooks=Webhook.query.filter_by(customer_id=c).all(),jobs=ImportJob.query.filter_by(customer_id=c).order_by(ImportJob.created_at.desc()).limit(40),new_key=new_key)
@bp.get('/imports/vehicles/template.csv')
@login_required
def vehicle_template():
 data='fleet_no,registration,vin,make,model,vehicle_class,tank_capacity_l\nTRK-0001,ABC123GP,VIN123,Volvo,FH,TRUCK,600\n';return send_file(io.BytesIO(data.encode()),mimetype='text/csv',as_attachment=True,download_name='fleettrack360_vehicle_import.csv')
