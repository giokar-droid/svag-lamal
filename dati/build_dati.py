#!/usr/bin/env python3
"""Rigenera premi_ti_<anno>.json e npa_ti_<anno>.json dai file ufficiali UFSP (Ufficio federale della sanita' pubblica, BAG).

Cosa serve, ogni anno (a fine settembre l'UFSP pubblica i premi dell'anno dopo), tutto in una cartella:
  Praemien_CH_<anno>.csv               premi di tutte le casse        opendata.swiss, dataset «health-insurance-premiums»
  Tarife_<anno>.csv                    nomi DE/FR/IT dei prodotti     stesso dataset
  praemienregionen-<anno>.xlsx         comune / NPA -> regione        priminfo.admin.ch -> Downloads
  zugelassene-krankenversicherer-*.xlsx  nomi degli assicuratori      bag.admin.ch -> Krankenversicherer

Uso:
  python3 build_dati.py --anno 2027
  python3 build_dati.py --anno 2028 --sorgenti "/percorso/bag_2028"
Default delle sorgenti: TOOL/CASSA MALATI/src/data/bag_<anno> nel Dropbox. I JSON finiscono accanto a questo script.

Tipi di modello (stessa logica del wizard cassa malati, genera_dati_lamal.py):
  BASE  modello standard, libera scelta del medico
  HAM   medico di famiglia
  HMO   rete HMO (studio medico di gruppo)
  DIV   altri: telemedicina o app, farmacia, modelli flessibili
Dal 2027 l'UFSP classifica in BASE / PRAXIS / TEL_DIG / FLEX: PRAXIS diventa HAM, oppure HMO se il nome lo dice
(HMO, Santé, BestCare), oppure DIV «farmacia» se il nome parla di farmacia; TEL_DIG e FLEX diventano DIV.
Il formato fino al 2026 (TAR-BASE / TAR-HAM / TAR-HMO / TAR-DIV) e' letto lo stesso.

Fasce d'eta': E adulti 26+, J giovani 19-25, K bambini 0-18 (premio del primo figlio, senza sconto).
Gli sconti per fratelli, dove la cassa li ha, stanno a parte: K3 dal 3° figlio, K4 dal 2° figlio per tutti,
K5 dal 3° figlio per tutti. Premi mensili in franchi, «N» senza infortunio, «U» con infortunio.

Alla fine lo script confronta alcuni premi con priminfo.admin.ch (tabella CONTROLLI): se uno non torna, si ferma
e non scrive nulla.
"""
import argparse, csv, datetime, glob, json, os, pathlib, re, sys

import openpyxl

QUI = pathlib.Path(__file__).resolve().parent
DROPBOX_CM = pathlib.Path.home() / 'Library/CloudStorage/Dropbox/RESOURCES/SVAG/TOOL/CASSA MALATI/src/data'

# Premi verificati a mano su priminfo.admin.ch: (anno, BAG n., codice prodotto, regione, eta', infortunio, franchigia, premio)
CONTROLLI = {
    2027: [
        ('376', 'HMO_A', '1', 'E', 'N', 2500, 473.00, 'KPT KPTwin.plus'),
        ('32', 'SMARTMED', '1', 'E', 'N', 2500, 477.70, 'Aquilana SMARTMED'),
        ('290', 'HMO_01', '1', 'E', 'N', 2500, 478.80, 'CONCORDIA HMO'),
        ('1562', 'BFP_CP', '1', 'E', 'N', 2500, 485.30, 'Helsana BeneFit PLUS Medico di famiglia R1'),
        ('1509', 'Hausarztmodell 1 (NetMed 1)', '1', 'E', 'N', 2500, 489.80, 'Sanitas Medico di famiglia 1'),
        ('1509', 'Hausarztmodell 1 (NetMed 1)', '1', 'J', 'N', 2500, 297.35, 'Sanitas Medico di famiglia 1, giovani 19-25'),
    ],
}
CONTROLLI_NPA = {2027: [('6964', 'Lugano', 1)]}

# Nomi brevi dove la pulizia automatica non basta
NOMI_BREVI = {'1386': 'Galenos', '1542': 'Assura', '509': 'Vivao Sympany', '1479': 'Mutuel'}

ETA = {'E': 'Adulti 26+', 'J': 'Giovani 19-25', 'K': 'Bambini 0-18',
       'K3': 'Bambini 0-18, sconto dal 3° figlio', 'K4': 'Bambini 0-18, sconto dal 2° figlio (per tutti i figli)',
       'K5': 'Bambini 0-18, sconto dal 3° figlio (per tutti i figli)'}
