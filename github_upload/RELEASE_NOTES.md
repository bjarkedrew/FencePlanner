# AgOpenGPS Fence Planner v1.0.0

Windows-program til planlægning af hegn, zoner og pælepunkter ud fra AgOpenGPS-markfiler.

## Hovedfunktioner

- Finder automatisk `Documents\AgOpenGPS\Fields`
- Viser AgOpenGPS-marker
- Læser `Boundary.txt` og `Field.kml`
- Kan bruge `zISOXML\v3/v4\TASKDATA.XML` som fallback, når `Field.kml` mangler
- Viser satellitkort, når marken har georeference fra `Field.kml` eller `TASKDATA.XML`
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

## Download

For almindelig installation:

1. Download `FencePlanner_Setup.bat`
2. Download `FencePlanner_Setup.ps1`
3. Læg dem i samme mappe
4. Kør `FencePlanner_Setup.bat`

Hvis online setup ikke er sat op endnu, kan man i stedet downloade:

- `AgOpenGPS_FencePlanner_package.zip`
- `Installer_fra_lokal_pakke.bat`

Læg dem i samme mappe og kør `Installer_fra_lokal_pakke.bat`.

## Release assets

- `AgOpenGPS_FencePlanner_package.zip`
- `FencePlanner_Setup.bat`
- `FencePlanner_Setup.ps1`
- `Installer_fra_lokal_pakke.bat`

## SHA256

```text
3F272A05E321C6C42AA72726575F2643FD86B9F4789F063710401D084D1C8F1F
```
