# AgOpenGPS Fence Planner

Windows-program til planlægning af rotationszoner og hegnslinjer til AgOpenGPS.

## Funktioner

- Finder automatisk `Documents\AgOpenGPS\Fields`
- Viser marker fra AgOpenGPS
- Læser `Boundary.txt`
- Læser `Field.kml`, hvis den findes
- Kan bruge `zISOXML\v3/v4\TASKDATA.XML` som fallback, når `Field.kml` mangler
- Kan importere én samlet AgShare export ZIP og bruge `geojson/fields.geojson` som georeference
- Opretter egne markmapper under `Documents\FencePlanner\Fields`
- Kan gemme og indlæse hegnsplaner igen senere fra markens `FencePlans`-mappe
- Viser Esri World Imagery satellitkort, når marken har georeference fra `Field.kml`, `TASKDATA.XML` eller AgShare ZIP
- Kan skifte mellem `Esri nyeste` og `Esri Clarity`
- Har kortkvalitet `Høj` eller `Normal`
- Har flytbare A/B-punkter direkte på kortet
- Opdaterer zoner, hektar og hegnslinjer live ved flytning af A/B
- Bruger `Antal zoner`, hvor fx 3 zoner giver 2 hegn
- Har justerbar pæleafstand med 10/25/50 m som forvalg og mulighed for selv at skrive afstand
- Viser antal pæle pr. hegnslinje og samlet antal pæle
- Eksporterer en mobilklar `FenceGuide.html`, som kan åbnes direkte på telefon/tablet
- Gemmer som ny markmappe
- Skriver hegnslinjer til `TrackLines.txt`
- Har KØR-fane med simpleRTK2B/NMEA GPS via COM-port
- Viser GPS-position og afstand til valgt hegnslinje
- Kan eksportere flere gemte hegnsplaner til en mobilsky-side

## Mobilsky

`Eksporter mobilsky` laver en mappe med `index.html` og `data.json`, som kan hostes på en HTTPS-side. Hvis den uploades til GitHub Pages fra et offentligt repository, bliver marknavne og GPS-koordinater offentlige.

## Installer som Windows-program

Fra GitHub release kan du normalt nøjes med at downloade og køre:

```bat
FencePlanner_Online_Installer.bat
```

Den henter selv nyeste programpakke og installerer Fence Planner.

Hvis du arbejder direkte fra kildekoden, kan du køre:

```bat
install_program.bat
```

Installeren bygger EXE, installerer den i `%LOCALAPPDATA%\Programs\AgOpenGPS Fence Planner`, og opretter genvej på skrivebordet og i Start-menuen.

## Start uden installation

Kør:

```bat
start_program.bat
```

Hvis programmet allerede er installeret, åbner den installerede EXE. Ellers starter den fra kildekoden.

## Afinstaller

Kør:

```bat
afinstaller_program.bat
```

## Mobilguide

1. Lav zoner/hegn i Windows-programmet.
2. Tryk `Eksportér til mobil`.
3. Gem `*_FenceGuide.html`.
4. Send HTML-filen til telefonen.
5. Åbn den i Chrome/Edge på telefonen.
6. Tryk `Start GPS`.

Mobilguiden viser mark, hegn, pælepunkter og afstand til valgt hegnslinje.
