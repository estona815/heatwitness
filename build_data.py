"""Build the small browser dataset from the unchanged NOAA source."""
from heatwitness import *

root=Path(__file__).parent
raw=(root/'data/KSM00047108.dly').read_bytes()
station,records=parse_tmax(raw.decode('ascii'))
payload={'station':station,'source_sha256':hashlib.sha256(raw).hexdigest(),
         'provenance':json.loads((root/'data/provenance.json').read_text()),'audits':{}}
for threshold in [300,320,350]:
    payload['audits'][str(threshold)]={str(y):audit(records,f'{y}-06-01',f'{y}-08-31',threshold) for y in range(2010,2026)}
(root/'audits.json').write_text(json.dumps(payload,separators=(',',':')))
print('Built',len(payload['audits'])*16,'source-derived summer audits')
