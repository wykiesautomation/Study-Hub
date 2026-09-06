from pathlib import Path
r=Path(__file__).parents[1]
text='\n'.join(p.read_text(errors='ignore') for p in r.rglob('*') if p.is_file() and '__pycache__' not in str(p))
def test_product_contracts():
 for x in ['/api/fleet/v1','locations/batch','fuel/observations/batch','diagnostics/batch','security/events','imports/vehicles','feed/<kind>']:
  assert x in text
def test_full_web_areas():
 for x in ['Fleet Overview','Live Tracking','Fleet Registry','Drivers','Assignments','Security Events','Geofences','Fuel & Diesel','Devices & Sources','Diagnostics','Maintenance','Fleet API Studio','Reports & Evidence']:
  assert x in text
def test_safety_contracts():
 for x in ['if len(current)>=3','POSSIBLE_DIESEL_LOSS','capability_not_supported','token_hash','queue_webhooks']:
  assert x in text
