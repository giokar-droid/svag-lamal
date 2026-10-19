# La tua cassa malati 2027: ti conviene cambiare? — pagina SVAG

Versione **1.0.1** del 19.10.2026 (la 1.0 rivista lo stesso giorno: vedi «Revisione del 19.10.2026»). Copia **locale**: nessun repository remoto, nessun push.
Si pubblica solo quando Giorgio lo decide.

Pagina statica che una persona apre dal telefono, come il wizard del budget (v1.5) e il wizard RC auto:
risponde a una decina di domande sulla sua assicurazione di base e la pagina le dice, con i premi
ufficiali UFSP (Ufficio federale della sanità pubblica) 2027 del Ticino, se per il 2027 le conviene
cambiare cassa, quanto risparmia e perché. Alla fine può mandare tutto a Giorgio su WhatsApp.

## I file

| File | Cosa fa |
|---|---|
| `index.html` | La pagina: grafica, domande, conti, risultato, invio. Nessuna libreria esterna |
| `dati/premi_ti_2027.json` | Premi 2027 del Ticino, 21 casse, 105 prodotti, regioni 1 e 2 |
| `dati/npa_ti_2027.json` | 241 NPA del Ticino con comune, n. UST, regione di premio |
| `dati/build_dati.py` | Rigenera i due JSON dai file UFSP: `python3 build_dati.py --anno 2028` |
| `prove/riferimento.py` | Rifà a parte i conti dei casi di prova e si ferma se un numero non torna |
| `.nojekyll` | Per GitHub Pages, il giorno in cui si pubblica |

Per un anno nuovo: rigenerare i dati, cambiare `ANNO`, le date in `DATE` e i nomi dei file in `carica(...)`
dentro `index.html`, poi ricalcolare i valori attesi in `prove/riferimento.py`.

## Il link

Tutto quello che sta dopo `#` resta nel browser: il sito che ospita la pagina non lo riceve.

- `#pre=npa:6964` propone il numero postale: la pagina lo mostra con l'etichetta «proposto da Giorgio»
  e la persona lo conferma o lo corregge.
- `#pre=npa:6596;comune:5108` sceglie anche il comune (n. UST), per i 7 NPA divisi fra due regioni.
- Ogni altra chiave è ignorata. **Mai nel link** nomi, nascite, casse, premi o altri dati personali.
- Riaperto uguale riprende le risposte. Un link con un NPA diverso non cancella niente: il NPA proposto
  entra solo se la persona non ne ha ancora scritto uno.

In locale: `http://127.0.0.1:8777/#pre=npa:6964` (configurazione `lamal` in `Dropbox/.claude/launch.json`:
`python3 -m http.server 8777 --bind 127.0.0.1 --directory ~/svag-lamal-repo`).

## Le domande

1. Anno di nascita (fascia 2027: bambini 0-18, giovani 19-25, adulti 26+).
2. NPA; se cade su due regioni, il comune.
3. Lavoro di almeno 8 ore a settimana per lo stesso datore; se sì, se oggi c'è l'infortunio.
4. Cassa di oggi (21 casse del Ticino, «Non lo so»).
5. Modello di oggi (standard, medico di famiglia, rete HMO, Telmed, altro, «Non lo so»).
6. Prodotto esatto, filtrato per cassa e modello. Non compare se il prodotto è uno solo.
7. Franchigia di oggi (solo quelle che il prodotto offre).
8. Premio 2027 della lettera, facoltativo: se c'è, vince sui dati.
9. Cosa va bene nel 2027 (scelta multipla): qualsiasi medico, medico di famiglia, studio HMO, Telmed, farmacia.
10. Uso della sanità: visite, farmaci regolari, cure in corso o previste.
11. Complementari: dentista, ospedale, altro, nessuna, «Non lo so».

Una domanda per schermata, scelte grandi, barra di avanzamento, tema chiaro e scuro (segue il telefono;
il pulsante in alto lo cambia su quel dispositivo). Sulle scelte singole la pagina va avanti da sola.
Mentre si scrive non si ridisegna niente: si aggiorna solo la riga sotto il campo.

## I conti

- **Premio di oggi.** Il premio della lettera, se c'è; altrimenti i dati UFSP per cassa, prodotto, regione,
  fascia, franchigia e infortunio. Senza prodotto esatto la pagina usa la forchetta dei prodotti di quella
  cassa e di quel modello.
- **Premio della lettera.** Oltre CHF 1'500 al mese la pagina lo tratta come un importo all'anno: lo segnala,
  blocca «Avanti» e non lo usa nei conti. Se è più basso di ogni premio 2027 per quell'età e quella regione,
  chiede di controllare sussidi e rimborso della tassa ambientale. Se combacia al centesimo con i dati della cassa indicata, completa franchigia,
  prodotto e infortunio mancanti. Con la cassa «Non lo so» la pagina mostra con chi combacia e chiede
  «È la tua cassa?»: conta solo se la persona tocca «Sì, è la mia». Motivo: nel collaudo il premio tondo
  540.00 combaciava per caso con un prodotto sana24.
