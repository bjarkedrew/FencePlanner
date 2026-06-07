# FencePlanner
a planning tool for fences.
**AgOpenGPS Fence Planner**

AgOpenGPS Fence Planner er et Windows-program til at planlægge midlertidige hegn, folde og zoner direkte ud fra dine AgOpenGPS-markfiler.

Programmet læser automatisk dine marker fra:

```text
Documents\AgOpenGPS\Fields
```

Det bruger markens `Boundary.txt` og `Field.kml` til at vise marken korrekt på satellitkort og til at lave GPS-baseret mobilguide.

**Hvad Programmet Kan**

- Vise alle AgOpenGPS-marker
- Læse markgrænser fra `Boundary.txt`
- Læse georeference fra `Field.kml`
- Vise marken på satellitkort
- Oprette flytbare A/B-punkter
- Opdele marken i zoner/folde
- Lave lige store hektar pr. zone
- Beregne hegnslinjer mellem zonerne
- Vise pælepunkter med valgfri afstand
- Gemme planen som en ny AgOpenGPS-mark
- Skrive hegnslinjer til `TrackLines.txt`
- Vise GPS-position i KØR-fanen med simpleRTK2B
- Vise afstand til valgt hegnslinje
- Starte mobilguide med QR-kode

**Sådan Virker Det**

1. Åbn programmet.
2. Vælg en mark fra listen.
3. Vælg antal zoner.
4. Vælg pæleafstand, fx `10 m`, `25 m`, `50 m` eller skriv selv en afstand.
5. Tryk `Vælg A/B`.
6. Klik A-punkt og B-punkt på kortet.
7. Flyt A/B-punkterne rundt, indtil hegnene ligger rigtigt.
8. Programmet opdaterer zoner, arealer, hegn og pæle live.
9. Tryk `Gem som ny mark`, hvis planen skal bruges i AgOpenGPS.
10. Tryk `Start mobilguide`, hvis du vil bruge telefonen som GPS-guide ude i marken.

**Mobilguide**

Mobilguiden åbnes via QR-kode.

Når du trykker `Start mobilguide`, gør programmet automatisk dette:

- starter en lokal webguide
- laver et sikkert HTTPS-link
- kopierer linket
- viser QR-kode
- sender mark, hegn og pæle til mobilen
- lader telefonens GPS vise afstand til valgt hegnslinje

På mobilen scanner du QR-koden, åbner siden og trykker `GPS`.

**Typisk Brug**

Programmet er lavet til dig, der vil:

- dele en mark op i lige store folde
- planlægge elhegn
- finde hvor hegnslinjerne skal gå
- se hvor mange pæle der skal bruges
- bruge mobilen som guide ude i marken
- gemme planen tilbage til AgOpenGPS som en ny mark

Det er især tænkt til praktisk markarbejde, hvor planen laves på computeren, og udførelsen sker ude i marken med telefonens GPS.

**Step By Step: Download Og Opsætning Fra GitHub**

1. Gå ind på GitHub-siden for programmet.

2. Klik på `Releases` i højre side.

3. Åbn den nyeste release.

4. Download denne fil:

```text
FencePlanner_Online_Installer.bat
```

Den henter selv resten af programmet fra nyeste release.

5. Læg filen i `Downloads`.

6. Højreklik på:

```text
FencePlanner_Online_Installer.bat
```

7. Vælg:

```text
Kør som administrator
```

8. Windows kan advare om ukendt program. Tryk:

```text
Flere oplysninger
Kør alligevel
```

9. Installeren downloader programpakken og installerer Fence Planner.

10. Når installationen er færdig, ligger programmet på skrivebordet som:

```text
AgOpenGPS Fence Planner
```

11. Dobbeltklik på ikonet for at åbne programmet.

**Første Gang I Programmet**

1. Programmet forsøger automatisk at finde:

```text
Documents\AgOpenGPS\Fields
```

2. Hvis dine marker ikke vises, tryk:

```text
Vælg Fields-mappe
```

3. Vælg din AgOpenGPS `Fields`-mappe.

4. Vælg en mark i listen.

5. Vælg antal zoner.

6. Vælg pæleafstand.

7. Tryk:

```text
Vælg A/B
```

8. Klik A og B på kortet.

9. Flyt A/B-punkterne indtil hegnene ligger rigtigt.

10. Tryk:

```text
Start mobilguide
```

11. Scan QR-koden med mobilen.

12. Tryk `GPS` på mobilen og tillad placering.

**Hvis Setup Ikke Virker**

Download i stedet:

```text
AgOpenGPS_FencePlanner_package.zip
Installer_fra_lokal_pakke.bat
```

Læg dem i samme mappe og kør:

```text
Installer_fra_lokal_pakke.bat
```

Så installeres programmet fra den downloadede zip-fil.
