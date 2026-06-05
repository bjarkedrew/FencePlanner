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
