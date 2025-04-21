
# Finanšu panelis 💰

## Projekta apraksts
**Finanšu panelis** ir tīmekļa lietotne, kas palīdz lietotājiem pārvaldīt personīgās finanses, reģistrēt ienākumus un izdevumus, izvirzīt finanšu mērķus un pārskatīt atlikumu dažādās valūtās.

## Funkcionalitāte

- ✅ Lietotāja reģistrācija un ielogošanās
- 💸 Ienākumu pievienošana un dzēšana
- 📉 Izdevumu pievienošana un dzēšana
- 🎯 Mērķu izvirzīšana (uzkrājumi/tēriņu ierobežojumi), papildināšana un dzēšana
- 🌍 Valūtas konvertācija (EUR uz USD, GBP, JPY)
- 📊 Pārskatāms atlikums un mērķu progress

## Izmantotās tehnoloģijas

- **Python** (Flask)
- **SQLite3** – datubāzes pārvaldība
- **HTML/CSS** – saskarne
- **Jinja2** – HTML veidņu renderēšana
- **Fixer.io API** – valūtas kursu iegūšanai

## Projekta struktūra

```bash
.
├── app.py                   # Galvenā Flask lietotne
├── templates/
│   ├── dashboard.html       # Sākuma lapa ar kopsavilkumu
│   ├── ienakumi.html        # Ienākumu pievienošanas lapa
│   ├── izdevumi.html        # Izdevumu pievienošanas lapa
│   ├── login.html           # Pieslēgšanās lapa
│   ├── register.html        # Reģistrācijas lapa
│   ├── merki.html           # Finanšu mērķu pārvaldības lapa
│   └── index.html           # Galvenā pāradresēšanas lapa
└── finansesprogr1.db        # SQLite datubāze
```

## Uzstādīšana un palaišana

1. Klonē vai lejupielādē repozitoriju:
   ```bash
   git clone https://github.com/elinuklis/finansesProg.git
   cd finansesProg
   ```

2. Instalē nepieciešamās atkarības:
   ```bash
   pip install flask requests werkzeug
   ```

3. Palaid programmu:
   ```bash
   python app.py
   ```

4. Atver pārlūkprogrammā:
   ```
   http://127.0.0.1:5000/
   ```

## Prasības

- Interneta savienojums (valūtas konvertēšanai)
- Pārlūks: Chrome, Firefox, Edge, Opera, Brave
- Python 3.8+ ar Flask

## Izstrādes gaita

Projekts veidots pēc **iteratīvā izstrādes modeļa**, ietverot šādus posmus:

| Posms                     | Apraksts |
|--------------------------|----------|
| Projekta izpēte          | Aptauja, analogu salīdzinājums |
| Prasību specificēšana    | Sistēmas funkcionalitātes apraksts |
| Projektēšana             | Saskarnes skices, datubāzes modelis |
| Izstrāde                 | Front-end un back-end izstrāde |
| Testēšana                | Vienībtesti, akcepttesti |
| Dokumentācija            | PPS, lietotāja ceļvedis, README |
| Publicēšana              | PythonAnywhere, GitHub, Figma |

## Saistītie resursi

- 🔗 Mājaslapa: [elinuklis.pythonanywhere.com](https://elinuklis.pythonanywhere.com)
- 💾 [Programmas kods GitHub](https://github.com/elinuklis/finansesProg)
- 🎨 [Figma dizains](https://www.figma.com/design/KgTjd6dKwbpQCh9ohAzZCs/finanseskkas?node-id=4-70)
