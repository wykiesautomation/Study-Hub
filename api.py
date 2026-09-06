import csv,io,secrets
from datetime import datetime,timezone
from flask import Blueprint,request,jsonify
from sqlalchemy.exc import IntegrityError
from werkzeug.security import generate_password_hash,check_password_hash
from .models import *
from .services import parse_time,validate_location,create_event,detect_fuel_loss,queue_webhooks
api=Blueprint('fleet_api',__name__)
def cid():return int(request.headers.get('X-Customer-ID','1'))
def auth_device():
 raw=request.headers.get('Authorization','').removeprefix('Bearer ').strip();prefix=raw[:10]
 for d in Device.query.filter(Device.enabled.is_(True),Device.token_hash.isnot(None)).all():
  if d.verify_token(raw):return d
 return None
def api_credential(scope):
 raw=request.headers.get('X-API-Key','').strip()
 if not raw:return None
 prefix=raw[:10]
 for x in ApiCredential.query.filter_by(key_prefix=prefix,enabled=True):
  if check_password_hash(x.key_hash,raw) and scope in (x.scopes or []):x.last_used=datetime.now(timezone.utc);return x
 return None
@api.get('/health')
def health():return jsonify(status='ok',product='FleetTrack 360',api='Fleet API',version='1.0.0',time=datetime.now(timezone.utc).isoformat())
@api.route('/vehicles',methods=['GET','POST'])
def vehicles():
 customer=cid()
 if request.method=='GET':
  return jsonify(data=[{'id':v.id,'fleet_no':v.fleet_no,'registration':v.registration,'vin':v.vin,'make':v.make,'model':v.model,'year':v.year,'class':v.vehicle_class,'status':v.status,'tank_capacity_l':v.tank_capacity_l} for v in Vehicle.query.filter_by(customer_id=customer).order_by(Vehicle.fleet_no)])
 d=request.get_json() or {};v=Vehicle(customer_id=customer,fleet_no=d.get('fleet_no','').strip(),registration=d.get('registration'),vin=d.get('vin'),make=d.get('make'),model=d.get('model'),year=d.get('year'),vehicle_class=d.get('vehicle_class','TRUCK'),depot_id=d.get('depot_id'),group_id=d.get('group_id'),tank_capacity_l=d.get('tank_capacity_l'));db.session.add(v)
 try:db.session.commit();return jsonify(id=v.id),201
 except IntegrityError:db.session.rollback();return jsonify(error='duplicate_vehicle_identity'),409
@api.route('/vehicles/<int:vehicle_id>',methods=['GET','PATCH'])
def vehicle(vehicle_id):
 v=Vehicle.query.filter_by(id=vehicle_id,customer_id=cid()).first_or_404()
 if request.method=='GET':return jsonify(id=v.id,fleet_no=v.fleet_no,registration=v.registration,status=v.status)
 d=request.get_json() or {}
 for k in ('fleet_no','registration','vin','make','model','year','vehicle_class','depot_id','group_id','tank_capacity_l','status'):
  if k in d:setattr(v,k,d[k])
 db.session.commit();return jsonify(ok=True)
@api.route('/drivers',methods=['GET','POST'])
def drivers():
 customer=cid()
 if request.method=='GET':return jsonify(data=[{'id':x.id,'employee_no':x.employee_no,'name':x.name,'licence_expiry':x.licence_expiry.isoformat() if x.licence_expiry else None,'active':x.active,'driving_score':x.driving_score} for x in Driver.query.filter_by(customer_id=customer)])
 d=request.get_json() or {};x=Driver(customer_id=customer,employee_no=d['employee_no'],name=d['name'],phone=d.get('phone'),licence_no=d.get('licence_no'),licence_code=d.get('licence_code'));db.session.add(x);db.session.commit();return jsonify(id=x.id),201
@api.post('/assignments')
def assignment():
 d=request.get_json() or {};DriverAssignment.query.filter_by(customer_id=cid(),vehicle_id=d['vehicle_id'],ended_at=None).update({'ended_at':datetime.now(timezone.utc)});x=DriverAssignment(customer_id=cid(),vehicle_id=d['vehicle_id'],driver_id=d['driver_id'],start_odometer_km=d.get('start_odometer_km'));db.session.add(x);db.session.commit();return jsonify(id=x.id),201
