#!/usr/bin/env python3
"""Gramadeg content builder (Nov 2026 overhaul).

Run from the repo root:  python3 tools/gramadeg_build.py

It reads gramadeg/content.json and
  1. applies small fixes to existing questions (FIXES),
  2. adds / replaces the Canolradd units written below (ids c1..c10),
  3. regenerates the drill bank (content["drills"]): hundreds of short questions made
     from rule tables x everyday vocabulary, so practice doesn't repeat the same items.
Safe to re-run: unit ids and drill ids are stable, so progress in the app is kept.
"""
import json, hashlib, os, sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'gramadeg')
PATH = os.path.join(ROOT, 'content.json')
VERSION = '2026-11-15'

# ---------------------------------------------------------------- mutations
DIGRAPHS = ('ch', 'dd', 'ff', 'ng', 'll', 'ph', 'rh', 'th')
SOFT = {'p': 'b', 't': 'd', 'c': 'g', 'b': 'f', 'd': 'dd', 'g': '', 'm': 'f', 'll': 'l', 'rh': 'r'}
NASAL = {'p': 'mh', 't': 'nh', 'c': 'ngh', 'b': 'm', 'd': 'n', 'g': 'ng'}
ASP = {'p': 'ph', 't': 'th', 'c': 'ch'}

def head(w):
    lw = w.lower()
    for d in DIGRAPHS:
        if lw.startswith(d):
            return d
    return lw[0]

def mutate(w, table, skip=()):
    h = head(w)
    if h not in table or h in skip:
        return w
    new = table[h] + w[len(h):]
    if w[0].isupper():
        new = new[0].upper() + new[1:]
    return new

soft = lambda w, skip=(): mutate(w, SOFT, skip)
nasal = lambda w: mutate(w, NASAL)
asp = lambda w: mutate(w, ASP)
VOWELS = 'aeiouwyâêîôûŵŷáéíóú'
def h_vowel(w):
    return ('h' + w) if w[0].lower() in VOWELS else w

def how(a, b, kind):
    if a == b:
        return f'{a} does not change here.'
    return f'{kind}: {a} → {b}.'

def qid(prefix, *parts):
    return prefix + '-' + hashlib.md5('|'.join(parts).encode('utf8')).hexdigest()[:7]

def pick(items, n, salt=''):
    """Deterministic sample: the same n items every run."""
    key = lambda x: hashlib.md5((salt + json.dumps(x, ensure_ascii=False, sort_keys=True)).encode('utf8')).hexdigest()
    return sorted(items, key=key)[:n]

DR = []
def drill(unit, skills, text, hint, en, answer, explain, alts=None, gender=None):
    q = {'id': qid('d-' + unit, text, hint, answer), 'type': 'type', 'unit': unit, 'text': text, 'hint': hint,
         'en': en, 'answer': answer, 'alts': list(dict.fromkeys(a for a in (alts or []) if a != answer)), 'explain': explain, 'skills': skills}
    if gender:
        q['gender'] = [{'w': w, 'g': g} for w, g in gender]
    DR.append(q)

# ---------------------------------------------------------------- vocabulary (from the Vocab 1000 deck)
# (Welsh, gender, English singular, English plural, kind)
NOUNS = [
 ('bwrdd','m','table','tables','thing'), ('car','m','car','cars','thing'), ('tŷ','m','house','houses','thing'),
 ('ci','m','dog','dogs','animal'), ('llyfr','m','book','books','thing'), ('drws','m','door','doors','thing'),
 ('gwely','m','bed','beds','thing'), ('crys','m','shirt','shirts','thing'), ('bag','m','bag','bags','thing'),
 ('tocyn','m','ticket','tickets','thing'), ('pentref','m','village','villages','place'), ('mynydd','m','mountain','mountains','place'),
 ('plentyn','m','child','children','person'), ('brawd','m','brother','brothers','person'), ('mab','m','son','sons','person'),
 ('papur','m','paper','papers','thing'), ('trên','m','train','trains','thing'), ('parc','m','park','parks','place'),
 ('capel','m','chapel','chapels','place'), ('castell','m','castle','castles','place'), ('gwesty','m','hotel','hotels','place'),
 ('dosbarth','m','class','classes','place'), ('cwestiwn','m','question','questions','idea'), ('gair','m','word','words','idea'),
 ('diwrnod','m','day','days','time'), ('mis','m','month','months','time'), ('cwpan','m','cup','cups','thing'),
 ('cath','f','cat','cats','animal'), ('cadair','f','chair','chairs','thing'), ('cegin','f','kitchen','kitchens','place'),
 ('ffenest','f','window','windows','thing'), ('pont','f','bridge','bridges','place'), ('tref','f','town','towns','place'),
 ('siop','f','shop','shops','place'), ('merch','f','girl','girls','person'), ('chwaer','f','sister','sisters','person'),
 ('braich','f','arm','arms','body'), ('coes','f','leg','legs','body'), ('llaw','f','hand','hands','body'),
 ('potel','f','bottle','bottles','thing'), ('cot','f','coat','coats','thing'), ('stryd','f','street','streets','place'),
 ('tafarn','f','pub','pubs','place'), ('punt','f','pound','pounds','money'), ('ceiniog','f','penny','pence','money'),
 ('munud','f','minute','minutes','time'), ('rhaglen','f','programme','programmes','idea'), ('ffilm','f','film','films','idea'),
 ('cân','f','song','songs','idea'), ('coeden','f','tree','trees','thing'), ('buwch','f','cow','cows','animal'),
 ('dafad','f','sheep','sheep','animal'), ('draig','f','dragon','dragons','animal'), ('llong','f','ship','ships','thing'),
 ('taith','f','journey','journeys','idea'), ('dinas','f','city','cities','place'), ('problem','f','problem','problems','idea'),
 ('neges','f','message','messages','idea'), ('tudalen','f','page','pages','thing'), ('swydd','f','job','jobs','idea'),
]
G = {'m': 'masculine', 'f': 'feminine'}

PLACES = ['Caerdydd','Bangor','Pontypridd','Tregaron','Dolgellau','Gwent','Machynlleth','Llanelli','Rhuthun','Penarth',
          'Caerfyrddin','Talybont','Bryste','Dinbych','Merthyr','Porthcawl','Trefynwy','Glynebwy','Manceinion','Llundain',
          'Caeredin','Dulyn','Abertawe','Aberystwyth','Wrecsam','Hwlffordd']

