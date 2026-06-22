# AgOpenGPS Fence Planner test

Windows-program til planlægning af hegn, zoner og pælepunkter ud fra AgOpenGPS-markfiler.

## Hovedfunktioner

- Finder automatisk `Documents\AgOpenGPS\Fields`
- Viser AgOpenGPS-marker
- Læser `Boundary.txt` og `Field.kml`
- Kan bruge `zISOXML\v3/v4\TASKDATA.XML` som fallback, når `Field.kml` mangler
- Kan importere én samlet AgShare export ZIP og bruge `geojson/fields.geojson` som georeference
- Opretter egne Fence Planner-markmapper under `Documents\FencePlanner\Fields`
- Kan gemme og indlæse hegnsplaner igen senere fra markens `FencePlans`-mappe
- Viser satellitkort, når marken har georeference fra `Field.kml`, `TASKDATA.XML` eller AgShare ZIP
- Flytbare A/B-punkter
- Live opdatering af zoner og hegn
- Lige hektar pr. zone
- Justerbar pæleafstand
- Viser antal pæle
- Gemmer ny mark til AgOpenGPS
- Skriver hegnslinjer til `TrackLines.txt`
- KØR-fane med GPS/simpleRTK2B
- Mobilguide med HTTPS-link og QR-kode
- Telefonens GPS kan bruges som markør ude i marken
- Mobilsky-eksport kan samle flere gemte hegnsplaner til en mobilside
- Ny enklere `Mobil QR`, der laver midlertidigt HTTPS-link til kun den aktuelle mark
- QR-koden peger paa en fast HTTPS-mobilside i stedet for lokal sync-server
- Ny `Vifte`-knap med fire punkter: A1/B1 og A2/B2 som yderlinjer
- Vifte fordeler hegnslinjer mellem de to yderlinjer; A1-A2 bestemmer aabningen
- Satellitkort-indstillinger er fjernet fra hovedsiden, saa datafeltet faar mere plads
- Knapper/indstillinger i planlaegning ligger nu i et scrollfelt
- Opdateringsknappen henter og installerer nyeste release automatisk
- QR-sync er erstattet af enklere `Mobil QR` til én aktuel mark ad gangen
- Mobil QR laver midlertidigt HTTPS-link og QR-kode uden GitHub-upload
- Mobil QR uploader ikke markdata til GitHub Pages og laver ikke online sync-mappe
- Vifte tager nu hoejde for A/B-raekkefoelgen og deler fra linje til linje
- Programnavn og Program-fane viser nu samme versionsnummer som GitHub release
- Antal zoner har nu tydelige plus/minus-knapper, saa zonetallet kan skrues op uden den lille spinbox-pil
- De indbyggede pile i zonetalsfeltet er skjult, saa kun plus/minus-knapperne bruges
- `Generer zoner`, `Vaelg A/B` og `Vifte`-knapperne er fjernet fra planlaegningspanelet
- Dropdown til linjetype starter nu punktvalg direkte paa kortet
- Ny linjetype `Kurve`, hvor A/B-punkter paa boundaryen bruges til kurvebaseret planlaegning
- Programmet tjekker ved opstart om GitHub har en nyere release
- Program/Om-fanen har nu sprogvalg mellem dansk og engelsk tekst
- `Koer mark` skifter direkte til KØR-fanen med valgt mark og hegnslinjer
- KØR-fanen viser linjelængde, pæle og GPS-koordinater for valgt hegnslinje

## Download

For almindelig installation:

1. Download `FencePlanner_Installer.bat`
2. Kør filen
3. Installeren henter selv resten af programmet fra nyeste GitHub release

Hvis online setup ikke er sat op endnu, kan man i stedet downloade:

- `AgOpenGPS_FencePlanner_package.zip`
- `Installer_fra_lokal_pakke.bat`

Læg dem i samme mappe og kør `Installer_fra_lokal_pakke.bat`.

## Release assets

- `AgOpenGPS_FencePlanner_package.zip`
- `FencePlanner_Installer.bat`
- `Installer_fra_lokal_pakke.bat`

## SHA256

```text
57241C24DA8DA25B6BC046EE905CA8E239D92F7BFDA857FAC0AFB2B28619DAD8
```
