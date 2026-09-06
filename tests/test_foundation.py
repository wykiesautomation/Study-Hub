from app import create_app
from app.models import db,Customer

def client():
 app=create_app(True);app.config['SQLALCHEMY_DATABASE_URI']='sqlite:///:memory:'
 with app.app_context():
  db.drop_all();db.create_all();db.session.add(Customer(id=1,name='Test Fleet',slug='test'));db.session.commit()
 return app.test_client()
def test_health():
 r=client().get('/api/fleet/v1/health');assert r.status_code==200 and r.json['version']=='v1'
def test_vehicle_create_and_list():
 c=client();r=c.post('/api/fleet/v1/vehicles',json={'fleet_no':'TRK-0001','registration':'ABC123GP'});assert r.status_code==201
 assert c.get('/api/fleet/v1/vehicles').json['data'][0]['fleet_no']=='TRK-0001'
def test_device_capability_gate():
 c=client();v=c.post('/api/fleet/v1/vehicles',json={'fleet_no':'TRK-0002'}).json['id'];d=c.post('/api/fleet/v1/devices/register',json={'device_uid':'DEV-1','vehicle_id':v,'capabilities':{'location':True}}).json
 r=c.post('/api/fleet/v1/fuel/observations/batch',headers={'Authorization':'Bearer '+d['device_token']},json={'observations':[]});assert r.status_code==409
def test_ui_pages():
 c=client()
 for path in ['/','/registry','/modules','/api-studio']:assert c.get(path).status_code==200