# ---------------------------------------------------------------- drills
def build_drills():
    # 1. soft mutation after i / o with place names
    items = []
    for p in PLACES:
        items.append(('i', "Dw i'n mynd i ___ yfory.", f"I'm going to {p} tomorrow.", p))
        items.append(('o', "Mae hi'n dod o ___ yn wreiddiol.", f"She comes from {p} originally.", p))
    for prep, text, en, p in pick(items, 34, 'g1'):
        a = soft(p)
        drill('u3', ['sm-prep', 'mut-soft' if a != p else 'mut-none'], text, p, en, a,
              f'{prep} causes soft mutation. ' + how(p, a, 'Soft'))

    # 2. soft mutation after am / heb / o with nouns
    items = []
    for cy, g, en, pl, kind in NOUNS:
        if kind in ('thing', 'place'):
            items.append(('am', "Dw i'n chwilio am ___.", f"I'm looking for a {en}.", cy))
        if cy in ('bag', 'tocyn', 'cot', 'car', 'llyfr', 'papur', 'crys', 'plentyn', 'ci', 'potel', 'cwpan', 'gair'):
            items.append(('heb', "Daeth e heb ___.", f"He came without a {en}.", cy))
    for prep, text, en, cy in pick(items, 30, 'g2'):
        a = soft(cy)
        drill('u3', ['sm-prep', 'mut-soft' if a != cy else 'mut-none'], text, cy, en, a,
              f'{prep} causes soft mutation. ' + how(cy, a, 'Soft'))

    # 3. yn (in) + place: nasal mutation, and yn changes too
    def yn_place(p):
        h = head(p)
        n = nasal(p)
        yn = {'c': 'yng', 'g': 'yng', 'p': 'ym', 'b': 'ym', 'm': 'ym'}.get(h, 'yn')
        return yn + ' ' + n
    frames = [("Dw i'n byw ___.", "I live in {}."), ("Mae hi'n gweithio ___.", "She works in {}."), ("Arhoson ni ___.", "We stayed in {}.")]
    for i, p in enumerate(PLACES):
        t, e = frames[i % 3]
        a = yn_place(p)
        changed = nasal(p) != p
        drill('p6', ['nas-yn', 'nas-yn-form', 'mut-nasal'] if changed else ['nas-yn', 'mut-none'] + (['nas-yn-form'] if a.startswith('ym') else []),
              t, 'yn + ' + p, e.format(p), a,
              (f'yn (in) causes nasal mutation: {p} → {nasal(p)}, and yn becomes {a.split()[0]} to match.' if changed
               else (f'm does not mutate, but yn still becomes ym before m.' if a.startswith('ym') else f'{head(p).upper() if len(head(p))==1 else head(p)} has no nasal mutation, so nothing changes.')))

    # 4. possessives x nouns
    POSS = [('fy', 'i', 'my', nasal, 'poss-fy', 'fy causes nasal mutation', 'mut-nasal'),
            ('dy', 'di', 'your', soft, 'poss-dy', 'dy causes soft mutation', 'mut-soft'),
            ('ei', 'e', 'his', soft, 'poss-ei-his', 'ei (his) causes soft mutation', 'mut-soft'),
            ('ei', 'hi', 'her', lambda w: h_vowel(asp(w)), 'poss-ei-her', 'ei (her) causes aspirate mutation (c, p, t) and adds h before a vowel', 'mut-aspirate'),
            ('ein', 'ni', 'our', h_vowel, 'poss-h-vowel', 'ein causes no mutation; it only adds h before a vowel', 'mut-none'),
            ('eich', 'chi', 'your (chi)', lambda w: w, 'poss-no-mut', 'eich causes no mutation', 'mut-none'),
            ('eu', 'nhw', 'their', h_vowel, 'poss-h-vowel', 'eu causes no mutation; it only adds h before a vowel', 'mut-none')]
    own = [n for n in NOUNS if n[4] in ('thing', 'person', 'body') or n[0] in ('ci', 'cath')] + [
        ('tad','m','father','','person'), ('mam','f','mother','','person'), ('enw','m','name','','thing'), ('ysgol','f','school','','place'),
        ('ardal','f','area','','place'), ('gwaith','m','work','','idea'), ('teulu','m','family','','person'), ('pen','m','head','','body'),
        ('ffrind','m','friend','','person'), ('arian','m','money','','thing'), ('desg','f','desk','','thing'), ('gardd','f','garden','','place')]
    items = [(i, n) for i in range(len(POSS)) for n in own]
    for i, n in pick(items, 70, 'g4'):
        w, post, en, fn, sk, why, mut = POSS[i]
        cy = n[0]
        a = fn(cy)
        drill('u4', [sk, mut if a != cy else 'mut-none'], f'{w} ___ {post}', cy, f'{en} {n[2]}', a, why + '. ' + how(cy, a, 'Here'))

    # 5. numbers 1-6 x nouns: gender must be known
    NUM = {1: ('one', 'un', 'un'), 2: ('two', 'dau', 'dwy'), 3: ('three', 'tri', 'tair'), 4: ('four', 'pedwar', 'pedair'),
           5: ('five', 'pum', 'pum'), 6: ('six', 'chwe', 'chwe')}
    def num_phrase(k, cy, g):
        w = NUM[k][1 if g == 'm' else 2]
        if k == 1:
            n = soft(cy, skip=('ll', 'rh')) if g == 'f' else cy
            why = 'un soft-mutates a feminine noun (not ll or rh)' if g == 'f' else 'un does not mutate a masculine noun'
        elif k == 2:
            n = soft(cy); why = f'{w} causes soft mutation'
        elif k == 3:
            n = asp(cy) if g == 'm' else cy
            why = 'tri causes aspirate mutation (c, p, t)' if g == 'm' else 'tair causes no mutation'
        elif k == 4:
            n = cy; why = f'{w} causes no mutation'
        elif k == 5:
            n = cy; why = 'pump becomes pum before a noun, with no mutation'
        else:
            n = asp(cy); why = 'chwech becomes chwe before a noun, with aspirate mutation (c, p, t)'
        return w + ' ' + n, why
    items = [(k, n) for k in NUM for n in NOUNS if n[4] != 'time' or n[0] in ('mis', 'munud')]
    for k, n in pick(items, 80, 'g5'):
        cy, g, en, pl = n[:4]
        a, why = num_phrase(k, cy, g)
        drill('u7', ['num-gender', 'num-mutation', 'num-singular'], '___', f'{k} + {cy}', f'{NUM[k][0]} {en if k == 1 else pl}', a,
              f'{cy} is {G[g]}. {why[0].upper() + why[1:]}. The noun stays singular after a number.', gender=[(cy, g)])

    # 6. y + noun + adjective: gender decides both mutations
    ADJ = {'thing': ['mawr', 'bach', 'newydd', 'coch', 'du', 'drud', 'rhad', 'glân', 'trwchus'],
           'place': ['mawr', 'bach', 'tawel', 'prysur', 'newydd', 'glân', 'prydferth', 'poblogaidd'],
           'person': ['bach', 'tal', 'tawel', 'caredig', 'doniol', 'prysur'],
           'animal': ['mawr', 'bach', 'du', 'tawel', 'diog', 'peryglus']}
    ADJ_EN = {'mawr': 'big', 'bach': 'small', 'newydd': 'new', 'coch': 'red', 'du': 'black', 'drud': 'expensive', 'rhad': 'cheap',
              'glân': 'clean', 'trwchus': 'thick', 'tawel': 'quiet', 'prysur': 'busy', 'prydferth': 'beautiful', 'poblogaidd': 'popular',
              'tal': 'tall', 'caredig': 'kind', 'doniol': 'funny', 'diog': 'lazy', 'peryglus': 'dangerous'}
    items = []
    for cy, g, en, pl, kind in NOUNS:
        if kind not in ADJ or cy[0] in VOWELS or (g == 'f' and head(cy) == 'g') or (cy == 'llyfr'):
            continue
        for adj in pick(ADJ[kind], 2, cy):
            if adj == 'trwchus' and cy not in ('cot', 'papur'):
                continue
            items.append((cy, g, en, adj))
    items.append(('llyfr', 'm', 'book', 'trwchus'))
    for cy, g, en, adj in pick(items, 60, 'g6'):
        if g == 'f':
            n, a2 = soft(cy, skip=('ll', 'rh')), soft(adj)
            why = f'{cy} is feminine: it soft-mutates after y' + (' (but ll and rh resist)' if n == cy and head(cy) in ('ll', 'rh') else '') + ', and so does the adjective after it.'
        else:
            n, a2 = cy, adj
            why = f'{cy} is masculine: no mutation of the noun or the adjective.'
        drill('u3', ['sm-gender', 'sm-fem-noun', 'sm-fem-adj'], 'y ___', f'{cy} + {adj}', f'the {ADJ_EN[adj]} {en}', f'{n} {a2}', why, gender=[(cy, g)])
    PLUR = [('cathod', 'cath', 'cats', 'bach'), ('cadeiriau', 'cadair', 'chairs', 'coch'), ('merched', 'merch', 'girls', 'tal'),
            ('siopau', 'siop', 'shops', 'bach'), ('trefi', 'tref', 'towns', 'mawr'), ('pontydd', 'pont', 'bridges', 'newydd'),
            ('poteli', 'potel', 'bottles', 'mawr'), ('coed', 'coeden', 'trees', 'tal')]
    for plc, sg, en, adj in PLUR:
        drill('p15', ['gender-mut', 'mut-none'], 'y ___', f'{plc} + {adj}', f'the {ADJ_EN[adj]} {en}', f'{plc} {adj}',
              f'{sg} is feminine, but only the singular mutates. Plurals do not mutate after y, and neither does the adjective.')

    # 7. yn + adjective (soft, but not ll / rh)
    PRED = [("Mae'r cawl yn ___.", 'poeth', 'The soup is hot.'), ("Mae'r pentref yn ___.", 'tawel', 'The village is quiet.'),
            ("Mae'r bws yn ___.", 'llawn', 'The bus is full.'), ("Mae'r tocyn yn ___.", 'rhad', 'The ticket is cheap.'),
            ("Mae'r car yn ___.", 'drud', 'The car is expensive.'), ("Mae'r ystafell yn ___.", 'glân', 'The room is clean.'),
            ("Mae'r gwaith yn ___.", 'caled', 'The work is hard.'), ("Mae'r adeilad yn ___.", 'mawr', 'The building is big.'),
            ("Mae'r ffilm yn ___.", 'diddorol', 'The film is interesting.'), ("Mae'r dŵr yn ___.", 'cynnes', 'The water is warm.'),
            ("Mae'r bwyd yn ___.", 'blasus', 'The food is tasty.'), ("Mae'r stryd yn ___.", 'prysur', 'The street is busy.'),
            ("Mae'r bag yn ___.", 'trwm', 'The bag is heavy.'), ("Mae'r ffordd yn ___.", 'peryglus', 'The road is dangerous.'),
            ("Mae'r botel yn ___.", 'gwag', 'The bottle is empty.'), ("Mae'r tywydd yn ___.", 'braf', 'The weather is fine.'),
            ("Mae'r cwestiwn yn ___.", 'pwysig', 'The question is important.'), ("Mae'r mynydd yn ___.", 'uchel', 'The mountain is high.'),
            ("Mae'r afon yn ___.", 'llydan', 'The river is wide.'), ("Mae'r gadair yn ___.", 'cyfforddus', 'The chair is comfortable.'),
            ("Mae'r rhaglen yn ___.", 'doniol', 'The programme is funny.'), ("Mae'r plant yn ___.", 'hapus', 'The children are happy.'),
            ("Mae'r llyfr yn ___.", 'da', 'The book is good.'), ("Mae'r nos yn ___.", 'tywyll', 'The night is dark.'),
            ("Mae'r siocled yn ___.", 'melys', 'The chocolate is sweet.'), ("Mae'r dyn yn ___.", 'tal', 'The man is tall.'),
            ("Mae'r gegin yn ___.", 'brwnt', 'The kitchen is dirty.'), ("Mae'r swydd yn ___.", 'diflas', 'The job is boring.'),
            ("Mae'r plentyn yn ___.", 'bach', 'The child is small.'), ("Mae'r gacen yn ___.", 'ffres', 'The cake is fresh.')]
    for text, adj, en in PRED:
        if adj == 'braf':
            drill('u3', ['sm-yn-pred', 'sm-exceptions'], text, adj, en, adj, 'braf is one of the few adjectives that never mutates.')
            continue
        a = soft(adj, skip=('ll', 'rh'))
        ex = head(adj) in ('ll', 'rh')
        drill('u3', ['sm-exceptions'] if ex else ['sm-yn-pred', 'mut-soft' if a != adj else 'mut-none'], text, adj, en, a,
              'Exception: ll and rh do not mutate after yn.' if ex else 'yn + adjective causes soft mutation. ' + how(adj, a, 'Soft'))

    # 8. aspirate mutation after a (and) and gyda
    PAIRS = [('bara', 'caws', 'bread and cheese'), ('halen', 'pupur', 'salt and pepper'), ('te', 'coffi', 'tea and coffee'),
             ('ci', 'cath', 'a dog and a cat'), ('mam', 'tad', 'mother and father'), ('papur', 'pensil', 'paper and a pencil'),
             ('pysgod', 'sglodion', 'fish and chips'), ('cyllell', 'fforc', 'a knife and fork'), ('brawd', 'chwaer', 'a brother and sister'),
             ('bws', 'trên', 'a bus and a train'), ('haul', 'glaw', 'sun and rain'), ('coffi', 'te', 'coffee and tea'),
             ('te', 'cacen', 'tea and cake'), ('tad', 'mam', 'father and mother'), ('ceir', 'bysiau', 'cars and buses'),
             ('gwin', 'cwrw', 'wine and beer'), ('mab', 'merch', 'a son and daughter'), ('car', 'tŷ', 'a car and a house'),
             ('bore', 'prynhawn', 'morning and afternoon'), ('cŵn', 'cathod', 'dogs and cats'), ('llaeth', 'siwgr', 'milk and sugar'),
             ('bwrdd', 'cadair', 'a table and a chair'), ('sglodion', 'pys', 'chips and peas'), ('glaw', 'gwynt', 'rain and wind')]
    for a1, b, en in PAIRS:
        ans = asp(b)
        drill('p7', ['asp-a', 'mut-aspirate' if ans != b else 'mut-none'], f'{a1} a ___', b, en, ans,
              'a (and) causes aspirate mutation of c, p, t. ' + how(b, ans, 'Aspirate'))
    WITH = [('Tad-cu', 'Grandad', ''), ('plant', 'children', ''), ('ffrind', 'a friend', ''), ('cariad', 'a partner', ''),
            ('teulu', 'family', ''), ('pawb', 'everyone', ''), ('Mam', 'Mum', ''), ('tri', 'three of them', ''),
            ('cydweithwyr', 'colleagues', ''), ('pobl', 'people', ''), ('Tom', 'Tom', ''), ('Carys', 'Carys', '')]
    for w, en, _ in WITH:
        ans = asp(w)
        txt = 'Es i yno gyda ___' + (' ohonyn nhw.' if w == 'tri' else '.')
        drill('p7', ['asp-other', 'mut-aspirate' if ans != w else 'mut-none'], txt, w, f'I went there with {en}.', ans,
              'gyda causes aspirate mutation of c, p, t. ' + how(w, ans, 'Aspirate'))

    # 9. past tense: regular verbs
    VERBS = [('prynu', 'pryn', 'y car', 'bought the car'), ('talu', 'tal', 'y bil', 'paid the bill'), ('canu', 'can', 'y gân', 'sang the song'),
             ('dysgu', 'dysg', 'y geiriau', 'learned the words'), ('darllen', 'darllen', 'y llyfr', 'read the book'),
             ('ysgrifennu', 'ysgrifenn', 'y llythyr', 'wrote the letter'), ('bwyta', 'bwyt', 'y gacen', 'ate the cake'),
             ('yfed', 'yf', 'y coffi', 'drank the coffee'), ('gweld', 'gwel', 'y ffilm', 'saw the film'),
             ('clywed', 'clyw', 'y newyddion', 'heard the news'), ('gwylio', 'gwyli', 'y gêm', 'watched the game'),
             ('cofio', 'cofi', 'y stori', 'remembered the story'), ('agor', 'agor', 'y drws', 'opened the door'),
             ('cau', 'cae', 'y ffenest', 'closed the window'), ('colli', 'coll', 'y bws', 'missed the bus'),
             ('ennill', 'enill', 'y gêm', 'won the game'), ('gadael', 'gadaw', 'y tŷ', 'left the house'),
             ('gorffen', 'gorffenn', 'y gwaith', 'finished the work'), ('dechrau', 'dechreu', 'y cwrs', 'started the course'),
             ('gwerthu', 'gwerth', 'y car', 'sold the car'), ('golchi', 'golch', 'y llestri', 'washed the dishes'),
             ('anfon', 'anfon', 'y neges', 'sent the message'), ('ateb', 'ateb', 'y cwestiwn', 'answered the question'),
             ('helpu', 'help', 'y plant', 'helped the children'), ('trefnu', 'trefn', 'y parti', 'organised the party'),
             ('coginio', 'cogini', 'y swper', 'cooked the supper'), ('codi', 'cod', 'y plant', 'picked up the children'),
             ('cyrraedd', 'cyrhaedd', 'y gwesty', 'reached the hotel'), ('aros', 'arhos', 'am y bws', 'waited for the bus'),
             ('edrych', 'edrych', 'ar y map', 'looked at the map')]
    PERS = [('i', 'I', 'ais', ['es']), ('ti', 'You', 'aist', ['est']), ('e', 'He', 'odd', []), ('hi', 'She', 'odd', []),
            ('ni', 'We', 'on', []), ('chi', 'You (chi)', 'och', []), ('nhw', 'They', 'on', [])]
    items = [(v, p) for v in VERBS for p in PERS]
    for v, p in pick(items, 70, 'g9'):
        vn, stem, obj, en = v
        pro, pen, end, alt = p
        form = (stem + end).capitalize()
        alts = [(stem + a).capitalize() for a in alt]
        alts += [soft(x) for x in [form] + alts]
        o = ("'r " + obj[2:]) if obj.startswith('y ') else ' ' + obj
        drill('u5', ['past-endings'], f'___ {pro}{o} ddoe.', f'{vn}, {pen.lower() if pen != "I" else "I"}', f'{pen} {en} yesterday.', form, alts=alts,
              explain=f'{vn} → stem {stem}- + {end}: {form} {pro}.')

    # 10. past tense: the irregular four
    IRR = {'mynd': (['Es', 'Est', 'Aeth', 'Aeth', 'Aethon', 'Aethoch', 'Aethon'], " i'r dre ddoe.", 'went to town yesterday'),
           'dod': (['Des', 'Dest', 'Daeth', 'Daeth', 'Daethon', 'Daethoch', 'Daethon'], " adre'n hwyr neithiwr.", 'came home late last night'),
           'cael': (['Ces', 'Cest', 'Cafodd', 'Cafodd', 'Cawson', 'Cawsoch', 'Cawson'], ' amser da.', 'had a good time'),
           'gwneud': (['Gwnes', 'Gwnest', 'Gwnaeth', 'Gwnaeth', 'Gwnaethon', 'Gwnaethoch', 'Gwnaethon'], "'r gwaith ddoe.", 'did the work yesterday')}
    IRR_ALT = {'Aeth': ['Âth'], 'Aethon': ['Ethon', 'Aethom'], 'Aethoch': ['Ethoch'], 'Daeth': ['Dath', 'Doth'],
               'Daethon': ['Dethon'], 'Daethoch': ['Dethoch'], 'Ces': ['Cefais'], 'Cest': ['Cefaist'], 'Cafodd': ['Caeth', 'Cas'],
               'Cawson': ['Ceson', 'Cawsom'], 'Cawsoch': ['Cesoch'], 'Gwnaeth': ['Gwnath', 'Nath'], 'Gwnaethon': ['Gwnaethom', 'Naethon'],
               'Gwnes': ['Nes'], 'Gwnest': ['Nest'], 'Gwnaethoch': ['Naethoch']}
    for vn, (forms, tail, en) in IRR.items():
        for (pro, pen, _, _), f in zip(PERS, forms):
            alts = IRR_ALT.get(f, [])
            alts = alts + [soft(x) for x in [f] + alts]
            drill('u5', ['past-irregular'], f'___ {pro}{tail}', f'{vn}, {pen if pen == "I" else pen.lower()}', f'{pen} {en}.', f, alts=alts,
                  explain=f'{vn} is irregular in the past: {f} {pro}.')

    # 11. bod in the imperfect, future and conditional
    PP = [('i', 'I'), ('ti', 'you'), ('hi', 'she'), ('ni', 'we'), ('chi', 'you (chi)'), ('nhw', 'they')]
    T = {
     'imp': ('p1', 'imp', "{} {}'n byw yno.", ['was', 'were', 'was', 'were', 'were', 'were'], 'living there',
             (["Ro'n", "Ro't", 'Roedd', "Ro'n", "Ro'ch", "Ro'n"], [['Roeddwn', "O'n"], ['Roeddet', "O't"], ["Ro'dd", "O'dd"], ['Roedden', "O'n"], ['Roeddech', "O'ch"], ['Roedden', "O'n", 'Roeddent']]),
             (["O'n", "O't", 'Oedd', "O'n", "O'ch", "O'n"], [['Oeddwn'], ['Oeddet'], ["O'dd"], ['Oedden'], ['Oeddech'], ['Oedden']]),
             (["Do'n", "Do't", 'Doedd', "Do'n", "Do'ch", "Do'n"], [['Doeddwn'], ['Doeddet'], ["Do'dd"], ['Doedden'], ['Doeddech'], ['Doedden']])),
     'fut': ('p2', 'fut', "{} {}'n barod yfory.", ['will be'] * 6, 'ready tomorrow',
             (['Bydda', 'Byddi', 'Bydd', 'Byddwn', 'Byddwch', 'Byddan'], [['Byddaf', 'Fydda'], ['Fyddi'], ['Fydd'], ['Fyddwn'], ['Fyddwch'], ['Byddant', 'Fyddan']]),
             (['Fydda', 'Fyddi', 'Fydd', 'Fyddwn', 'Fyddwch', 'Fyddan'], [['Fyddaf'], [], [], [], [], ['Fyddant']]),
             (['Fydda', 'Fyddi', 'Fydd', 'Fyddwn', 'Fyddwch', 'Fyddan'], [['Fyddaf'], [], [], [], [], ['Fyddant']])),
     'cond': ('p5', 'cond', "{} {}'n hapus yno.", ['would be'] * 6, 'happy there',
             (['Baswn', 'Baset', 'Basai', 'Basen', 'Basech', 'Basen'], [['Byddwn', 'Buaswn'], ['Byddet', 'Basat'], ['Base', 'Byddai', 'Bydde'], ['Bydden'], ['Byddech'], ['Bydden']]),
             (['Faswn', 'Faset', 'Fasai', 'Fasen', 'Fasech', 'Fasen'], [['Fyddwn', 'Fuaswn'], ['Fyddet', 'Fasat'], ['Fase', 'Fyddai', 'Fydde'], ['Fydden'], ['Fyddech'], ['Fydden']]),
             (['Faswn', 'Faset', 'Fasai', 'Fasen', 'Fasech', 'Fasen'], [['Fyddwn', 'Fuaswn'], ['Fyddet', 'Fasat'], ['Fase', 'Fyddai', 'Fydde'], ['Fydden'], ['Fyddech'], ['Fydden']])),
    }
    SK = {'imp': ('imp-statement', 'imp-question', 'imp-negative'), 'fut': ('fut-statement', 'fut-question', 'fut-negative'),
          'cond': ('cond-bod', 'cond-qneg', 'cond-qneg')}
    for key, (unit, _, frame, be, rest, st, qu, ng) in T.items():
        for i, (pro, pen) in enumerate(PP):
            body = frame.format('___', pro)
            drill(unit, [SK[key][0]], body, f'{pen} {be[i]}', f'{pen.capitalize()} {be[i]} {rest}.', st[0][i], alts=st[1][i],
                  explain=f'Statement, {pen}: {st[0][i]} {pro}.')
            drill(unit, [SK[key][1]], body[:-1] + '?', f'{be[i].split()[0]} {pen}…?', f'{be[i].split()[0].capitalize()} {pen} {(be[i].split()[1] + " ") if " " in be[i] else ""}{rest}?', qu[0][i], alts=qu[1][i],
                  explain=f'Question, {pen}: {qu[0][i]} {pro}?')
            neg = body.replace("'n ", ' ddim yn ')
            w = be[i].split()
            ne = (w[0] + "n't" if w[0] != 'will' else "won't") + (' ' + w[1] if len(w) > 1 else '')
            drill(unit, [SK[key][2]], neg, f'{pen} {ne}', f'{pen.capitalize()} {ne} {rest}.', ng[0][i], alts=ng[1][i],
                  explain=f'Negative, {pen}: {ng[0][i]} {pro} ddim.')

    # 12. inflected prepositions
    PR = [('i', 'me'), ('ti', 'you'), ('fe', 'him'), ('hi', 'her'), ('ni', 'us'), ('chi', 'you (chi)'), ('nhw', 'them')]
    PREPS = {
     'ar': ('p8', 'prep-ar', 'Edrychodd y plant ___ {}.', 'The children looked at {}.', ['arna', 'arnat', 'arno', 'arni', 'arnon', 'arnoch', 'arnyn'],
            {'arna': ['arnaf'], 'arnon': ['arnom'], 'arnyn': ['arnynt']}),
     'at': ('p8', 'prep-at', 'Anfonodd Siân neges ___ {}.', 'Siân sent a message to {}.', ['ata', 'atat', 'ato', 'ati', 'aton', 'atoch', 'atyn'],
            {'ata': ['ataf'], 'aton': ['atom'], 'atyn': ['atynt']}),
     'am': ('p8', 'prep-am', "Maen nhw'n siarad ___ {}.", "They're talking about {}.", ['amdana', 'amdanat', 'amdano', 'amdani', 'amdanon', 'amdanoch', 'amdanyn'],
            {'amdana': ['amdanaf'], 'amdanon': ['amdanom'], 'amdanyn': ['amdanynt']}),
     'wrth': ('p19', 'prep-wrth', 'Dwedodd Tom ___ {}.', 'Tom told {}.', ['wrtha', 'wrthot', 'wrtho', 'wrthi', 'wrthon', 'wrthoch', 'wrthyn'],
            {'wrtha': ['wrthyf', 'wrtho'], 'wrthot': ['wrthat', 'wrthyt'], 'wrthon': ['wrthym'], 'wrthyn': ['wrthynt']}),
     'o': ('p19', 'prep-o', 'Mae llun ___ {} ar y wal.', 'There is a picture of {} on the wall.', ['ohono', 'ohonot', 'ohono', 'ohoni', 'ohonon', 'ohonoch', 'ohonyn'],
            {'ohono': ['ohona', 'ohonof'], 'ohonot': ['ohonat'], 'ohonon': ['ohonom'], 'ohonyn': ['ohonynt']}),
     'heb': ('p19', 'prep-heb', 'Aeth y bws ___ {}.', 'The bus went without {}.', ['hebdda', 'hebddot', 'hebddo', 'hebddi', 'hebddon', 'hebddoch', 'hebddyn'],
            {'hebdda': ['hebddo', 'hebof'], 'hebddot': ['hebddat'], 'hebddon': ['hebom'], 'hebddyn': ['hebddynt']}),
     'dros': ('p19', 'prep-dros', 'Talodd Mam ___ {}.', 'Mum paid for {}.', ['drosta', 'drostat', 'drosto', 'drosti', 'droston', 'drostoch', 'drostyn'],
            {'drosta': ['drosto', 'drosof'], 'drostat': ['drostot'], 'droston': ['drosom'], 'drostyn': ['drostynt']}),
    }
    for prep, (unit, sk, frame, en, forms, alts) in PREPS.items():
        for (pro, pen), f in zip(PR, forms):
            a = list(alts.get(f, []))
            if prep == 'o' and pro == 'fe':
                a = []
            drill(unit, [sk], frame.format(pro), prep, en.format(pen), f, alts=a, explain=f'{prep} + {pro} → {f} {pro}.')
    for prep, forms in (('i', ['iddo', 'iddi', 'iddyn']), ('gan', ['ganddo', 'ganddi', 'ganddyn'])):
        for (pro, pen), f in zip([('fe', 'him'), ('hi', 'her'), ('nhw', 'them')], forms):
            if prep == 'i':
                drill('p19', ['prep-pattern'], f"Rhoddodd Siân y llyfr ___ {pro}.", prep, f'Siân gave the book to {pen}.', f,
                      explain=f'i only changes in the third person: {f} {pro}. (i fi, i ti, i ni, i chi stay as they are.)')
            else:
                drill('p19', ['prep-pattern'], f"Ces i anrheg ___ {pro}.", prep, f'I got a present from {pen}.', f, alts=[f + 't'] if pro == 'nhw' else [],
                      explain=f'gan + {pro} → {f} {pro}.')

    # 13. comparatives after yn
    CMP = [('tal', 'talach', 'taller'), ('byr', 'byrrach', 'shorter'), ('hen', 'hŷn', 'older'), ('ifanc', 'iau', 'younger'),
           ('rhad', 'rhatach', 'cheaper'), ('drud', 'drutach', 'more expensive'), ('gwlyb', 'gwlypach', 'wetter'), ('teg', 'tecach', 'fairer'),
           ('cryf', 'cryfach', 'stronger'), ('oer', 'oerach', 'colder'), ('poeth', 'poethach', 'hotter'), ('hapus', 'hapusach', 'happier'),
           ('pell', 'pellach', 'further'), ('hawdd', 'haws', 'easier'), ('da', 'gwell', 'better'), ('drwg', 'gwaeth', 'worse'),
           ('mawr', 'mwy', 'bigger'), ('bach', 'llai', 'smaller'), ('uchel', 'uwch', 'higher'), ('isel', 'is', 'lower'),
           ('cyflym', 'cyflymach', 'faster'), ('araf', 'arafach', 'slower'), ('tawel', 'tawelach', 'quieter'), ('trwm', 'trymach', 'heavier'),
           ('diddorol', 'mwy diddorol', 'more interesting'), ('peryglus', 'mwy peryglus', 'more dangerous'),
           ('cyfforddus', 'mwy cyfforddus', 'more comfortable'), ('pwysig', 'pwysicach', 'more important')]
    CMP_ALT = {'ifanc': ['ifancach', 'fwy ifanc'], 'hen': ['henach'], 'pwysig': ['fwy pwysig'], 'hawdd': ['hawsach'], 'drud': ['fwy drud'],
               'hapus': ['fwy hapus'], 'cyflym': ['fwy cyflym'], 'tawel': ['fwy tawel'], 'araf': ['fwy araf']}
    IRREG = ('hen', 'ifanc', 'hawdd', 'da', 'drwg', 'mawr', 'bach', 'uchel', 'isel')
    for adj, c, en in CMP:
        a = soft(c, skip=('ll', 'rh'))
        sk = 'cmp-irregular' if adj in IRREG else 'cmp-mwy' if c.startswith('mwy ') else 'cmp-ach'
        note = (f'{adj} → {c} (irregular).' if adj in IRREG else f'Long adjective: mwy + {adj}.' if c.startswith('mwy ') else f'{adj} → {c}.')
        note += (' After yn it soft-mutates: yn ' + a + '.') if a != c else ' No change after yn here.'
        drill('u8', [sk, 'cmp-yn-sm'], 'Mae hwn yn ___ na hwnna.', f'{adj}: comparative', f'This one is {en} than that one.', a,
              alts=CMP_ALT.get(adj, []), explain=note)

