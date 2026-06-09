# AgOpenGPS Fence Planner

Windows-program til planlaegning af rotationszoner og hegnslinjer til AgOpenGPS.

## Funktioner

- Finder automatisk `Documents\AgOpenGPS\Fields`
- Viser marker fra AgOpenGPS
- Importerer AgShare/TASKDATA ZIP
- Opretter egne markmapper under `Documents\FencePlanner\Fields`
- Laeser `Boundary.txt`
- Laeser `Field.kml`, `TASKDATA.XML` eller AgShare `fields.geojson`
- Viser Esri World Imagery satellitkort
- Har flytbare A/B-punkter direkte paa kortet
- Opdaterer zoner, hektar og hegnslinjer live
- Bruger `Antal zoner`, hvor fx 3 zoner giver 2 hegn
- Kan lave parallelle zoner eller vifte-zoner mellem to A/B-yderlinjer
- Har justerbar paeleafstand med 10/25/50 m som forvalg og mulighed for selv at skrive afstand
- Viser antal paele pr. hegnslinje og samlet antal paele
- Kan gemme og indlaese hegnsplaner igen senere
- Kan gemme som ny AgOpenGPS-mark og skrive `TrackLines.txt`
- Har KOR-fane med simpleRTK2B/NMEA GPS via COM-port
- Har QR-sync til mobilside uden bruger-login
- Har automatisk opdateringsknap under fanen `Program`

## QR-Sync Til Mobil

1. Lav eller indlaes en hegnsplan i Windows-programmet.
2. Gem hegnsplanen.
3. Start eventuelt lokal QR-server under fanen `Program`.
4. Tryk `Upload QR-sync`.
5. Scan QR-koden med mobilen.

Hvis sync-serveren koerer online med HTTPS, kan mobilen hente marker og linjer uden at desktop-programmet er aabent. Desktop-programmet beholder en hemmelig upload-noegle lokalt, saa QR-koden kun er et laeselink til mobilen.

Mobilen viser mark, hegn, paelepunkter, GPS-position og afstand til valgt hegnslinje.

## Installer Som Windows-Program

Fra GitHub release kan du normalt nojes med at downloade og koere:

```bat
FencePlanner_Installer.bat
```

Den henter selv nyeste programpakke og installerer Fence Planner.

Hvis du arbejder direkte fra kildekoden, kan du koere:

```bat
install_program.bat
```

## Start Uden Installation

Koer:

```bat
start_program.bat
```

## Afinstaller

Koer:

```bat
afinstaller_program.bat
```