TIPI = {'BASE': 'Modello standard (libera scelta del medico)', 'HAM': 'Medico di famiglia',
        'HMO': 'Rete HMO (studio medico di gruppo)', 'DIV': 'Altri modelli (telemedicina o app, farmacia, flessibili)'}
DETTAGLI = {'BASE': 'Libera scelta del medico', 'HAM': 'Medico di famiglia', 'HMO': 'Rete HMO',
            'FARM': 'Farmacia come primo contatto', 'TEL': 'Telemedicina o app come primo contatto',
            'FLEX': 'Flessibile: si sceglie ogni volta il primo contatto'}
ORDINE_TIPO = {'BASE': 0, 'HAM': 1, 'HMO': 2, 'DIV': 3}


def trova(cartella, modello):
    l = sorted(glob.glob(str(pathlib.Path(cartella) / modello)))
    if not l:
        sys.exit(f'ERRORE: in {cartella} manca un file «{modello}»')
    return l[-1]


def cifra_finale(s):
    m = re.search(r'(\d+)\s*$', s or '')
    return m.group(1) if m else (s or '').strip()


def eta(classe, sotto):
    c = classe.upper()
    base = 'K' if 'KIN' in c else 'J' if 'JUG' in c else 'E'
    sotto = (sotto or '').strip().upper()
    if base == 'K' and sotto and sotto != 'K1':
        return sotto                                   # K3 / K4 / K5: sconti fratelli
    return base


def classifica(tariftyp, nomi):
    """-> (tipo BASE/HAM/HMO/DIV, codice dettaglio)."""
    tt = tariftyp.upper().replace('TAR-', '').strip()
    s = ' '.join(nomi).lower()
    farmacia = re.search(r'pharm|apothek|farmac', s)
    combinato = re.search(r'hausarzt|famiglia|telmed|telemed', s)     # «medico di famiglia, telemedicina e farmacia»
    if tt == 'BASE':
        return 'BASE', 'BASE'
    if tt == 'HMO' or re.search(r'\bhmo\b|hmo[-_ ]|sant[ée]\b|bestcare', s):
        return 'HMO', 'HMO'
    if farmacia and not combinato:
        return 'DIV', 'FARM'
    if tt in ('PRAXIS', 'HAM'):
        return 'HAM', 'HAM'
    if tt == 'TEL_DIG':
        return 'DIV', 'TEL'
    if tt == 'FLEX':
        return 'DIV', 'FLEX'
    # vecchio formato TAR-DIV: si guarda il nome
    if re.search(r'tel|call|24\b', s):
        return 'DIV', 'TEL'
    return 'DIV', 'FLEX'


def pulisci(s):
    s = str(s or '')
    s = re.sub(r'-\s*\n\s*(?=[a-zäöü])', '', s)        # «Krankenver-\nsicherung» -> «Krankenversicherung»
    s = re.sub(r'(?<=[a-zäöü])-(?=[a-zäöü])', '', s)     # «Unfallver-sicherung» -> «Unfallversicherung»
    s = re.sub(r'-\s*\n\s*', '-', s)                    # «Kranken-\nVersicherung» -> «Kranken-Versicherung»
    return re.sub(r'\s+', ' ', s).strip()


def nome_breve(num, nome):
    if num in NOMI_BREVI:
        return NOMI_BREVI[num]
    n = re.sub(r'\s+(Kranken\w*|Gesundheits\w*|Grundversicherung\w*|Versicherung\w*)(\s+(AG|SA))?$', '', nome.strip())
    n = re.sub(r'(-Basis)?\s+(AG|SA)$', '', n)
    return n.strip()