- **Infortunio.** Chi lavora almeno 8 ore per lo stesso datore è confrontato senza infortunio. Se non sa
  se oggi ce l'ha, il premio di oggi è calcolato senza (ipotesi prudente: risparmio più basso) e la
  pagina lo dice.
- **Alternative.** Stessa franchigia, la più economica per ogni cassa, solo modelli compatibili con la
  domanda 9. Il modello standard va sempre bene; i modelli flessibili vanno bene a chi accetta il medico
  di famiglia o il Telmed. La polizza di oggi è esclusa, gli altri prodotti della stessa cassa no
  (etichetta «la tua cassa»). Se oggi c'è l'infortunio e il datore di lavoro lo copre, la stessa polizza
  senza infortunio è un'alternativa (etichetta «la tua polizza, senza infortunio»; a parità di premio vince
  lei): il risultato dice allora «Ti conviene togliere l'infortunio», con i passi per restare nella cassa.
- **Verdetto.** Risparmio all'anno = 12 × (premio di oggi − migliore alternativa).
  - da CHF 120 in su: «Ti conviene cambiare: risparmi circa X all'anno»;
  - sotto CHF 120: «Sei già messa bene»;
  - premio di oggi o franchigia sconosciuti: «Dipende da…», con il premio mensile oltre il quale conviene.
- **Franchigia.** Costo totale in un anno = 12 premi + spese fino alla franchigia + 10 % oltre, fino a
  CHF 700 (adulti e giovani) o CHF 350 (bambini). Spese ipotizzate: CHF 500, 2'000 o 6'000 all'anno
  (poche, medie, molte), scritte nella pagina. Il livello stimato dalle risposte si può cambiare nel
  risultato. Il grafico è in SVG, con la stessa tabella dei numeri sotto.
- **Date.** Raccomandata entro venerdì 13.11.2026, disdetta arrivata entro lunedì 30.11.2026, nuova
  cassa da venerdì 01.01.2027. Franchigia: abbassarla entro il 30.11, alzarla entro giovedì 31.12.2026.

## Il ritorno

Il pulsante principale apre WhatsApp verso Giorgio (+41 78 871 69 00) con il messaggio già scritto.
In riserva ci sono «Copia il messaggio» ed e-mail (giorgio.carrara@svag.ch).

```
Ciao Giorgio, ecco le mie risposte sulla cassa malati 2027 (Nome), compilate il GG.MM.AAAA.
La pagina dice: mi conviene cambiare, risparmio circa CHF X all'anno.
Il testo qui sotto serve al tuo programma ed è giusto così: va mandato com'è.

{…JSON…}
```