# ---------------------------------------------------------------- new units (hand-written)
def mc(i, prompt, en, answer, wrong, explain, skill, alts=None, noType=False):
    opts = [answer] + wrong.split('|')
    assert len(opts) == 6 and len(set(opts)) == 6, (i, opts)
    q = {'id': i, 'type': 'mc', 'prompt': prompt, 'en': en, 'options': opts, 'answer': 0, 'explain': explain, 'skills': [skill]}
    if alts: q['alts'] = alts
    if noType: q['noType'] = True
    return q
def ty(i, text, hint, en, answer, explain, skill, alts=None):
    assert '___' in text, i
    return {'id': i, 'type': 'type', 'text': text, 'hint': hint, 'en': en, 'answer': answer, 'alts': alts or [], 'explain': explain, 'skills': [skill]}
def ti(i, en, answer, distractors, explain, skill, alts=None):
    q = {'id': i, 'type': 'tiles', 'en': en, 'answer': answer, 'distractors': distractors.split('|'), 'explain': explain, 'skills': [skill]}
    if alts: q['alts'] = alts
    return q
def er(i, sentence, wrong, fix, explain, skill):
    s, f = sentence.split(' '), fix.split(' ')
    assert len(s) == len(f) and s[wrong] != f[wrong] and [a for k, a in enumerate(s) if k != wrong] == [a for k, a in enumerate(f) if k != wrong], (i, s, f)
    return {'id': i, 'type': 'error', 'sentence': sentence, 'wrong': wrong, 'fix': fix, 'explain': explain, 'skills': [skill]}

