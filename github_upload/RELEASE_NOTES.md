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
- QR-sync testserver med QR-parring uden bruger-login
- QR-sync starter lokal testserver automatisk ved lokal upload, hvis den ikke koerer
- Ny `Vifte`-knap med fire punkter: A1/B1 og A2/B2 som yderlinjer
- Vifte fordeler hegnslinjer mellem de to yderlinjer; A1-A2 bestemmer aabningen
- Satellitkort-indstillinger er fjernet fra hovedsiden, saa datafeltet faar mere plads
- Knapper/indstillinger i planlaegning ligger nu i et scrollfelt
- Opdateringsknappen henter og installerer nyeste release automatisk
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
35A96EA0654A7B77301FF2813332878BB45C3A0237A54D790D18E9B3B3DAF4B0
```
