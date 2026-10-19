#!/usr/bin/env python3
"""Conti di riferimento della pagina, scritti a parte, per ricontrollare i casi di prova.

Rifà da zero i numeri che la pagina mostra (premio di oggi, 3 alternative, risparmio, franchigia che
conviene) leggendo solo dati/premi_ti_<anno>.json. Se un numero non torna con quello atteso, si ferma.

Uso:  python3 prove/riferimento.py
Dopo ogni nuovo anno di dati i valori attesi vanno ricalcolati e riscritti qui sotto (CASI).
"""
import json, pathlib, sys

QUI = pathlib.Path(__file__).resolve().parent
D = json.load(open(QUI.parent / 'dati' / 'premi_ti_2027.json', encoding='utf-8'))
SPESE = {'basso': 500, 'medio': 2000, 'alto': 6000}
ALIQ = {'E': 700, 'J': 700, 'K': 350}


def cat(p):
    if p['t'] == 'BASE': return 'libero'
    if p['t'] == 'HAM': return 'medico'
    if p['t'] == 'HMO': return 'hmo'
    d = p['d'].lower()
    if d.startswith('farmacia'): return 'farmacia'
    if d.startswith('telemedicina'): return 'tel'
    return 'flex'


def premio(num, code, reg, fa, f, inf):
    p = D['assicuratori'][num]['prodotti'].get(code)
    if not p: return None
    l = p['p'].get(reg, {}).get(fa, {}).get(inf)
    if not l: return None
    fr = D['franchigie'][fa]
    return l[fr.index(f)] if f in fr else None


def compat(c, acc):
    if c == 'libero': return True
    if c == 'flex': return 'medico' in acc or 'tel' in acc
    return c in acc


def alternative(reg, fa, F, inf, acc, escl, inf_oggi):
    # la polizza di oggi è esclusa; lo stesso prodotto senza infortunio (se oggi ce l'ha) no
    best = {}
    for num, a in D['assicuratori'].items():
        for code, p in a['prodotti'].items():
            stesso = (num, code) == escl
            if not compat(cat(p), acc) or (stesso and inf == inf_oggi): continue
            v = premio(num, code, reg, fa, F, inf)
            if v is None: continue
            if num not in best or v < best[num][0] or (v == best[num][0] and stesso): best[num] = (v, a['nome'], code, num)
    return sorted(best.values(), key=lambda x: (x[0], x[1].lower()))


def franchigia_migliore(num, code, reg, fa, inf, liv):
    s, righe = SPESE[liv], []
    for f in D['franchigie'][fa]:
        v = premio(num, code, reg, fa, f, inf)
        if v is None: continue
        righe.append((round(12 * v + min(s, f) + min(0.1 * max(s - f, 0), ALIQ[fa])), f))
    return min(righe)


# (nome, regione, fascia, premio di oggi, franchigia, infortunio delle alternative, va bene, polizza di oggi,
#  infortunio di oggi, livello di spese, prodotto per la franchigia)
#  -> atteso (risparmio all'anno, [3 casse], franchigia, totale, codice della migliore alternativa)
CASI = [
    ('adulta 1997, Helsana standard 300, lavora, oggi con infortunio, poche spese', '1', 'E',
     premio('1562', 'BASE', '1', 'E', 300, 'U'), 300, 'N', {'medico', 'tel'}, ('1562', 'BASE'), 'U', 'basso', None,
     (2041, ['Agrisano', 'KPT', 'Aquilana'], 2500, 6266, 'AGRIsmart')),
    ('giovane 2004, CSS medico di famiglia Profit 2500, non lavora, spese medie', '1', 'J',
     premio('8', '01_046', '1', 'J', 2500, 'U'), 2500, 'U', {'medico'}, ('8', '01_046'), 'U', 'medio', None,
     (575, ['Sanitas', 'CSS', 'EGK'], 2500, 5833, 'Hausarztmodell 1 (NetMed 1)')),
    ('adulta 1990, KPTwin.plus 2500, lavora, oggi senza infortunio', '1', 'E',
     premio('376', 'HMO_A', '1', 'E', 2500, 'N'), 2500, 'N', {'hmo', 'tel'}, ('376', 'HMO_A'), 'N', 'basso', ('376', 'HMO_A'),
     (0, ['KPT', 'Aquilana', 'Assura'], 2500, 6176, 'KPTwinsmart')),
    ('adulta 1985 a Gordola, cassa «non lo so», lettera 526.60 confermata Helsana R2 1500', '2', 'E',
     526.60, 1500, 'U', {'medico'}, ('1562', 'BFP_CM'), 'U', 'medio', None,
     (127, ['Sanitas', 'Helsana', 'Assura'], 2500, 7493, 'Hausarztmodell 1 (NetMed 1)')),
    # dal 19.10.2026 (revisione): con l'infortunio di oggi e il datore che lo copre, la prima alternativa può
    # essere la stessa polizza senza infortunio. Qui KPTwin.plus senza (473.00) pareggia KPTwin.smart: vince la sua.
    ('adulta, KPTwin.plus 2500, lavora, oggi CON infortunio, poche spese', '1', 'E',
     premio('376', 'HMO_A', '1', 'E', 2500, 'U'), 2500, 'N', {'hmo', 'tel'}, ('376', 'HMO_A'), 'U', 'basso', None,
     (427, ['KPT', 'Aquilana', 'Assura'], 2500, 6176, 'HMO_A')),
    # Il difetto della 1.0: qui la pagina proponeva Sanitas «Medico di famiglia 2» (301.70, CHF 212 all'anno, altra
    # lista di medici); togliendo solo l'infortunio dalla polizza di oggi si scende a 297.35, CHF 265 all'anno.
    ('giovane, Sanitas Medico di famiglia 1, 2500, lavora, oggi CON infortunio, spese medie', '1', 'J',
     premio('1509', 'Hausarztmodell 1 (NetMed 1)', '1', 'J', 2500, 'U'), 2500, 'N', {'medico'}, ('1509', 'Hausarztmodell 1 (NetMed 1)'), 'U', 'medio', None,
     (265, ['Sanitas', 'CSS', 'EGK'], 300, 5472, 'Hausarztmodell 1 (NetMed 1)')),
]

errori = 0
for nome, reg, fa, cur, F, inf, acc, escl, inf_oggi, liv, ref, atteso in CASI:
    al = alternative(reg, fa, F, inf, acc, escl, inf_oggi)
    risp = round((cur - al[0][0]) * 12)
    r = ref or (al[0][3], al[0][2])
    tot, fbest = franchigia_migliore(r[0], r[1], reg, fa, inf, liv)
    trovato = (max(risp, 0), [a[1] for a in al[:3]], fbest, tot, al[0][2])
    ok = trovato == atteso
    errori += not ok
    print(('OK   ' if ok else 'DIVERSO ') + nome)
    print('     premio di oggi %.2f, migliore %s %.2f, risparmio %s, franchigia %s (totale %s)' % (cur, al[0][1], al[0][0], risp, fbest, tot))
    if not ok: print('     atteso', atteso, 'trovato', trovato)
sys.exit(1 if errori else 0)