def yesno_unit():
    YES = ['Ydw', 'Do', 'Ie', 'Oes', 'Bydda', 'Oedd', 'Ydy', 'Baswn', 'Ydyn', "O'n"]
    NO = ['Nac ydw', 'Naddo', 'Nage', 'Nac oes', 'Na fydda', 'Nac oedd', 'Nac ydy', 'Na faswn', 'Nac ydyn', "Nac o'n"]
    ALT = {'Gwnaf': ['Gwna'], 'Bydda': ['Byddaf'], 'Nac ydw': ['Nag ydw'], 'Galla': ['Gallaf', 'Medra'], 'Na wnaf': ['Na wna'],
           'Na alla': ['Na allaf'], "O'n": ['Oeddwn'], "Nac o'n": ['Nac oeddwn', "Nag o'n"], 'Nac oes': ['Nag oes'], 'Nac oedd': ['Nag oedd'],
           'Nac ydy': ['Nag ydy', 'Nac ydi'], 'Nac ydyn': ['Nag ydyn'], 'Ydy': ['Ydi'], 'Basai': ['Base', 'Byddai'], 'Na fasai': ['Na fase', 'Na fyddai'],
           'Baswn': ['Byddwn'], 'Na faswn': ['Na fyddwn'], 'Na fydda': ['Na fyddaf']}
    ROWS = [
     ("Wyt ti'n hoffi coffi?", 'Yes, I do', 'Ydw', 'yn-bod', 'Present of bod, answering about me: Ydw.'),
     ("Wyt ti'n gweithio heddiw?", "No, I'm not", 'Nac ydw', 'yn-bod', 'Nac + the bod form for me: Nac ydw.'),
     ("Ydy Siân yn dod heno?", 'Yes, she is', 'Ydy', 'yn-bod', 'About her: Ydy.'),
     ("Ydy'r siop ar agor?", "No, it isn't", 'Nac ydy', 'yn-bod', 'About it: Nac ydy.'),
     ("Ydyn nhw'n byw yma?", 'Yes, they do', 'Ydyn', 'yn-bod', 'About them: Ydyn.'),
     ("Dych chi'n barod, blant?", 'Yes, we are', 'Ydyn', 'yn-bod', 'Chi asked of several people is answered for us: Ydyn.'),
     ("Ydw i'n hwyr?", 'Yes, you are (ti)', 'Wyt', 'yn-bod', 'The answer is about you: Wyt.'),
     ("Oes car gyda ti?", 'Yes', 'Oes', 'yn-bod', 'An Oes question is answered Oes / Nac oes, whoever it is about.'),
     ("Oes llaeth yn yr oergell?", 'No', 'Nac oes', 'yn-bod', 'Oes…? → Nac oes.'),
     ("Wyt ti wedi bwyta?", 'Yes, I have', 'Ydw', 'yn-bod', 'The perfect (wedi) is built on bod, so it is Ydw, not Do.'),
     ("Ydy'r bws wedi mynd?", "No, it hasn't", 'Nac ydy', 'yn-bod', 'Wedi uses bod: Nac ydy. Naddo is only for the short past.'),
     ("O't ti'n byw yng Nghaerdydd?", 'Yes, I was', "O'n", 'yn-imp', "Imperfect, about me: O'n."),
     ("Oedd hi'n oer ddoe?", 'Yes, it was', 'Oedd', 'yn-imp', 'Imperfect, about it: Oedd.'),
     ("Oedd Tom yn y cyfarfod?", "No, he wasn't", 'Nac oedd', 'yn-imp', 'Imperfect: Nac oedd.'),
     ("O'ch chi'n hapus yno, Mrs Jones?", "No, I wasn't", "Nac o'n", 'yn-imp', "Polite chi to one person is answered for me: Nac o'n."),
     ("Est ti i'r gwaith ddoe?", 'Yes', 'Do', 'yn-do', 'Short past: Do, for every person.'),
     ("Welodd hi'r ffilm?", 'No', 'Naddo', 'yn-do', 'Short past: Naddo, for every person.'),
     ("Brynoch chi fara?", 'Yes, we did', 'Do', 'yn-do', 'Short past: Do, for every person.'),
     ("Gawson nhw amser da?", 'No', 'Naddo', 'yn-do', 'Short past: Naddo.'),
     ("Fyddi di yno yfory?", 'Yes, I will', 'Bydda', 'yn-fut', 'Future of bod, about me: Bydda.'),
     ("Fydd hi'n braf yfory?", 'Yes, it will', 'Bydd', 'yn-fut', 'Future, about it: Bydd.'),
     ("Fyddan nhw'n dod?", "No, they won't", 'Na fyddan', 'yn-fut', 'Na + soft mutation: Na fyddan.'),
     ("Fyddwch chi'n barod erbyn saith?", 'Yes, we will', 'Byddwn', 'yn-fut', 'Answering for us: Byddwn.'),
     ("Fyddi di'n gweithio dydd Sadwrn?", "No, I won't", 'Na fydda', 'yn-fut', 'Na + soft mutation: Na fydda.'),
     ("Faset ti'n hoffi dod?", 'Yes, I would', 'Baswn', 'yn-cond', 'Conditional of bod, about me: Baswn.'),
     ("Fasai fe'n helpu?", "No, he wouldn't", 'Na fasai', 'yn-cond', 'Na + soft mutation: Na fasai.'),
     ("Hoffet ti baned?", 'Yes, I would', 'Hoffwn', 'yn-cond', 'Answer with the same verb: Hoffwn.'),
     ("Wnei di helpu?", 'Yes, I will', 'Gwnaf', 'yn-short', 'Wnei di? is answered with gwneud: Gwnaf (Gwna in speech).'),
     ("Wnewch chi agor y drws?", "No, I won't", 'Na wnaf', 'yn-short', 'Na + soft mutation of gwnaf: Na wnaf.'),
     ("Ga i ddod gyda chi?", 'Yes, you may (ti)', 'Cei', 'yn-short', 'Ga i? is answered with cael, about you: Cei.'),
     ("Ga i barcio yma?", 'No, you may not (ti)', 'Na chei', 'yn-short', 'Na + aspirate mutation of cei: Na chei.'),
     ("Gawn ni ddechrau?", 'Yes, you may (chi)', 'Cewch', 'yn-short', 'Permission given to several people: Cewch.'),
     ("Alli di ddod heno?", 'Yes, I can', 'Galla', 'yn-short', 'Alli di? is answered with gallu, about me: Galla.'),
     ("Allwch chi helpu, Mr Evans?", "No, I can't", 'Na alla', 'yn-short', 'Na + soft mutation (g drops): Na alla.'),
     ("Ddylwn i ffonio?", 'Yes, you should (ti)', 'Dylet', 'yn-short', 'Answer with the same verb, about you: Dylet.'),
     ("Ti sy'n gyrru heno?", 'Yes', 'Ie', 'yn-ie', 'The question does not start with a verb, so the answer is Ie / Nage.'),
     ("Athro wyt ti?", 'No', 'Nage', 'yn-ie', 'Not verb-first (Athro…): Nage.'),
     ("Yng Nghaerdydd dych chi'n byw?", 'Yes', 'Ie', 'yn-ie', 'Not verb-first (a place first): Ie.'),
     ("Coffi dych chi eisiau?", 'No', 'Nage', 'yn-ie', 'Not verb-first (a noun first): Nage.'),
     ("Siân yw dy enw di?", 'Yes', 'Ie', 'yn-ie', 'Not verb-first (a name first): Ie.'),
     ("Oes rhaid i fi fynd?", 'Yes', 'Oes', 'yn-bod', 'Oes rhaid…? → Oes / Nac oes.'),
     ("Oedd llawer o bobl yno?", 'Yes', 'Oedd', 'yn-imp', 'Oedd…? (was there) → Oedd.'),
    ]
    qs = []
    for n, (q, who, ans, sk, why) in enumerate(ROWS):
        pool = [x for x in (NO if ans.startswith('Na') else YES) if x != ans]
        pool = pool[n % len(pool):] + pool[:n % len(pool)]
        qs.append(mc(f'c1-{n+1:02d}', f'{q} ({who})', '', ans, '|'.join(pool[:5]), why, sk, alts=ALT.get(ans)))
    return qs