| Chiave | Cosa contiene |
|---|---|
| `tipo`, `versione`, `creato`, `nome` | `svag-lamal-2027`, `1.0.1`, `GG.MM.AAAA hh:mm`, il nome se scritto |
| `risposte` | le risposte così come date: `nascita` (solo l'anno), `npa`, `comune_ust`, `lavoro_8_ore`, `infortunio_oggi`, `cassa` (n. UFSP o `nonso`), `modello`, `prodotto` (codice UFSP), `franchigia`, `premio_lettera`, `va_bene`, `complementari`. Le risposte su visite, farmaci e cure **non partono**: restano sul dispositivo e a Giorgio arriva solo `livello_spese` |
| `risultato` | quello che la pagina ha mostrato: fascia, regione, comune, cassa e prodotto (anche dedotti), franchigia, `premio_mese`, `fonte_premio` (`lettera` o `dati`), `verdetto` (`cambia`, `bene`, `dipende`) e `motivo`, `risparmio_anno`, `franchigia_confronto`, le 3 `alternative` con premio e risparmio, `livello_spese`, `spese_ipotesi`, `franchigia_consigliata` |
| `dati` | anno dei premi e data di elaborazione |

Le risposte restano nel browser (`localStorage`, chiave `svag-lamal-2027-v1`, sempre con try/catch).
«Cancella le mie risposte» toglie solo quella chiave. Il tema scelto a mano sta in `svag-lamal-tema`.

## Collaudo del 19.10.2026

Nel browser di anteprima, in una scheda a parte, a 390×844 e a 1280×800, in tema chiaro e scuro. Le
risposte sono di prova. I numeri sono stati rifatti a parte con `prove/riferimento.py`: tornano tutti.

| Caso | Premio di oggi | Verdetto | Prime 3 alternative | Franchigia che conviene |
|---|---|---|---|---|
| Adulta 1997, Helsana standard, franchigia 300, lavora, oggi con infortunio, poche spese | 756.00 | cambiare, CHF 2'041 all'anno | Agrisano AGRIsmart 585.90, KPT 592.30, Aquilana 592.80 | 2'500, CHF 6'266 in tutto |
| Giovane 2004, CSS medico di famiglia Profit, 2'500, non lavora, spese medie | 367.30 | cambiare, CHF 575 all'anno | Sanitas Medico di famiglia 1 319.40, CSS Multimed 335.70, EGK-Care 343.10 | 2'500, CHF 5'833 |
| Adulta 1990, KPTwin.plus 2'500, lavora, oggi senza infortunio | 473.00 | «Sei già messa bene» | KPT KPTwin.smart 473.00 (costa uguale), Aquilana, Assura | 2'500, CHF 6'176 |
| Adulta 1985 a Gordola (NPA diviso, comune scelto), cassa «Non lo so», lettera 526.60 | 526.60 (combacia con Helsana R2, 1'500, confermato) | cambiare, CHF 127 all'anno | Sanitas 516.05, Helsana R1 519.80, Assura 532.10 | 2'500, CHF 7'493 |

Provati anche: «Dipende» per prodotto non riconosciuto (forchetta Helsana 519.80-553.70), per premio
sconosciuto e per franchigia sconosciuta; un bambino del 2015 (franchigie 0-600, tetto CHF 350); anno e
NPA mancanti bloccano «Avanti»; `#pre` con NPA fuori Ticino, con `nome:` e illeggibile (ignorati);
ripresa dopo il ricaricamento; «Cancella»; nome scritto senza ridisegno; cambio del livello di spese
(la pagina resta al suo posto); il messaggio WhatsApp catturato senza aprirlo (circa 2'200 caratteri);
«Copia» con gli appunti simulati. Nessun errore in console, nessun testo sotto i 15 px, nessuno
scorrimento orizzontale.

## Limiti

- WhatsApp ed e-mail non sono stati aperti davvero. Il link `wa.me` è di circa 2'150 caratteri e il `mailto:`
  di circa 2'200: alcuni programmi di posta (Outlook su Windows) tagliano i `mailto:` oltre circa 2'000.
  Resta «Copia».
- Le spese per livello (500, 2'000, 6'000) sono ipotesi, non dati: la franchigia consigliata è
  indicativa, e con spese medie la differenza fra franchigie è spesso di pochi franchi.
- Con il medico di famiglia e i modelli flessibili la pagina non sa se il medico è nella lista della
  nuova cassa: lo dice e rimanda a Giorgio.
- 4 prodotti (CSS Multimed, SWICA Favorit Medpharm e Multichoice, Helsana BeneFit PLUS Flexmed) qui sono
  modelli flessibili, come li chiama l'UFSP dal 2027; il wizard cassa malati li tiene fra i medici di
  famiglia.
- Il contributo ospedaliero di CHF 15 al giorno e i sussidi RIPAM (riduzione individuale dei premi) non
  entrano nei conti.

## Revisione del 19.10.2026 (versione 1.0.1)

Revisione a parte della 1.0, con le correzioni fatte nello stesso giro:

- **Infortunio e polizza di oggi.** La 1.0 escludeva sempre la polizza di oggi dalle alternative, anche
  quando il confronto è senza infortunio e oggi l'infortunio c'è. Caso: giovane con Sanitas Medico di
  famiglia 1, franchigia 2'500, con infortunio, lavora, accetta solo il medico di famiglia. La 1.0 proponeva
  Sanitas Medico di famiglia 2 (CHF 301.70, risparmio CHF 212 all'anno, altra lista di medici); togliendo
  solo l'infortunio la stessa polizza scende a CHF 297.35 (CHF 265 all'anno). Ora è il caso 6 di
  `prove/riferimento.py`; il caso 5 è KPTwin.plus con infortunio (CHF 508.60 → 473.00, CHF 427 all'anno).
- **Messaggio a Giorgio.** Tolte dal JSON le risposte su visite, farmaci e cure (dati sulla salute): resta il
  livello di spese. Il testo del messaggio è di circa 1'400 caratteri; codificati nel link diventano circa
  2'150 (`wa.me`) e 2'200 (`mailto:`), quindi l'e-mail resta sopra i 2'000.
- **Premio della lettera.** Importi all'anno bloccati e fuori dai conti (prima entravano: CHF 6'000 «al mese»
  poteva dare un risparmio di decine di migliaia di franchi); cifra illeggibile bloccata; avviso sotto il minimo di
  mercato; nella domanda, «prima del rimborso della tassa ambientale».
- **Testi.** «cambia la cassa, non il modo di curarti» tolto; con la stessa cassa la pagina non dice più
  «cambia la cassa»; CHF e IP sciolti alla prima comparsa; chi riceve l'indennità di disoccupazione è coperto
  per gli infortuni e risponde «Sì»; sotto le casse, chi non ha ancora una cassa svizzera è mandato da Giorgio
  (obbligo entro 3 mesi dall'arrivo); con il premio della lettera, l'infortunio sconosciuto non è più
  descritto come «ipotesi» del calcolo; «gruppo Groupe Mutuel» → «Groupe Mutuel».
- **Accessibilità.** Ogni gruppo di scelte ha il nome della sua domanda (lettori di schermo).