def numero(x):
    x = round(float(x), 2)
    return int(x) if x == int(x) else x


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--anno', type=int, required=True)
    ap.add_argument('--cantone', default='TI')
    ap.add_argument('--sorgenti', default=None, help='cartella con i 4 file UFSP (default: bag_<anno> del wizard)')
    ap.add_argument('--uscita', default=str(QUI))
    a = ap.parse_args()
    kt = a.cantone.upper()
    src = pathlib.Path(a.sorgenti or DROPBOX_CM / f'bag_{a.anno}')
    f_premi = trova(src, f'Praemien_CH_{a.anno}.csv')
    f_tarife = trova(src, f'Tarife_{a.anno}.csv')
    f_regioni = trova(src, f'praemienregionen-{a.anno}.xlsx')
    f_ass = trova(src, 'zugelassene-krankenversicherer-*.xlsx')

    # 1) nomi italiani dei prodotti
    nomi_prod = {}
    raw = open(f_tarife, encoding='utf-8-sig').read()
    prima = raw.split('\n', 1)[0]
    for r in csv.DictReader(raw.splitlines(), delimiter=';' if prima.count(';') > prima.count(',') else ','):
        if r.get('Kategorie') == 'MOD':
            nomi_prod[(r['Versicherer'].lstrip('0'), r['Tarif'])] = (r.get('Name_DE', '').strip(), r.get('Name_IT', '').strip())

    # 2) premi del cantone
    prodotti, franchigie = {}, {}
    for r in csv.DictReader(open(f_premi, encoding='utf-8-sig')):
        if r['Kanton'] != kt:
            continue
        if str(r.get('Geschäftsjahr', a.anno)) != str(a.anno):
            sys.exit(f"ERRORE: riga dell'anno {r.get('Geschäftsjahr')} in un file {a.anno}")
        num = r['Versicherer'].lstrip('0')
        tarif = r['Tarif'].strip()
        reg = cifra_finale(r['Region'])
        e = eta(r['Altersklasse'], r.get('Altersuntergruppe'))
        unf = 'U' if r['Unfalleinschluss'].upper().startswith('MIT') else 'N'
        fr = int(cifra_finale(r['Franchise']))
        franchigie.setdefault(e[0] if e.startswith('K') else e, set()).add(fr)
        p = prodotti.setdefault(num, {}).setdefault(tarif, {'tt': r['Tariftyp'], 'nb': r['Tarifbezeichnung'].strip(), 'p': {}})
        cella = p['p'].setdefault(reg, {}).setdefault(e, {}).setdefault(unf, {})
        if fr in cella and cella[fr] != float(r['Prämie']):
            sys.exit(f'ERRORE: due premi diversi per {num} {tarif} R{reg} {e} {unf} {fr}')
        cella[fr] = float(r['Prämie'])
    if not prodotti:
        sys.exit(f'ERRORE: nessun premio per il cantone {kt}')
    fr_ord = {k: sorted(v) for k, v in franchigie.items()}

    # 3) nomi degli assicuratori
    wb = openpyxl.load_workbook(f_ass, read_only=True, data_only=True)
    indice, grezzi = {}, {}
    for ws in wb.worksheets:
        ultimo = None
        for row in ws.iter_rows(values_only=True):
            row = list(row) + [None] * 8
            if ws.title.strip().lower() == 'index' and isinstance(row[1], int):
                indice[str(row[1])] = pulisci(row[3])
            elif isinstance(row[0], int) and row[2]:
                ultimo = str(row[0])
                grezzi[ultimo] = [str(row[2]), row[5]]
            elif ultimo and row[0] is None and row[1] is None and isinstance(row[2], str):
                grezzi[ultimo][0] += '\n' + row[2]           # nome spezzato su due righe del foglio
                grezzi[ultimo][1] = grezzi[ultimo][1] or row[5]
            else:
                ultimo = None
    ufficiale = {k: (pulisci(n), pulisci(g) if g and pulisci(g) not in ('---', '-') else None) for k, (n, g) in grezzi.items()}

    assicuratori, n_prod, tipi_conta = {}, 0, {}
    for num, prods in prodotti.items():
        nome_idx = indice.get(num) or (ufficiale.get(num, (None,))[0]) or f'Assicuratore {num}'
        uff, gruppo = ufficiale.get(num, (nome_idx, None))
        out = {}
        for tarif, d in prods.items():
            nde, nit = nomi_prod.get((num, tarif), ('', ''))
            nde = nde or d['nb']
            nome_it = nit or nde or tarif
            if tarif == 'BASE' and nome_it.lower() in ('base', 'assicurazione di base'):
                nome_it = 'Assicurazione di base (modello standard)'
            t, det = classifica(d['tt'], [tarif, d['nb'], nde, nit])
            tipi_conta[t] = tipi_conta.get(t, 0) + 1
            pr = {}
            for reg in sorted(d['p']):
                pr[reg] = {}
                for e in sorted(d['p'][reg], key=lambda x: ('EJK'.index(x[0]), x)):
                    lista = fr_ord['K' if e.startswith('K') else e]
                    pr[reg][e] = {u: [numero(d['p'][reg][e][u][f]) if f in d['p'][reg][e][u] else None for f in lista]
                                  for u in sorted(d['p'][reg][e], key=lambda x: 'NU'.index(x))}
            out[tarif] = {'n': nome_it.strip(), 'nd': nde.strip(), 't': t, 'd': DETTAGLI[det], 'bag': d['tt'], 'p': pr}
            n_prod += 1
        out = dict(sorted(out.items(), key=lambda kv: (ORDINE_TIPO[kv[1]['t']], kv[1]['n'].lower())))
        assicuratori[num] = {'nome': nome_breve(num, nome_idx), 'nome_ufficiale': uff, 'gruppo': gruppo, 'prodotti': out}
    assicuratori = dict(sorted(assicuratori.items(), key=lambda kv: kv[1]['nome'].lower()))

    # 4) NPA -> comune e regione
    wb = openpyxl.load_workbook(f_regioni, read_only=True, data_only=True)
    npa = {}
    for row in wb['A_COM'].iter_rows(values_only=True):
        if not row or not isinstance(row[0], int) or row[1] != kt or row[5] is None:
            continue
        bfs, _, comune, reg, distretto, plz, loc = row[:7]
        voci = npa.setdefault(str(int(plz)), [])
        v = next((x for x in voci if x['bfs'] == bfs), None)
        if not v:
            v = {'c': comune, 'r': int(reg), 'bfs': bfs, 'dist': distretto, 'l': []}
            voci.append(v)
        if loc and loc not in v['l']:
            v['l'].append(loc)
    npa = dict(sorted(npa.items()))

    oggi = datetime.date.today().strftime('%d.%m.%Y')
    premi = {
        'anno': a.anno, 'cantone': kt, 'generato': oggi,
        'fonte': f'UFSP (Ufficio federale della sanità pubblica), premi approvati {a.anno}: '
                 f'{os.path.basename(f_premi)}, {os.path.basename(f_tarife)}, {os.path.basename(f_ass)}',
        'unita': 'franchi al mese', 'regioni': sorted({r for p in prodotti.values() for d in p.values() for r in d['p']}),
        'eta': {k: v for k, v in ETA.items() if any(k in d['p'][r] for p in prodotti.values() for d in p.values() for r in d['p'])},
        'infortunio': {'N': 'senza infortunio', 'U': 'con infortunio'},
        'franchigie': fr_ord, 'tipi': TIPI, 'assicuratori': assicuratori,
    }
    npa_out = {'anno': a.anno, 'cantone': kt, 'generato': oggi,
               'fonte': f'UFSP, regioni di premio {a.anno}: {os.path.basename(f_regioni)} (foglio A_COM)',
               'nota': 'La regione di premio dipende dal comune di domicilio (n. UST del comune); il NPA è solo indicativo.',
               'npa': npa}

    # 5) controlli: se uno non torna, non si scrive nulla
    errori = []
    for num, tarif, reg, e, u, fr, atteso, etichetta in CONTROLLI.get(a.anno, []):
        try:
            val = assicuratori[num]['prodotti'][tarif]['p'][reg][e][u][fr_ord[e[0] if e.startswith('K') else e].index(fr)]
        except (KeyError, ValueError):
            val = None
        ok = val is not None and abs(val - atteso) < 0.001
        print(f"{'OK ' if ok else 'NO '} {etichetta}: atteso {atteso:.2f}, nei dati {val}")
        if not ok:
            errori.append(etichetta)
    for plz, comune, reg in CONTROLLI_NPA.get(a.anno, []):
        voci = npa.get(plz, [])
        ok = any(v['c'] == comune and v['r'] == reg for v in voci)
        print(f"{'OK ' if ok else 'NO '} NPA {plz} = {comune}, regione {reg}: nei dati {[(v['c'], v['r']) for v in voci]}")
        if not ok:
            errori.append(f'NPA {plz}')
    if not CONTROLLI.get(a.anno):
        print(f'ATTENZIONE: nessun controllo per il {a.anno}. Verifica a mano 5 premi su priminfo.admin.ch e aggiungili a CONTROLLI.')
    if errori:
        sys.exit(f'FERMO: non tornano {errori}. Nessun file scritto.')

    usc = pathlib.Path(a.uscita)
    f1 = usc / f'premi_{kt.lower()}_{a.anno}.json'
    f2 = usc / f'npa_{kt.lower()}_{a.anno}.json'
    json.dump(premi, open(f1, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    json.dump(npa_out, open(f2, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    print(f'scritto {f1} ({f1.stat().st_size:,} byte): {len(assicuratori)} assicuratori, {n_prod} prodotti, tipi {tipi_conta}')
    print(f'scritto {f2} ({f2.stat().st_size:,} byte): {len(npa)} NPA')


if __name__ == '__main__':
    main()