def units():
    U = []
    U.append(dict(id='c1', section='verbs', icon='check', colour='#0EA5E9', title='Yes and no, every tense', subtitle='Ydw, Do, Bydda, Cei, Ie',
      term='Echo answers', termDef="Welsh has no single word for yes or no. You answer by echoing the verb of the question, in the form for whoever the answer is about. That makes the answer a quick test of whether you heard the tense and the person.",
      rule="""<p><b>Rule: answer with the verb of the question, for the person the answer is about.</b> No = <i>Na / Nac</i> + that verb.</p>
<table><tr><th>Question starts with</th><th>Yes</th><th>No</th></tr>
<tr><td>Wyt ti…? / Dych chi…? (present, and wedi)</td><td>Ydw (I) / Ydyn (we)</td><td>Nac ydw / Nac ydyn</td></tr>
<tr><td>Ydy e / hi…?  Ydyn nhw…?</td><td>Ydy / Ydyn</td><td>Nac ydy / Nac ydyn</td></tr>
<tr><td>Oes…? (is there / have you got)</td><td>Oes</td><td>Nac oes</td></tr>
<tr><td>O't ti…? Oedd e…? (imperfect)</td><td>O'n / Oedd</td><td>Nac o'n / Nac oedd</td></tr>
<tr><td>Short past: Est ti…? Welodd hi…?</td><td>Do</td><td>Naddo</td></tr>
<tr><td>Fyddi di…? Fydd hi…? (future)</td><td>Bydda / Bydd</td><td>Na fydda / Na fydd</td></tr>
<tr><td>Faset ti…? Hoffet ti…? (conditional)</td><td>Baswn / Hoffwn</td><td>Na faswn / Na hoffwn</td></tr>
<tr><td>Wnei di…? Ga i…? Alli di…?</td><td>Gwnaf / Cei / Galla</td><td>Na wnaf / Na chei / Na alla</td></tr>
<tr><td>Anything that isn't a verb first: <i>Ti sy'n…? Athro wyt ti?</i></td><td>Ie</td><td>Nage</td></tr></table>
<p><b>Traps.</b> <i>Wyt ti wedi bwyta?</i> uses bod, so <i>Ydw</i>, not Do. <i>Na</i> causes soft mutation (<i>Na fydda</i>) but aspirate for c, p, t (<i>Na chei</i>).</p>""",
      questions=yesno_unit()))

    U.append(dict(id='c2', section='verbs', icon='layers', colour='#8B5CF6', title='Passive with cael', subtitle='Ces i fy ngeni, cafodd ei adeiladu',
      term='Passive voice', termDef="In a passive sentence the subject has the action done to it: 'The house was built'. Spoken Welsh builds it with cael (to get): literally 'The house got its building'.",
      rule="""<p><b>Equation: cael (in any tense) + possessive + verbnoun.</b> The possessive matches the subject and brings its usual mutation.</p>
<table><tr><th>Subject</th><th>Past passive</th><th>Mutation</th></tr>
<tr><td>I</td><td>Ces i <i>fy ngeni</i></td><td>fy + nasal</td></tr><tr><td>you</td><td>Cest ti <i>dy eni</i></td><td>dy + soft</td></tr>
<tr><td>he / masculine noun</td><td>Cafodd e <i>ei eni</i>; Cafodd y tŷ <i>ei godi</i></td><td>ei + soft</td></tr>
<tr><td>she / feminine noun</td><td>Cafodd hi <i>ei geni</i>; Cafodd y bont <i>ei chodi</i></td><td>ei + aspirate</td></tr>
<tr><td>we / you / they</td><td>Cawson ni <i>ein talu</i>; Cawson nhw <i>eu talu</i></td><td>none (h before a vowel)</td></tr></table>
<p><b>Other tenses:</b> change only cael. <i>Mae'r car yn cael ei drwsio</i> (is being repaired). <i>Bydd y gwaith yn cael ei wneud</i> (will be done). <i>Mae'r tŷ wedi cael ei werthu</i> (has been sold).</p>
<p><b>By</b> = <i>gan</i>: <i>Cafodd y llyfr ei ysgrifennu gan Kate Roberts.</i></p>""",
      questions=[
       mc('c2-01', 'I was born in Cardiff.', '', 'Ces i fy ngeni yng Nghaerdydd.', "Ces i fy geni yng Nghaerdydd.|Ro'n i fy ngeni yng Nghaerdydd.|Ces i ei eni yng Nghaerdydd.|Ces i fy ngeni mewn Caerdydd.|Ces i geni yng Nghaerdydd.", 'Cael + fy + nasal mutation: geni → ngeni.', 'pas-cael', alts=['Ges i fy ngeni yng Nghaerdydd.', 'Cefais i fy ngeni yng Nghaerdydd.']),
       ty('c2-02', 'Cafodd y bont ei ___ yn 1900. (codi)', 'codi', 'The bridge was built in 1900.', 'chodi', 'Pont is feminine, so ei is "her": aspirate mutation, c → ch.', 'pas-poss'),
       ty('c2-03', 'Cafodd e ei ___ yn Abertawe. (geni)', 'geni', 'He was born in Swansea.', 'eni', 'ei (his) + soft mutation: g drops, geni → eni.', 'pas-poss'),
       ty('c2-04', 'Cafodd hi ei ___ yn Abertawe. (geni)', 'geni', 'She was born in Swansea.', 'geni', 'ei (her) takes the aspirate mutation, which only affects c, p, t. Geni stays.', 'pas-poss'),
       ty('c2-05', 'Cafodd y llythyr ei ___ ddoe. (postio)', 'postio', 'The letter was posted yesterday.', 'bostio', 'Llythyr is masculine: ei (his) + soft mutation, p → b.', 'pas-poss'),
       mc('c2-06', 'The car is being repaired.', '', "Mae'r car yn cael ei drwsio.", "Mae'r car yn cael ei trwsio.|Mae'r car wedi cael ei drwsio.|Mae'r car yn ei drwsio.|Cafodd y car ei drwsio.|Mae'r car yn cael ei thrwsio.", 'Is being = mae … yn cael. Car is masculine: ei + soft, trwsio → drwsio.', 'pas-tense'),
       mc('c2-07', 'Cawson nhw eu talu ddoe.', '', 'They were paid yesterday.', 'They paid yesterday.|They are being paid today.|They had to pay yesterday.|We were paid yesterday.|They will be paid tomorrow.', 'Cawson nhw + eu + verbnoun = they were …ed.', 'pas-cael', noType=True),
       ty('c2-08', "Ces i fy ___ i'r parti. (gwahodd)", 'gwahodd', 'I was invited to the party.', 'ngwahodd', 'fy + nasal mutation: g → ng.', 'pas-poss'),
       ty('c2-09', 'Cawson ni ein ___ gan y plant. (helpu)', 'helpu', 'We were helped by the children.', 'helpu', 'ein causes no mutation (it only adds h before a vowel).', 'pas-poss'),
       er('c2-10', 'Cafodd y ffilm ei wneud yng Nghymru y llynedd.', 4, 'Cafodd y ffilm ei gwneud yng Nghymru y llynedd.', 'Ffilm is feminine, so ei is "her": no soft mutation. Gwneud stays.', 'pas-poss'),
       ti('c2-11', 'The work will be done tomorrow.', 'Bydd y gwaith yn cael ei wneud yfory', "gwneud|Mae|wedi|fy", 'Future passive: bydd … yn cael ei + soft mutation.', 'pas-tense'),
       mc('c2-12', 'Cafodd y ffenest ei thorri ___ y bechgyn.', 'The window was broken by the boys.', 'gan', 'wrth|gyda|drwy|o|i', 'By (the doer) in a passive = gan.', 'pas-cael'),
      ]))

    U.append(dict(id='c3', section='sentences', icon='link', colour='#F59E0B', title='If: os and tasai', subtitle='Os bydd hi, taswn i',
      term='Conditional clauses', termDef="An if-clause sets a condition. Welsh separates a real possibility (os) from an imagined, unreal one (pe / tas-), and the verb in each half has to match.",
      rule="""<p><b>Two kinds of if.</b></p>
<table><tr><th></th><th>If half</th><th>Result half</th></tr>
<tr><td><b>Real</b> (may well happen)</td><td><i>Os</i> + normal verb: <i>Os bydd hi'n braf</i>; <i>Os wyt ti'n barod</i></td><td>future or command: <i>bydda i'n mynd</i>; <i>awn ni</i></td></tr>
<tr><td><b>Unreal</b> (imagined)</td><td><i>Taswn i, taset ti, tasai fe / hi, tasen ni, tasech chi, tasen nhw</i> (written: <i>pe bawn i</i>)</td><td>conditional: <i>baswn i'n mynd</i></td></tr></table>
<p><b>Rules for os:</b> no <i>bod</i> and no <i>mae</i> after it (<i>os ydy e</i>, not <i>os mae e</i>). If the meaning is future, use the future: <i>Os bydd…</i> Negative: <i>os na</i> + soft mutation: <i>Os na fydd hi'n bwrw glaw.</i></p>
<p><b>Whether</b> is a question form, not os + mae: <i>Dw i ddim yn gwybod ydy e'n dod.</i> (You will hear <i>os ydy</i> in speech.)</p>""",
      questions=[
       mc('c3-01', "If it's fine tomorrow, I'll go.", '', "Os bydd hi'n braf yfory, bydda i'n mynd.", "Os mae hi'n braf yfory, bydda i'n mynd.|Os bod hi'n braf yfory, bydda i'n mynd.|Pe bydd hi'n braf yfory, bydda i'n mynd.|Os bydd hi'n braf yfory, baswn i'n mynd.|Os yw hi'n braf yfory, es i.", 'Real and future: os + bydd, then the future.', 'if-os', alts=["Os bydd hi'n braf yfory, a i.", "Os bydd hi'n braf fory, bydda i'n mynd."]),
       ty('c3-02', "Os ___ ti'n barod, awn ni. (bod, present)", 'bod, present', "If you're ready, we'll go.", 'wyt', 'After os use the plain present form: os wyt ti.', 'if-os', alts=['rwyt']),
       mc('c3-03', "If I were rich, I'd buy a boat.", '', "Taswn i'n gyfoethog, baswn i'n prynu cwch.", "Os dw i'n gyfoethog, baswn i'n prynu cwch.|Taswn i'n gyfoethog, bydda i'n prynu cwch.|Os baswn i'n gyfoethog, bydda i'n prynu cwch.|Taswn i'n cyfoethog, baswn i'n prynu cwch.|Pe dw i'n gyfoethog, baswn i'n prynu cwch.", 'Unreal: taswn i (if I were) + baswn i (I would).', 'if-pe', alts=["Pe baswn i'n gyfoethog, baswn i'n prynu cwch.", "Pe bawn i'n gyfoethog, baswn i'n prynu cwch."]),
       ty('c3-04', "___ hi'n gwybod, basai hi'n dweud. (if she, unreal)", 'if she, unreal', "If she knew, she'd say.", 'Tasai', 'Unreal if for she: tasai hi.', 'if-pe', alts=['Tase', 'Pe basai', 'Pe bai', 'Petai']),
       mc('c3-05', "I don't know if he's coming.", '', "Dw i ddim yn gwybod ydy e'n dod.", "Dw i ddim yn gwybod os mae e'n dod.|Dw i ddim yn gwybod bod e'n dod.|Dw i ddim yn gwybod tasai fe'n dod.|Dw i ddim yn gwybod mae e'n dod.|Dw i ddim yn gwybod pe bydd e'n dod.", "Whether = a question form (ydy e…?). Never os + mae. You'll hear os ydy in speech.", 'if-whether', alts=["Dw i ddim yn gwybod a ydy e'n dod.", "Dw i ddim yn gwybod os ydy e'n dod."]),
       ty('c3-06', "Os ___ fydd hi'n bwrw glaw, awn ni am dro. (not)", 'not', "If it doesn't rain, we'll go for a walk.", 'na', 'If … not = os na + soft mutation (fydd).', 'if-os'),
       ti('c3-07', 'If I had money, I would go.', "Tasai arian gyda fi baswn i'n mynd", "Os|bydda|mae|fydd", 'Unreal: tasai (if there were) + baswn i (I would).', 'if-pe', alts=["Tasai arian gyda fi baswn i'n mynd"]),
       er('c3-08', "Os bod hi'n bwrw glaw yfory, bydda i'n aros gartre.", 1, "Os bydd hi'n bwrw glaw yfory, bydda i'n aros gartre.", 'No bod after os. Use a normal verb form: os bydd hi.', 'if-os'),
       mc('c3-09', "Tasech chi'n gofyn, basen nhw'n helpu.", '', 'If you asked, they would help.', 'If you ask, they will help.|When you asked, they helped.|If they asked, you would help.|Because you asked, they would help.|If you had to ask, they helped.', 'Tasech chi (if you were to) + basen nhw (they would): unreal.', 'if-pe', noType=True),
       mc('c3-10', "___ ti'n hwyr, ffonia fi.", "If you're late, phone me.", 'Os wyt', 'Os bod|Taset|Os mae|Pe wyt|Os dy fod', 'Real possibility: os + wyt ti.', 'if-os', noType=True),
      ]))

    U.append(dict(id='c4', section='sentences', icon='quote', colour='#EC4899', title="'That' clauses 2", subtitle='y bydd, na fydd, mai / taw',
      term='Reported speech (future, negative, emphatic)', termDef="The earlier unit used bod for 'that' with the present and imperfect. Other tenses, negatives and emphatic sentences each need a different linking word.",
      rule="""<p><b>Which 'that'?</b> It depends on what follows.</p>
<table><tr><th>What follows</th><th>That =</th><th>Example</th></tr>
<tr><td>present / imperfect of bod</td><td><i>bod</i></td><td>Dw i'n meddwl <i>bod</i> hi'n braf.</td></tr>
<tr><td>future or conditional</td><td><i>y</i> (often dropped in speech)</td><td>Dw i'n meddwl <i>y bydd</i> hi'n braf. Mae hi'n dweud <i>y basai</i> hi'n dod.</td></tr>
<tr><td>negative</td><td><i>na</i> + soft (aspirate for c, p, t); <i>nad</i> before a vowel</td><td>Dw i'n gwybod <i>na fydd</i> e'n dod.</td></tr>
<tr><td>emphasis: anything that isn't the verb comes first</td><td><i>mai</i> (also <i>taw</i> in the south)</td><td>Dw i'n siŵr <i>mai</i> Siân sy'n iawn.</td></tr></table>
<p>Speech also uses <i>bod … ddim</i> for a present negative: <i>Dw i'n gwybod bod e ddim yn dod.</i></p>""",
      questions=[
       mc('c4-01', 'I think it will be fine tomorrow.', '', "Dw i'n meddwl y bydd hi'n braf yfory.", "Dw i'n meddwl bod hi'n braf yfory.|Dw i'n meddwl mai bydd hi'n braf yfory.|Dw i'n meddwl y fydd hi'n braf yfory.|Dw i'n meddwl bod bydd hi'n braf yfory.|Dw i'n meddwl na fydd hi'n braf yfory.", 'Future after that: y + bydd (no mutation after y).', 'that-y', alts=["Dw i'n meddwl bydd hi'n braf yfory.", "Dw i'n meddwl y bydd hi'n braf fory."]),
       ty('c4-02', "Mae hi'n dweud ___ bydd hi'n hwyr. (that)", 'that', "She says that she'll be late.", 'y', 'Before a future verb, that = y.', 'that-y'),
       mc('c4-03', "I know he won't come.", '', "Dw i'n gwybod na fydd e'n dod.", "Dw i'n gwybod na bydd e'n dod.|Dw i'n gwybod mai fydd e'n dod.|Dw i'n gwybod nad bydd e'n dod.|Dw i'n gwybod bod e ddim wedi dod.|Dw i'n gwybod dim bydd e'n dod.", 'That … not = na + soft mutation: na fydd.', 'that-na', alts=["Dw i'n gwybod fydd e ddim yn dod."]),
       ty('c4-04', "Dw i'n siŵr ___ Siân sy'n iawn. (that: emphatic)", 'that: emphatic', "I'm sure that it's Siân who's right.", 'mai', 'A name comes first, not the verb, so that = mai (or taw).', 'that-mai', alts=['taw']),
       mc('c4-05', 'Dwedodd e taw athro yw e.', '', "He said that he's a teacher.", "He asked if he's a teacher.|He said he isn't a teacher.|He said that he'll be a teacher.|He said that the teacher is here.|He told the teacher.", 'Taw (= mai) introduces an emphatic clause: athro yw e.', 'that-mai', noType=True),
       mc('c4-06', "Dw i'n credu ___ yng Nghaerdydd mae hi'n byw.", "I think it's in Cardiff that she lives.", 'mai', 'bod|y|na|os|a', 'A place comes first, not the verb: mai / taw.', 'that-mai', alts=['taw']),
       ty('c4-07', "Gobeithio ___ fydd hi'n bwrw glaw. (that … not)", 'that … not', "I hope it won't rain.", 'na', 'Negative that = na + soft mutation (fydd).', 'that-na'),
       mc('c4-08', "She says she'd like to come.", '', "Mae hi'n dweud y basai hi'n hoffi dod.", "Mae hi'n dweud bod hi'n hoffi dod.|Mae hi'n dweud mai basai hi'n hoffi dod.|Mae hi'n dweud na fasai hi'n hoffi dod.|Mae hi'n dweud y fasai hi'n hoffi dod.|Mae hi'n dweud os basai hi'n hoffi dod.", 'Conditional after that: y + basai.', 'that-y', alts=["Mae hi'n dweud basai hi'n hoffi dod.", "Mae hi'n dweud yr hoffai hi ddod.", "Mae hi'n dweud y byddai hi'n hoffi dod."]),
       er('c4-09', "Dw i'n meddwl bod Tom sy'n gyrru heno, nid Siân.", 3, "Dw i'n meddwl mai Tom sy'n gyrru heno, nid Siân.", 'Emphatic clause (Tom first): mai or taw, not bod.', 'that-mai'),
       mc('c4-10', "Dw i'n gwybod bod hi wedi mynd.", '', 'I know that she has gone.', "I know that she is going.|I know that she will go.|I know that she wants to go.|I know when she went.|I don't know whether she's gone.", 'bod + wedi = that … has / had.', 'that-y', noType=True),
      ]))

    U.append(dict(id='c5', section='nouns', icon='key', colour='#16A34A', title='X of Y', subtitle='drws y tŷ, car Siân',
      term='Possession between nouns (genitive)', termDef="English says 'the door of the house' or 'Siân's car'. Welsh simply puts the two nouns side by side, owner last, with no word for 'of'.",
      rule="""<p><b>Equation: thing owned + owner.</b> No <i>o</i>, and only <b>one</b> 'the', before the <b>last</b> noun.</p>
<table><tr><th>English</th><th>Welsh</th><th>Not</th></tr>
<tr><td>the door of the house</td><td><i>drws y tŷ</i></td><td>y drws y tŷ, drws o'r tŷ</td></tr>
<tr><td>Siân's car</td><td><i>car Siân</i></td><td>y car Siân</td></tr>
<tr><td>the end of the week</td><td><i>diwedd yr wythnos</i></td><td>y diwedd o'r wythnos</td></tr>
<tr><td>Siân's brother's house</td><td><i>tŷ brawd Siân</i></td><td></td></tr></table>
<p>The whole phrase is already definite, which is why the first noun never takes <i>y</i>: <i>Mae car fy mrawd yn y garej.</i></p>
<p><b>When you do use o:</b> a quantity or a part of something: <i>darn o gacen, llawer o bobl, paned o de</i> (o + soft mutation).</p>""",
      questions=[
       mc('c5-01', 'the door of the house', '', 'drws y tŷ', "y drws y tŷ|y drws o'r tŷ|drws o'r tŷ|y drws tŷ|drws yr tŷ", "Owned + owner, one 'the' before the last noun.", 'gen-order'),
       mc('c5-02', "Siân's car", '', 'car Siân', 'Siân car|y car Siân|car o Siân|car i Siân|ei char Siân', "Owned + owner. A name is already definite, so no 'the'.", 'gen-order'),
       ti('c5-03', 'The price of the ticket is too high.', 'Mae pris y tocyn yn rhy uchel', "o'r|Mae'r|tocynnau|uchaf", 'pris y tocyn: no "the" on pris, no o.', 'gen-the'),
       mc('c5-04', 'the end of the week', '', 'diwedd yr wythnos', "y diwedd yr wythnos|diwedd y wythnos|y diwedd o'r wythnos|diwedd o'r wythnos|yr wythnos diwedd", "One 'the', before the last noun. Yr before a vowel sound (w here).", 'gen-the'),
       ty('c5-05', "Dw i'n mynd i ___. (the children's school)", "the children's school", "I'm going to the children's school.", 'ysgol y plant', 'School + the children: ysgol y plant.', 'gen-order'),
       mc('c5-06', 'a piece of cake', '', 'darn o gacen', "darn cacen|darn y gacen|darn o cacen|y darn gacen|darn o'r cacen", 'A part or quantity of something uses o + soft mutation: cacen → gacen.', 'gen-o'),
       mc('c5-07', 'the capital of Wales', '', 'prifddinas Cymru', 'y brifddinas Cymru|prifddinas o Gymru|y prifddinas o Gymru|prifddinas y Cymru|Cymru prifddinas', "Owned + owner. Cymru is a name, so there is no 'the' at all.", 'gen-the'),
       er('c5-08', "Mae'r car fy mrawd yn y garej ers dydd Llun.", 0, 'Mae car fy mrawd yn y garej ers dydd Llun.', "Car fy mrawd is already definite: no 'the' on the first noun.", 'gen-the'),
       mc('c5-09', "Siân's brother's house", '', 'tŷ brawd Siân', 'tŷ Siân brawd|tŷ y brawd Siân|brawd Siân tŷ|tŷ brawd o Siân|y tŷ brawd Siân', 'Chain them, owner last each time: house + brother + Siân.', 'gen-order'),
       ty('c5-10', 'Beth yw ___? (the name of the dog)', 'the name of the dog', "What is the dog's name?", "enw'r ci", "enw + y ci → enw'r ci (y becomes 'r after a vowel).", 'gen-the', alts=['enw y ci']),
       mc('c5-11', 'a cup of tea', '', 'paned o de', 'paned te|paned y te|paned o te|y paned de|paned de', 'Quantity + o + soft mutation: te → de.', 'gen-o', alts=['cwpanaid o de', 'dishgled o de']),
      ]))

    U.append(dict(id='c6', section='sentences', icon='speech', colour='#06B6D4', title='Question words', subtitle='Pwy, beth, ble, pryd, sawl, pa',
      term='Interrogatives', termDef="Question words such as who, what and where. In Welsh the hard part is the verb that follows: mae, ydy / yw, or sy.",
      rule="""<table><tr><th>Word</th><th>Meaning</th><th>Note</th></tr>
<tr><td><i>Pwy</i></td><td>who</td><td></td></tr><tr><td><i>Beth</i></td><td>what</td><td></td></tr>
<tr><td><i>Ble</i></td><td>where</td><td>+ mae</td></tr><tr><td><i>Pryd</i></td><td>when (questions only)</td><td>+ mae</td></tr>
<tr><td><i>Pam</i> / <i>Sut</i></td><td>why / how</td><td>+ mae</td></tr>
<tr><td><i>Faint</i></td><td>how much / many</td><td>Faint o + plural (soft): Faint o blant?</td></tr>
<tr><td><i>Sawl</i></td><td>how many</td><td>+ singular: Sawl plentyn?</td></tr>
<tr><td><i>Pa</i></td><td>which</td><td>+ soft mutation: Pa lyfr?</td></tr></table>
<p><b>Which verb after Pwy / Beth?</b></p>
<table><tr><th>Job of the question word</th><th>Verb</th><th>Example</th></tr>
<tr><td>identity (X = ?)</td><td><i>yw / ydy</i></td><td>Pwy yw e? Beth yw hwn?</td></tr>
<tr><td>subject (the doer)</td><td><i>sy</i></td><td>Pwy sy'n dod? Beth sy'n digwydd?</td></tr>
<tr><td>object (the thing done)</td><td><i>mae</i></td><td>Beth mae hi'n ddarllen?</td></tr></table>
<p><b>Short past:</b> the verb soft-mutates after the question word: <i>Beth wnest ti? Ble est ti? Pwy welaist ti?</i></p>""",
      questions=[
       mc('c6-01', "___ mae'r orsaf?", 'Where is the station?', 'Ble', 'Beth|Pwy|Pryd|Pa|Sawl', 'Where = ble.', 'q-word', alts=['Lle']),
       mc('c6-02', 'Who is coming tonight?', '', "Pwy sy'n dod heno?", "Pwy mae'n dod heno?|Pwy ydy dod heno?|Pwy yw'n dod heno?|Pwy sy dod heno?|Pwy maen nhw'n dod heno?", 'Pwy is the subject (the one coming), so sy.', 'q-verb', alts=['Pwy sydd yn dod heno?']),
       mc('c6-03', 'Who is he?', '', 'Pwy yw e?', "Pwy mae e?|Pwy sy e?|Pwy sy'n e?|Pwy oes e?|Pwy e yw?", 'Identity: yw / ydy.', 'q-verb', alts=['Pwy ydy e?', 'Pwy ydi o?', 'Pwy ydy o?']),
       ty('c6-04', "___ lyfr wyt ti'n ddarllen? (which)", 'which', 'Which book are you reading?', 'Pa', 'Which = pa, followed by soft mutation (llyfr → lyfr).', 'q-word'),
       ty('c6-05', 'Pa ___ wyt ti eisiau? (lliw)', 'lliw', 'Which colour do you want?', 'liw', 'Pa + soft mutation: lliw → liw.', 'q-pa'),
       mc('c6-06', 'How many children do you have?', '', 'Sawl plentyn sy gyda chi?', 'Sawl plant sy gyda chi?|Faint plentyn sy gyda chi?|Sawl o blentyn sy gyda chi?|Faint o blentyn sy gyda chi?|Sawl blentyn sy gyda chi?', 'Sawl + singular noun, no mutation. (Or: Faint o blant.)', 'q-pa', alts=['Faint o blant sy gyda chi?', 'Sawl plentyn sydd gyda chi?']),
       mc('c6-07', 'How much does it cost?', '', "Faint mae e'n costio?", "Sawl mae e'n costio?|Faint sy e'n costio?|Pa mae e'n costio?|Faint yw e'n costio?|Sut faint mae e'n costio?", 'How much = faint. It is the object here, so mae.', 'q-verb', alts=["Faint mae'n costio?", "Faint mae o'n costio?", 'Faint yw e?']),
       ty('c6-08', 'Beth ___ ti ddoe? (gwneud, past)', 'gwneud, past', 'What did you do yesterday?', 'wnest', 'Gwnest ti soft-mutates after the question word: wnest.', 'q-past', alts=['wnaethost', 'nest']),
       mc('c6-09', "What's happening?", '', "Beth sy'n digwydd?", "Beth mae'n digwydd?|Beth yw digwydd?|Beth ydy'n digwydd?|Beth sy digwydd?|Beth oes yn digwydd?", 'Beth is the subject (the thing happening), so sy.', 'q-verb', alts=['Beth sydd yn digwydd?', "Be sy'n digwydd?"]),
       mc('c6-10', 'What is she reading?', '', "Beth mae hi'n ddarllen?", "Beth sy hi'n darllen?|Beth yw hi'n darllen?|Beth sy'n darllen hi?|Beth mae hi darllen?|Beth ydy hi'n ddarllen?", "Beth is the object, so mae. Formally 'ei ddarllen'; the mutation usually stays in speech.", 'q-verb', alts=["Beth mae hi'n ei ddarllen?", "Beth mae hi'n darllen?"]),
       er('c6-11', "Pryd sy'r trên nesa yn gadael am Gaerdydd?", 1, "Pryd mae'r trên nesa yn gadael am Gaerdydd?", 'Sy is only for when the question word is the subject. After pryd, ble, pam, sut: mae.', 'q-verb'),
       mc('c6-12', "Pam wyt ti'n dysgu Cymraeg?", '', 'Why are you learning Welsh?', 'When are you learning Welsh?|How are you learning Welsh?|Where are you learning Welsh?|Who is teaching you Welsh?|Which Welsh are you learning?', 'Pam = why.', 'q-word', noType=True),
      ]))

    U.append(dict(id='c7', section='nouns', icon='clock', colour='#F97316', title='Time and dates', subtitle="am ddau o'r gloch, nos Lun, ym mis Mai",
      term='Telling the time; days and dates', termDef="Clock times use the older, traditional numbers (un ar ddeg, ugain) and a few fixed mutations. Days change form depending on whether you mean one occasion or a habit.",
      rule="""<p><b>Clock.</b> <i>tri o'r gloch</i> (3:00). <i>am</i> (at) + soft mutation: <i>am ddau o'r gloch</i>. Past the hour: <i>wedi</i>. To the hour: <i>i</i> + soft mutation.</p>
<table><tr><td>3:15</td><td>chwarter wedi tri</td><td>2:45</td><td>chwarter i dri</td></tr>
<tr><td>3:30</td><td>hanner awr wedi tri</td><td>6:20</td><td>ugain munud wedi chwech</td></tr>
<tr><td>11:00</td><td>un ar ddeg o'r gloch</td><td>12:00</td><td>deuddeg o'r gloch</td></tr></table>
<p><b>Days.</b></p>
<table><tr><td><i>dydd Llun</i></td><td>Monday (the name)</td></tr><tr><td><i>ddydd Llun</i></td><td>on Monday (one occasion): soft mutation, no word for on</td></tr>
<tr><td><i>ar ddydd Llun</i></td><td>on Mondays (a habit)</td></tr><tr><td><i>nos Lun</i></td><td>Monday night: nos is feminine, so the day mutates (nos Fawrth, nos Wener)</td></tr></table>
<p><b>Months and years.</b> <i>ym mis Mai</i> (in May). <i>eleni</i> (this year), <i>y llynedd</i> (last year), <i>y flwyddyn nesa</i> (next year).</p>
<p><b>Ordinals.</b> <i>cyntaf</i> goes after the noun: <i>y tro cyntaf</i>. The rest go before: <i>yr ail dro</i> (ail + soft), <i>y trydydd dydd</i>. Feminine forms <i>trydedd, pedwaredd</i> mutate after y, and so does the noun: <i>y drydedd flwyddyn</i>.</p>""",
      questions=[
       mc('c7-01', "at two o'clock", '', "am ddau o'r gloch", "am dau o'r gloch|yn ddau o'r gloch|ar ddau o'r gloch|am ddwy o'r gloch|am ddau o gloch", 'am (at) + soft mutation: dau → ddau.', 'time-clock'),
       mc('c7-02', 'half past three', '', 'hanner awr wedi tri', 'hanner wedi tri|hanner awr i dri|tri a hanner awr|hanner awr wedi dri|hanner awr ar ôl tri', 'Half past = hanner awr wedi. No mutation after wedi.', 'time-clock', alts=["hanner awr 'di tri"]),
       ty('c7-03', 'chwarter i ___ (tri)', 'tri', 'quarter to three', 'dri', 'i (to) + soft mutation: tri → dri.', 'time-clock'),
       mc('c7-04', "eleven o'clock", '', "un ar ddeg o'r gloch", "un deg un o'r gloch|un ar deg o'r gloch|deuddeg o'r gloch|un ar ddeg o gloch|un ar ddeg awr", 'Clock times use the traditional numbers: un ar ddeg.', 'time-clock'),
       mc('c7-05', "I'm working on Monday. (this Monday only)", '', "Dw i'n gweithio ddydd Llun.", "Dw i'n gweithio ar ddydd Llun.|Dw i'n gweithio yn dydd Llun.|Dw i'n gweithio nos Lun.|Dw i'n gweithio dydd Lun.|Dw i'n gweithio ar y Llun.", 'One occasion: soft mutation and no ar. Ar ddydd Llun means every Monday.', 'time-day', alts=["Dw i'n gweithio dydd Llun."]),
       mc('c7-06', 'Monday night', '', 'nos Lun', 'nos Llun|noson Llun|dydd Llun nos|nos dydd Llun|Llun nos', 'Nos is feminine, so the day soft-mutates: Llun → Lun.', 'time-day'),
       ty('c7-07', 'nos ___ (Gwener)', 'Gwener', 'Friday night', 'Wener', 'After nos the day soft-mutates: g drops.', 'time-day'),
       mc('c7-08', 'in May', '', 'ym mis Mai', 'yn mis Mai|mewn Mai|ym Mai mis|yn y Mai|ar fis Mai', 'In (a month) = ym mis … (yn becomes ym before m).', 'time-date', alts=['ym Mai']),
       mc('c7-09', 'the second time', '', 'yr ail dro', 'yr ail tro|y dau dro|y tro ail|y ail dro|yr ail droeon', 'Ail goes before the noun and soft-mutates it: tro → dro.', 'time-ordinal'),
       ty('c7-10', 'y ___ flwyddyn (third, feminine)', 'third, feminine', 'the third year', 'drydedd', 'Trydydd → trydedd for a feminine noun, and it soft-mutates after y.', 'time-ordinal'),
       mc('c7-11', 'last year', '', 'y llynedd', "eleni|y flwyddyn nesa|neithiwr|y llynedd nesa|echdoe", 'Last year = y llynedd. Eleni = this year.', 'time-date', alts=['llynedd', 'y flwyddyn ddiwethaf', 'y flwyddyn ddiwetha']),
       mc('c7-12', 'twenty past six', '', 'ugain munud wedi chwech', 'ugain munud i chwech|ugain wedi chwech munud|chwech ac ugain|ugain munud wedi chwe|ugain awr wedi chwech', 'Clock times use ugain for twenty. Past = wedi.', 'time-clock', alts=['dau ddeg munud wedi chwech']),
      ]))

    U.append(dict(id='c8', section='sentences', icon='bolt', colour='#84CC16', title='How and how much', subtitle='yn gyflym, rhy ddrud, hen dŷ',
      term='Adverbs and degree words', termDef="An adverb says how something is done (quickly). A degree word says how much (very, too, quite). Each Welsh degree word has its own position and its own mutation.",
      rule="""<p><b>Adverb = yn + adjective (soft mutation).</b> <i>cyflym → yn gyflym</i> (quickly), <i>da → yn dda</i> (well). After a vowel: <i>gyrru'n ofalus</i>.</p>
<table><tr><th>Word</th><th>Meaning</th><th>Position</th><th>Mutation</th></tr>
<tr><td><i>iawn</i></td><td>very</td><td>after: da iawn</td><td>–</td></tr>
<tr><td><i>rhy</i></td><td>too</td><td>before: rhy ddrud</td><td>soft</td></tr>
<tr><td><i>mor</i></td><td>so / as</td><td>before: mor dda</td><td>soft (not ll, rh)</td></tr>
<tr><td><i>eitha</i></td><td>quite</td><td>before: eitha da</td><td>none</td></tr>
<tr><td><i>gweddol, go, hollol</i></td><td>fairly, pretty, completely</td><td>before: gweddol dda</td><td>soft</td></tr></table>
<p><b>Adjectives that go before the noun</b> (and soft-mutate it): <i>hen dŷ</i> (an old house), <i>fy hoff lyfr</i> (my favourite book), <i>prif reswm</i> (main reason), <i>unig blentyn</i> (an only child). Compare <i>plentyn unig</i> = a lonely child.</p>""",
      questions=[
       ty('c8-01', "Mae hi'n siarad yn ___. (cyflym)", 'cyflym', 'She speaks quickly.', 'gyflym', 'Adverb = yn + soft mutation: cyflym → gyflym.', 'adv-yn'),
       mc('c8-02', 'too expensive', '', 'rhy ddrud', 'rhy drud|gormod drud|drud rhy|yn rhy drud|rhy o ddrud', 'Rhy goes before the adjective and soft-mutates it.', 'deg-rhy'),
       mc('c8-03', 'very good (on its own)', '', 'da iawn', 'iawn da|iawn dda|da yn iawn|mor da|da rhy', 'Iawn goes after the adjective.', 'deg-other'),
       ty('c8-04', "Mae'r ffilm yn rhy ___. (hir)", 'hir', 'The film is too long.', 'hir', 'Rhy causes soft mutation, but h has none.', 'deg-rhy'),
       ty('c8-05', 'hen ___ (tŷ)', 'tŷ', 'an old house', 'dŷ', 'Hen comes before the noun and soft-mutates it.', 'adj-before', alts=['dy']),
       mc('c8-06', 'my favourite book', '', 'fy hoff lyfr', 'fy llyfr hoff|fy hoff llyfr|fy lyfr hoff|fy hoffi llyfr|hoff fy lyfr', 'Hoff goes before the noun and soft-mutates it.', 'adj-before'),
       mc('c8-07', 'quite good', '', 'eitha da', "eitha dda|da eitha|rhy dda|eitha'n dda|mor dda", 'Eitha goes before the adjective and causes no mutation.', 'deg-other', alts=['eithaf da']),
       ty('c8-08', 'Roedd y bwyd mor ___! (da)', 'da', 'The food was so good!', 'dda', 'Mor + soft mutation: da → dda.', 'deg-other'),
       mc('c8-09', 'an only child', '', 'unig blentyn', 'plentyn unig|unig plentyn|blentyn unig|dim ond plentyn|un plentyn unig', 'Unig before the noun = only (and it mutates). After the noun it means lonely.', 'adj-before'),
       mc('c8-10', 'He drives carefully.', '', "Mae e'n gyrru'n ofalus.", "Mae e'n gyrru gofalus.|Mae e'n gyrru'n gofalus.|Mae e'n ofalus gyrru.|Mae e'n gyrru ofalus.|Mae e gyrru'n ofalus.", "Adverb: yn ('n after a vowel) + soft mutation: gofalus → ofalus.", 'adv-yn', alts=["Mae e'n gyrru yn ofalus.", "Mae o'n gyrru'n ofalus."]),
       er('c8-11', "Mae'r car newydd yn rhy drud i ni ar hyn o bryd.", 5, "Mae'r car newydd yn rhy ddrud i ni ar hyn o bryd.", 'Rhy + soft mutation: drud → ddrud.', 'deg-rhy'),
       ty('c8-12', 'y ___ reswm (main)', 'main', 'the main reason', 'prif', 'Prif goes before the noun and soft-mutates it: rheswm → reswm.', 'adj-before'),
      ]))

    U.append(dict(id='c9', section='verbs', icon='megaphone', colour='#E11D48', title='News Welsh: -wyd, -ir', subtitle='Agorwyd, cynhelir, ganwyd',
      term='Impersonal verbs', termDef="News bulletins, signs and formal writing use one-word passives instead of cael. You mainly need to recognise them: the Canolradd listening paper includes a news bulletin.",
      rule="""<p><b>Recognise two endings.</b></p>
<table><tr><th>Ending</th><th>Time</th><th>Example</th><th>Everyday equivalent</th></tr>
<tr><td><i>-wyd</i></td><td>past: was / were …ed</td><td><i>Agorwyd y siop</i> = The shop was opened</td><td>Cafodd y siop ei hagor</td></tr>
<tr><td><i>-ir</i></td><td>present or future: is / will be …ed</td><td><i>Cynhelir y cyfarfod</i> = The meeting will be held</td><td>Bydd y cyfarfod yn cael ei gynnal</td></tr></table>
<p><b>Common in the news:</b> <i>ganwyd</i> (was born), <i>lladdwyd</i> (was killed), <i>anafwyd</i> (was injured), <i>arestiwyd</i> (was arrested), <i>cafwyd</i> (there was / was found), <i>dywedir</i> (it is said), <i>gwelir</i> (is seen).</p>
<p>There is no subject doing the action, and the noun after the verb does not mutate. Negative: <i>ni</i> + mutation: <i>Ni chaniateir ysmygu</i> = Smoking is not allowed.</p>""",
      questions=[
       mc('c9-01', 'Agorwyd yr ysgol yn 1950.', '', 'The school was opened in 1950.', 'He opened the school in 1950.|The school will be opened in 1950.|The school has been open since 1950.|They are opening the school.|The school was closed in 1950.', '-wyd = was …ed (past, no doer named).', 'imps-wyd', noType=True),
       mc('c9-02', 'Cynhelir y cyfarfod nos Fawrth.', '', 'The meeting will be held on Tuesday night.', 'The meeting was held on Tuesday night.|He is holding the meeting on Tuesday night.|The meeting was cancelled on Tuesday night.|The meeting will be held on Tuesday morning.|Hold the meeting on Tuesday night!', '-ir = is / will be …ed. Cynnal → cynhelir.', 'imps-ir', noType=True),
       mc('c9-03', 'Same meaning as: Cafodd dau ddyn eu harestio.', '', 'Arestiwyd dau ddyn.', 'Arestir dau ddyn.|Arestiodd dau ddyn.|Arestiwyd dau dyn.|Mae dau ddyn yn arestio.|Bydd dau ddyn yn cael eu harestio.', 'Past passive in one word: -wyd.', 'imps-wyd', noType=True),
       ty('c9-04', '___ hi yng Nghaerdydd yn 1970. (geni: was born, formal)', 'geni: was born, formal', 'She was born in Cardiff in 1970.', 'Ganwyd', 'Geni → ganwyd (also ganed). Everyday: Cafodd hi ei geni.', 'imps-wyd', alts=['Ganed']),
       mc('c9-05', 'Ni chaniateir ysmygu.', '', 'Smoking is not allowed.', 'Smoking was not allowed.|Smoking is allowed.|Nobody is smoking.|They did not smoke.|You may smoke outside.', 'Caniatáu → caniateir (is allowed). Ni + aspirate mutation makes it negative.', 'imps-ir', noType=True),
       mc('c9-06', 'What does the ending -wyd tell you? (gwelwyd, agorwyd)', '', 'Past: something was done', 'Present or future: something is or will be done|A command|I did it|They will do it|It would be done', '-wyd is the past impersonal: was / were …ed.', 'imps-wyd', noType=True),
       mc('c9-07', 'Dywedir bod y ffordd ar gau.', '', 'It is said that the road is closed.', 'He said that the road was closed.|It was said that the road would close.|Say that the road is closed!|They will close the road.|The road was closed, he said.', 'Dweud → dywedir = it is said.', 'imps-ir', noType=True),
       mc('c9-08', 'Anafwyd tri o bobl yn y ddamwain.', '', 'Three people were injured in the accident.', 'Three people were killed in the accident.|Three people saw the accident.|Three people will be injured in the accident.|Three people caused the accident.|Three people were arrested after the accident.', 'Anafu = to injure; -wyd = were …ed. (Killed would be lladdwyd.)', 'imps-wyd', noType=True),
      ]))

    U.append(dict(id='c10', section='sentences', icon='puzzle', colour='#6366F1', title='Although, while, when, so', subtitle='er bod, tra, pan, felly, neu',
      term='Conjunctions', termDef="Conjunctions join two clauses. Some are followed by bod (like 'that' clauses), one causes a mutation, and one is easy to confuse with a question word.",
      rule="""<table><tr><th>Word</th><th>Meaning</th><th>What follows</th></tr>
<tr><td><i>er</i></td><td>although</td><td><i>bod</i>: Er bod hi'n oer… (never er mae)</td></tr>
<tr><td><i>efallai</i></td><td>perhaps</td><td><i>bod</i>: Efallai bod nhw'n hwyr</td></tr>
<tr><td><i>tra</i></td><td>while</td><td>a normal verb: tra o'n i'n gweithio</td></tr>
<tr><td><i>pan</i></td><td>when (joining, not asking)</td><td>soft mutation: pan ddaeth e; pan o'n i'n blentyn</td></tr>
<tr><td><i>felly</i></td><td>so, therefore</td><td>normal sentence</td></tr>
<tr><td><i>neu</i></td><td>or</td><td>soft mutation of a noun, adjective or verbnoun: te neu goffi</td></tr>
<tr><td><i>er mwyn</i></td><td>in order to</td><td>verbnoun: er mwyn dysgu</td></tr></table>
<p><b>Pan or pryd?</b> <i>Pryd</i> asks a question (<i>Pryd wyt ti'n mynd?</i>). <i>Pan</i> joins two clauses (<i>pan o'n i'n blentyn</i>).</p>""",
      questions=[
       mc('c10-01', "Although it's cold, I'm going out.", '', "Er bod hi'n oer, dw i'n mynd allan.", "Er mae hi'n oer, dw i'n mynd allan.|Er hi'n oer, dw i'n mynd allan.|Er yn oer mae hi, dw i'n mynd allan.|Er bod hi oer, dw i'n mynd allan.|Er ei fod hi'n oer, dw i'n mynd allan.", 'Er + bod, never er + mae.', 'conj-bod', alts=["Er ei bod hi'n oer, dw i'n mynd allan."]),
       ty('c10-02', "Efallai ___ nhw'n hwyr. (that … are)", 'that … are', "Perhaps they're late.", 'bod', 'Efallai + bod.', 'conj-bod', alts=['fod', 'eu bod']),
       mc('c10-03', 'while I was working', '', "tra o'n i'n gweithio", "tra bod i'n gweithio|tra mae fi'n gweithio|pan bod fi'n gweithio|tra fi'n gweithio|tra oeddwn i gweithio", 'Tra + a normal verb form.', 'conj-pan', alts=["tra ro'n i'n gweithio", "tra oeddwn i'n gweithio", "tra roeddwn i'n gweithio"]),
       ty('c10-04', 'Pan ___ e adre, roedd pawb yn cysgu. (dod: he came)', 'dod: he came', 'When he came home, everyone was asleep.', 'ddaeth', 'Pan + soft mutation: daeth → ddaeth.', 'conj-pan', alts=['ddath', 'ddoth']),
       mc('c10-05', 'when I was a child', '', "pan o'n i'n blentyn", "pan o'n i'n plentyn|pan dw i'n blentyn|pan bod fi'n blentyn|pryd o'n i'n blentyn|pan o'n i blentyn", 'Joining when = pan. Pryd is only for questions. Yn + noun soft-mutates: blentyn.', 'conj-pan', alts=["pan ro'n i'n blentyn", "pan oeddwn i'n blentyn"]),
       mc('c10-06', "___ wyt ti'n mynd?", 'When are you going?', 'Pryd', 'Pan|Tra|Er|Os|Achos', 'A question: pryd. Pan only joins clauses.', 'conj-pan'),
       ty('c10-07', 'te neu ___ (coffi)', 'coffi', 'tea or coffee', 'goffi', 'Neu + soft mutation: coffi → goffi.', 'conj-neu'),
       mc('c10-08', "Mae hi'n gweithio'n galed, ___ mae hi wedi blino.", "She works hard, so she's tired.", 'felly', 'ond|achos|er|neu|pan', 'So / therefore = felly.', 'conj-neu'),
       {'id': 'c10-09', 'type': 'error', 'sentence': "Er mae'r tywydd yn wael iawn, aethon ni i'r traeth ddoe.", 'wrong': 1, 'fix': "Er bod y tywydd yn wael iawn, aethon ni i'r traeth ddoe.", 'explain': 'Er + bod, never er + mae.', 'skills': ['conj-bod']},
       mc('c10-10', "Dw i'n dysgu Cymraeg er mwyn siarad â'r plant.", '', "I'm learning Welsh in order to speak to the children.", "I'm learning Welsh although I speak to the children.|I'm learning Welsh because the children speak it.|I'm learning Welsh while speaking to the children.|I'm learning Welsh, so the children speak it.|I'm learning Welsh before speaking to the children.", 'Er mwyn + verbnoun = in order to.', 'conj-bod', noType=True),
       ty('c10-11', 'Wyt ti eisiau cerdded neu ___? (gyrru)', 'gyrru', 'Do you want to walk or drive?', 'yrru', 'Neu + soft mutation of a verbnoun: g drops.', 'conj-neu'),
      ]))
    return U

