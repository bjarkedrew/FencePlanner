# AgOpenGPS Fence Planner

AgOpenGPS Fence Planner er et Windows-program til at planlaegge midlertidige hegn, folde og zoner ud fra AgOpenGPS- og AgShare-markfiler.

Programmet er lavet til praktisk markarbejde: lav planen paa computeren med satellitkort og markfiler, gem hegnslinjerne, og brug derefter KOR-fanen eller mobilen som guide ude i marken.

Aktuel programversion: `v1.0.18`

## Kort Fortalt

- Finder automatisk `Documents\AgOpenGPS\Fields`
- Importerer AgShare/TASKDATA ZIP-filer
- Viser marker paa satellitkort, naar der findes georeference
- Deler marker op i lige store zoner/folde
- Kan lave parallelle hegn eller vifte-hegn mellem to yderlinjer
- Kan lave kurve-linjer ud fra A/B-punkter paa markgransen
- Viser paelepunkter og samlet antal paele
- Gemmer hegnsplaner, saa de kan indlaeses igen senere
- Skriver `TrackLines.txt`, saa linjer kan bruges i AgOpenGPS
- Har KOR-fane til GPS/simpleRTK2B via NMEA/COM-port
- Har NTRIP/RTK-felter til simpleRTK-korrektioner paa KOR-fanen
- Kan lave midlertidigt HTTPS-link og QR-kode til den aktuelle mark
- Har automatisk opdateringsknap under fanen `Program`
- Tjekker automatisk ved opstart om en ny GitHub release er tilgaengelig

## Markfiler

Programmet kigger som standard efter AgOpenGPS-marker her:

```text
Documents\AgOpenGPS\Fields
```

Importerede AgShare/TASKDATA-marker gemmes separat her:

```text
Documents\FencePlanner\Fields
```

Fence Planner kan bruge georeference fra:

- `Field.kml`
- `zISOXML\v3/v4\TASKDATA.XML`
- AgShare `geojson/fields.geojson`

Det betyder, at satellitkort og mobil GPS stadig kan bruges, selv om en downloadet mark ikke har `Field.kml`, hvis AgShare/TASKDATA indeholder geodata.

## Saadan Bruger Man Det

1. Aabn `AgOpenGPS Fence Planner`.
2. Vaelg en mark fra listen, eller importer en AgShare/TASKDATA ZIP.
3. Vaelg antal zoner og paeleafstand.
4. Vaelg almindelig parallel plan med `Vaelg A/B`, eller tryk `Vifte`.
5. Flyt punkterne paa kortet, indtil hegnene ligger rigtigt.
6. Tryk `Gem hegnsplan`, hvis planen skal gemmes til senere.
7. Tryk `Koer mark` for at gaa direkte til KOR-fanen.
8. Tryk `Mobil QR`, hvis planen skal bruges paa mobil.

## Parallelle Zoner

Tryk `Vaelg A/B` og klik to punkter paa kortet.

A/B-linjen bestemmer retningen, og programmet laver de noedvendige hegnslinjer, saa zonerne bliver lige store i hektar.

Eksempel:

- 3 zoner giver 2 hegn
- 5 zoner giver 4 hegn

## Vifte-Zoner

Tryk `Vifte` og klik fire punkter:

```text
A1 -> B1 -> A2 -> B2
```

`A1-B1` og `A2-B2` er de to yderlinjer. Programmet fordeler hegnslinjerne mellem dem efter det valgte antal zoner.

Vifte bruger linjerne som yderlinjer, saa det er ligegyldigt om en linje er klikket A til B eller B til A. Det er kun placeringen af de to linjer, der bestemmer omraadet mellem dem.

## Paele

Paeleafstand kan vaelges som:

- `10 m`
- `25 m`
- `50 m`
- eller en selvvalgt afstand skrevet direkte i feltet

Programmet viser antal paele pr. hegnslinje og samlet antal paele.

## KOR-Fanen

KOR-fanen bruges som guide ved opmaerkning.

Den kan:

- vise valgt hegnslinje
- skifte mellem hegnslinjer
- vise linjelaengde og paele
- laese GPS fra NMEA/COM-port
- vise afstand til valgt hegnslinje

simpleRTK2B kan bruges, hvis den sender NMEA via COM-port. Centimeterpraecision kraever normalt RTK-korrektioner.

## Mobil QR

Mobil QR laver et midlertidigt HTTPS-link med den mark og hegnsplan, der er aaben i programmet lige nu.

Arbejdsgang:

1. Lav eller indlaes en hegnsplan.
2. Tryk `Mobil QR`.
3. Scan QR-koden paa mobilen.
4. Vaelg hegnslinje paa mobilen.
5. Brug mobilens GPS som guide.

Programmet uploader ikke marken til GitHub og laver ikke en online sync-mappe. Desktop-programmet skal vaere aabent, mens mobilen bruger QR-linket.

## Installation

Fra GitHub Release skal man normalt kun downloade:

```text
FencePlanner_Installer.bat
```

Koer filen. Den henter selv nyeste programpakke og installerer programmet.

Efter installation ligger programmet paa skrivebordet som:

```text
AgOpenGPS Fence Planner
```

Windows kan advare om ukendt program. Vaelg i saa fald `Flere oplysninger` og derefter `Koer alligevel`.

## Opdatering

Under fanen `Program` findes knappen:

```text
Hent/opdater nyeste version
```

Den henter nyeste GitHub Release, lukker programmet under installationen og opdaterer skrivebordsikonet automatisk.

## Offline/Lokal Installation

Hvis den lille installer ikke virker, kan man hente:

```text
AgOpenGPS_FencePlanner_package.zip
Installer_fra_lokal_pakke.bat
```

Laeg dem i samme mappe og koer `Installer_fra_lokal_pakke.bat`.
