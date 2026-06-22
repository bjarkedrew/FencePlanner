# AgOpenGPS Fence Planner

Windows-program til planlaegning af rotationszoner og hegnslinjer til AgOpenGPS.

Aktuel programversion: `v1.0.15`

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
- Kan lave parallelle zoner eller vifte-zoner mellem to yderlinjer
- Kan lave kurve-linjer ud fra A/B-punkter paa markgransen
- Vifte tager hoejde for A/B-raekkefoelgen og deler fra linje til linje
- Har justerbar paeleafstand med 10/25/50 m som forvalg og mulighed for selv at skrive afstand
- Viser antal paele pr. hegnslinje og samlet antal paele
- Kan gemme og indlaese hegnsplaner igen senere
- Kan gemme som ny AgOpenGPS-mark og skrive `TrackLines.txt`
- Har KOR-fane med simpleRTK2B/NMEA GPS via COM-port
- Har Mobil QR med midlertidigt HTTPS-link til den aktuelle mark/hegnsplan
- Har automatisk opdateringsknap under fanen `Program`
- Tjekker automatisk ved opstart om nyeste GitHub release er nyere

## QR-Sync Til Mobil

1. Lav eller indlaes en hegnsplan i Windows-programmet.
2. Gem hegnsplanen.
3. Tryk `Mobil QR`.
5. Scan QR-koden med mobilen.

Mobil QR laver et midlertidigt HTTPS-link og QR-kode for den mark/plan, der er aaben lige nu. Der bruges ikke GitHub-upload, sync-server eller en mappe med alle marker.

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