@api.post('/devices/register')
def device_register():
 d=request.get_json() or {};x=Device(customer_id=cid(),device_uid=d['device_uid'],vehicle_id=d.get('vehicle_id'),device_type=d.get('device_type','GENERIC_REST'),imei=d.get('imei'),iccid=d.get('iccid'),firmware=d.get('firmware'),capabilities=d.get('capabilities',{}));token=x.issue_token();db.session.add(x)
 try:db.session.commit();return jsonify(id=x.id,device_uid=x.device_uid,device_token=token),201
 except IntegrityError:db.session.rollback();return jsonify(error='duplicate_device_identity'),409
@api.post('/locations/batch')
def locations_batch():
 dev=auth_device()
 if not dev:return jsonify(error='invalid_device_token'),401
 if not dev.vehicle_id:return jsonify(error='device_not_assigned'),409
 points=(request.get_json() or {}).get('points',[])
 if not isinstance(points,list) or not points:return jsonify(error='points_required'),400
 if len(points)>250:return jsonify(error='batch_too_large',maximum=250),413
 existing={x[0] for x in db.session.query(Location.sequence).filter(Location.device_id==dev.id,Location.sequence.in_([str(p.get('sequence')) for p in points])).all()};accepted=[];duplicates=[];rejected=[]
 for i,p in enumerate(points):
  seq=str(p.get('sequence',''))
  if seq in existing:duplicates.append(seq);continue
  errors=validate_location(p)
  if errors:rejected.append({'index':i,'sequence':seq,'errors':errors});continue
  x=Location(customer_id=dev.customer_id,vehicle_id=dev.vehicle_id,device_id=dev.id,sequence=seq,session_id=p.get('session_id'),sampled_at=parse_time(p.get('sampled_at') or p.get('timestamp')),latitude=float(p['latitude']),longitude=float(p['longitude']),accuracy_m=p.get('accuracy_m'),speed_kmh=p.get('speed_kmh'),heading_deg=p.get('heading_deg',p.get('heading')),altitude_m=p.get('altitude_m'),ignition=p.get('ignition'),quality='GOOD');db.session.add(x);accepted.append(seq);existing.add(seq)
 dev.last_seen=datetime.now(timezone.utc);dev.external_power=(points[-1].get('external_power') if points else dev.external_power);db.session.commit();return jsonify(accepted=accepted,duplicates=duplicates,rejected=rejected,accepted_count=len(accepted),duplicate_count=len(duplicates),rejected_count=len(rejected)),207 if rejected else 202
@api.post('/fuel/observations/batch')
def fuel_batch():
 dev=auth_device()
 if not dev:return jsonify(error='invalid_device_token'),401
 if not (dev.capabilities or {}).get('fuel_level'):return jsonify(error='capability_not_supported',capability='fuel_level'),409
 rows=(request.get_json() or {}).get('observations',[]);accepted=[]
 for p in rows:
  x=FuelObservation(customer_id=dev.customer_id,vehicle_id=dev.vehicle_id,device_id=dev.id,sequence=p.get('sequence'),sampled_at=parse_time(p.get('sampled_at')),litres=p.get('litres'),percent=p.get('percent'),source=p.get('source','SENSOR'),quality=p.get('quality','GOOD'),ignition=p.get('ignition'),speed_kmh=p.get('speed_kmh'));db.session.add(x);db.session.flush();detect_fuel_loss(dev,x);accepted.append(p.get('sequence'))
 db.session.commit();return jsonify(accepted=accepted,accepted_count=len(accepted)),202
@api.post('/diagnostics/batch')
def diag_batch():
 dev=auth_device()
 if not dev:return jsonify(error='invalid_device_token'),401
 if not (dev.capabilities or {}).get('can_j1939'):return jsonify(error='capability_not_supported',capability='can_j1939'),409
 rows=(request.get_json() or {}).get('observations',[])
 for p in rows:
  x=Diagnostic(customer_id=dev.customer_id,vehicle_id=dev.vehicle_id,device_id=dev.id,sampled_at=parse_time(p.get('sampled_at')),odometer_km=p.get('odometer_km'),engine_hours=p.get('engine_hours'),rpm=p.get('rpm'),coolant_c=p.get('coolant_c'),oil_pressure_kpa=p.get('oil_pressure_kpa'),battery_v=p.get('battery_v'),fuel_used_l=p.get('fuel_used_l'),idle_fuel_l=p.get('idle_fuel_l'),faults=p.get('faults',[]));db.session.add(x)
  if p.get('odometer_km') is not None:dev.vehicle.odometer_km=p['odometer_km']
  if p.get('engine_hours') is not None:dev.vehicle.engine_hours=p['engine_hours']
  for fault in p.get('faults',[]):
   if str(fault.get('state','ACTIVE')).upper()=='ACTIVE':db.session.add(MaintenanceIssue(customer_id=dev.customer_id,vehicle_id=dev.vehicle_id,title=f"Fault {fault.get('code','UNKNOWN')}",description=fault.get('description'),severity=fault.get('severity','WARNING'),source='DIAGNOSTIC'))
 db.session.commit();return jsonify(accepted_count=len(rows)),202