NEW_SKILLS = {
 'yn-bod': ('Yes / no: present, wedi, oes', 'Ydw, Ydy, Oes'), 'yn-imp': ('Yes / no: imperfect', "O'n, Oedd"), 'yn-do': ('Yes / no: short past', 'Do, Naddo'),
 'yn-fut': ('Yes / no: future', 'Bydda, Na fydd'), 'yn-cond': ('Yes / no: conditional', 'Baswn, Hoffwn'), 'yn-short': ('Yes / no: wnei, ga, alli', 'Gwnaf, Cei, Galla'),
 'yn-ie': ('Ie and nage', 'When the verb is not first'),
 'pas-cael': ('Passive: cael pattern', 'Ces i fy ngeni'), 'pas-poss': ('Passive: possessive + mutation', 'ei godi, ei chodi'), 'pas-tense': ('Passive in other tenses', 'yn cael ei, bydd … yn cael'),
 'if-os': ('Os: real if', 'Os bydd hi, os na'), 'if-pe': ('Taswn i: unreal if', 'Taswn i … baswn i'), 'if-whether': ('Whether', 'Not os + mae'),
 'that-y': ('That + future / conditional', 'y bydd, y basai'), 'that-na': ('That … not', 'na fydd'), 'that-mai': ('That, emphatic', 'mai / taw'),
 'gen-order': ('X of Y: word order', 'drws y tŷ'), 'gen-the': ("X of Y: only one 'the'", 'pris y tocyn'), 'gen-o': ('When to use o', 'darn o gacen'),
 'q-word': ('Question words', 'Pwy, ble, pryd, pa'), 'q-verb': ('Mae, yw or sy after a question word', "Pwy sy'n, Beth mae"), 'q-pa': ('Pa, sawl, faint', 'Pa lyfr, sawl plentyn'), 'q-past': ('Question word + short past', 'Beth wnest ti'),
 'time-clock': ('Clock times', "am ddau o'r gloch"), 'time-day': ('Days: one occasion, habit, night', 'ddydd Llun, nos Lun'), 'time-date': ('Months and years', 'ym mis Mai, y llynedd'), 'time-ordinal': ('Ordinals', 'yr ail dro'),
 'adv-yn': ('Adverbs with yn', 'yn gyflym'), 'deg-rhy': ('Rhy + soft mutation', 'rhy ddrud'), 'deg-other': ('Iawn, mor, eitha', 'da iawn, mor dda'), 'adj-before': ('Adjectives before the noun', 'hen dŷ, hoff lyfr'),
 'imps-wyd': ('Impersonal past -wyd', 'Agorwyd'), 'imps-ir': ('Impersonal present / future -ir', 'Cynhelir'),
 'conj-bod': ('Er / efallai + bod', 'er bod'), 'conj-pan': ('Pan, tra, pryd', 'pan ddaeth'), 'conj-neu': ('Neu, felly', 'te neu goffi'),
}
NEW_GLOSSARY = [
 ('Passive', "The subject has the action done to it: 'The house was built'. Welsh: cael + possessive + verbnoun, or -wyd / -ir in formal Welsh."),
 ('Impersonal verb', "A one-word passive with no doer named: agorwyd (was opened), cynhelir (will be held). Common in news and notices."),
 ('Genitive', "The 'of' relationship between two nouns: drws y tŷ. Welsh puts owner last, with no word for of."),
 ('Adverb', "A word saying how something is done. Welsh: yn + adjective with soft mutation: yn gyflym."),
 ('Ordinal', 'A number showing order: cyntaf (first), ail (second), trydydd (third).'),
]

