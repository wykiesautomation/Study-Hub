from datetime import datetime,timezone
from math import radians,sin,cos,asin,sqrt
from .models import db,SecurityEvent,Webhook,WebhookDelivery,FuelObservation,Location

def parse_time(value):
 if not value:return datetime.now(timezone.utc)
 d=datetime.fromisoformat(str(value).replace('Z','+00:00'));return d if d.tzinfo else d.replace(tzinfo=timezone.utc)
def km(a,b):
 lat1,lon1,lat2,lon2=map(radians,(a.latitude,a.longitude,b.latitude,b.longitude));v=sin((lat2-lat1)/2)**2+cos(lat1)*cos(lat2)*sin((lon2-lon1)/2)**2;return 12742.0176*asin(min(1,sqrt(v)))
def validate_location(p):
 e=[]
 try:
  lat=float(p['latitude']);lon=float(p['longitude'])
  if not -90<=lat<=90:e.append('latitude_range')
  if not -180<=lon<=180:e.append('longitude_range')
 except Exception:e.append('invalid_coordinates')
 if not p.get('sequence'):e.append('sequence_required')
 try:
  if p.get('accuracy_m') is not None and float(p['accuracy_m'])>200:e.append('poor_accuracy')
  if p.get('speed_kmh') is not None and float(p['speed_kmh'])>240:e.append('implausible_speed')
 except Exception:e.append('invalid_measurement')
 return e
def queue_webhooks(customer_id,event_type,event_id,payload):
 for hook in Webhook.query.filter_by(customer_id=customer_id,enabled=True):
  if event_type in (hook.events or []):db.session.add(WebhookDelivery(customer_id=customer_id,webhook_id=hook.id,event_type=event_type,event_id=str(event_id),payload=payload))
def create_event(customer_id,vehicle_id,event_type,severity='WARNING',confidence=None,detail=None,device_id=None,latitude=None,longitude=None):
 x=SecurityEvent(customer_id=customer_id,vehicle_id=vehicle_id,device_id=device_id,event_type=event_type,severity=severity,confidence=confidence,detail=detail or {},latitude=latitude,longitude=longitude);db.session.add(x);db.session.flush();queue_webhooks(customer_id,'security.event.created',x.id,{'id':x.id,'vehicle_id':vehicle_id,'event_type':event_type,'severity':severity});return x
def route_segments(rows):
 rows=sorted(rows,key=lambda x:(x.sampled_at,x.id or 0));segments=[];current=[];previous=None
 for p in rows:
  valid=(p.quality=='GOOD' and (p.accuracy_m is None or p.accuracy_m<=50))
  if previous and valid:
   sec=(p.sampled_at-previous.sampled_at).total_seconds();valid=0<sec<=120 and km(previous,p)<=2 and km(previous,p)/(sec/3600)<=180
  if not valid:
   if len(current)>=3:segments.append(current)
   current=[];previous=None;continue
  current.append(p);previous=p
 if len(current)>=3:segments.append(current)
 return segments
def detect_fuel_loss(device,obs):
 prev=FuelObservation.query.filter(FuelObservation.vehicle_id==device.vehicle_id,FuelObservation.id!=obs.id,FuelObservation.quality=='GOOD').order_by(FuelObservation.sampled_at.desc()).first()
 if not prev or prev.litres is None or obs.litres is None:return None
 drop=prev.litres-obs.litres
 if drop>=20 and not obs.ignition and (obs.speed_kmh or 0)<2:return create_event(device.customer_id,device.vehicle_id,'POSSIBLE_DIESEL_LOSS','CRITICAL',0.78,{'drop_litres':round(drop,1),'from_litres':prev.litres,'to_litres':obs.litres},device.id)