@api.route('/security/events',methods=['GET','POST'])
def events():
 customer=cid()
 if request.method=='GET':return jsonify(data=[{'id':x.id,'vehicle_id':x.vehicle_id,'event_type':x.event_type,'state':x.state,'severity':x.severity,'confidence':x.confidence,'created_at':x.created_at.isoformat()} for x in SecurityEvent.query.filter_by(customer_id=customer).order_by(SecurityEvent.created_at.desc()).limit(500)])
 d=request.get_json() or {};x=create_event(customer,d['vehicle_id'],d['event_type'],d.get('severity','WARNING'),d.get('confidence'),d.get('detail'));db.session.commit();return jsonify(id=x.id),201
@api.post('/security/events/<int:event_id>/acknowledge')
def event_ack(event_id):
 x=SecurityEvent.query.filter_by(id=event_id,customer_id=cid()).first_or_404();x.state='ACKNOWLEDGED';x.acknowledged_at=datetime.now(timezone.utc);db.session.commit();return jsonify(ok=True)
@api.post('/webhooks')
def webhook_create():
 d=request.get_json() or {};x=Webhook(customer_id=cid(),name=d.get('name'),url=d['url'],secret=secrets.token_urlsafe(32),events=d.get('events',[]));db.session.add(x);db.session.commit();return jsonify(id=x.id,signing_secret=x.secret),201
@api.post('/credentials')
def credential_create():
 d=request.get_json() or {};raw='ft360_'+secrets.token_urlsafe(35);x=ApiCredential(customer_id=cid(),name=d.get('name','Integration'),key_prefix=raw[:10],key_hash=generate_password_hash(raw),scopes=d.get('scopes',['fleet.read']));db.session.add(x);db.session.commit();return jsonify(id=x.id,api_key=raw,scopes=x.scopes),201
@api.post('/imports/vehicles')
def vehicle_import():
 customer=cid();text=request.get_data(as_text=True);rows=list(csv.DictReader(io.StringIO(text)));job=ImportJob(customer_id=customer,kind='VEHICLES',filename=request.headers.get('X-Filename'),total_rows=len(rows),state='VALIDATING');db.session.add(job);db.session.flush();errors=[];accepted=0;seen=set()
 for n,r in enumerate(rows,2):
  fleet=(r.get('fleet_no') or '').strip()
  if not fleet or fleet in seen:errors.append({'row':n,'error':'missing_or_duplicate_fleet_no'});continue
  seen.add(fleet);db.session.add(Vehicle(customer_id=customer,fleet_no=fleet,registration=(r.get('registration') or '').strip() or None,vin=(r.get('vin') or '').strip() or None,make=r.get('make'),model=r.get('model'),vehicle_class=r.get('vehicle_class') or 'TRUCK',tank_capacity_l=float(r['tank_capacity_l']) if r.get('tank_capacity_l') else None));accepted+=1
 try:db.session.flush();job.state='COMPLETED';job.accepted_rows=accepted;job.rejected_rows=len(errors);job.errors=errors;db.session.commit();return jsonify(job_id=job.id,accepted=accepted,rejected=len(errors),errors=errors),201
 except IntegrityError:db.session.rollback();return jsonify(error='database_identity_conflict'),409
@api.get('/feed/<kind>')
def feed(kind):
 customer=cid();cursor=max(0,int(request.args.get('cursor','0')));limit=min(1000,max(1,int(request.args.get('limit','250'))));model={'locations':Location,'events':SecurityEvent,'fuel':FuelObservation,'diagnostics':Diagnostic}.get(kind)
 if not model:return jsonify(error='unsupported_feed'),404
 rows=model.query.filter(model.customer_id==customer,model.id>cursor).order_by(model.id).limit(limit).all();data=[{'id':x.id,'vehicle_id':x.vehicle_id,'sampled_at':getattr(x,'sampled_at',getattr(x,'created_at',None)).isoformat()} for x in rows];return jsonify(data=data,next_cursor=str(rows[-1].id if rows else cursor),has_more=len(rows)==limit)