FIXES = {
 # object after an inflected verb soft-mutates; a loanword hid the rule
 'u5-04': {'en': 'We ate fish last night.', 'answer': 'Bwyton ni bysgod neithiwr', 'alts': ['Fwyton ni bysgod neithiwr'],
           'distractors': ['pysgod', 'Bwytais', 'Bwytoch', 'Bwytodd', 'yn', 'Fwyton'],
           'explain': 'We ending: -on. Bwyta → bwyt- → bwyton ni. The object soft-mutates: pysgod → bysgod.'},
}

def main():
    C = json.load(open(PATH, encoding='utf8'))
    U = units()
    ids = {u['id'] for u in U}
    C['units'] = [u for u in C['units'] if u['id'] not in ids] + U
    for u in C['units']:
        for q in u['questions']:
            if q['id'] in FIXES:
                q.update(FIXES[q['id']])
    for k, (t, b) in NEW_SKILLS.items():
        C['skills'][k] = {'group': 'point', 'title': t, 'blurb': b}
    have = {g['term'] for g in C['glossary']}
    for t, d in NEW_GLOSSARY:
        if t not in have:
            C['glossary'].append({'term': t, 'def': d})
    DR.clear(); build_drills()
    seen = set(); out = []
    for q in DR:
        if q['id'] in seen:
            continue
        seen.add(q['id']); out.append(q)
    C['drills'] = out
    C['version'] = VERSION
    C['goal'] = {'name': 'Canolradd exam', 'date': '2027-06-18', 'register': '2027-03-01'}
    # ---- checks
    allq = [q for u in C['units'] for q in u['questions']] + out
    idset = set()
    for q in allq:
        assert q['id'] not in idset, 'duplicate id ' + q['id']; idset.add(q['id'])
        for s in q['skills']:
            assert s in C['skills'], (q['id'], s)
        if q['type'] == 'type':
            assert q['text'].count('___') == 1 and q['answer'], q['id']
        if q['type'] == 'error':
            assert 0 <= q['wrong'] < len(q['sentence'].split(' ')), q['id']
    units_by = {u['id'] for u in C['units']}
    assert all(q['unit'] in units_by for q in out)
    json.dump(C, open(PATH, 'w', encoding='utf8'), ensure_ascii=False, indent=1)
    print('units', len(C['units']), 'unit questions', sum(len(u['questions']) for u in C['units']), 'drills', len(out), 'skills', len(C['skills']))

if __name__ == '__main__':
    main()
