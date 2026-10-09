"""Bundled Census lookup. No network calls and no member-location logging."""
import csv
import re
import unicodedata
from difflib import get_close_matches
from functools import lru_cache
from pathlib import Path

DATA = Path(__file__).resolve().parent / 'seed' / 'geo'

def normalize(text):
    return ' '.join(''.join(c for c in unicodedata.normalize('NFKD', text.casefold()) if not unicodedata.combining(c)).split())

def place_name(name):
    return re.sub(r' (?:city and borough|unified government|consolidated government|municipality|borough|village|town|city|CDP)$', '', name, flags=re.I)

@lru_cache(maxsize=1)
def _index():
    names, zips, states = {}, {}, {}
    for kind, filename in [('state','states.csv'),('place','places.csv'),('zcta','zcta.csv')]:
        with (DATA/filename).open(encoding='utf-8',newline='') as f:
            for row in csv.DictReader(f):
                name=place_name(row['name']) if kind=='place' else row['name']
                label=f"{row['zip']}, {row['state']}" if kind=='zcta' else f"{name}, {row['state']}" if kind=='place' else row['name']
                item=dict(name=name,state=row['state'],zip=row['zip'],latitude=float(row['latitude']),longitude=float(row['longitude']),kind=kind,label=label)
                if kind=='state':
                    states[normalize(name)]=item;states[normalize(row['state'])]=item
                elif kind=='zcta':zips.setdefault(row['zip'],[]).append(item)
                else:
                    for key in set([normalize(name),normalize(row['name'])]):names.setdefault(key,[]).append(item)
    return names,zips,states

def lookup(text):
    """Return exact candidates, or explicitly marked spelling suggestions. Never auto-correct."""
    if not isinstance(text,str) or not text.strip() or len(text)>120:return []
    names,zips,states=_index();q=normalize(text)
    if q in states:return [dict(states[q],match='exact')]
    state=None
    if ',' in q:
        q,st=map(str.strip,q.rsplit(',',1));state=states.get(st,{}).get('state',st.upper())
        if not re.fullmatch('[A-Z]{2}',state):return []
    elif re.search(r' [a-z]{2}$',q) and q[-2:] in states:
        q,st=q.rsplit(' ',1);state=states[st]['state']
    if re.fullmatch(r'\d{5}',q): candidates=zips.get(q,[]);match='exact'
    elif any(c.isdigit() for c in q):return []
    else:
        candidates=names.get(q,[]);match='exact'
        if not candidates:
            match='suggestion'
            candidates=[v for key in get_close_matches(q,names,n=5,cutoff=.78) for v in names[key]]
    return [dict(v,match=match) for v in candidates if not state or v['state']==state]
