# AgOpenGPS Fence Planner - GitHub upload

Upload filerne fra `github_upload` til en GitHub Release.

## Anbefalet fil til brugeren

- `FencePlanner_Installer.bat`
  - Lille installer som henter den nyeste programpakke fra GitHub Release.
  - Brugeren skal normalt kun downloade og koere denne fil.

## Andre filer

- `AgOpenGPS_FencePlanner_package.zip`
  - Selve programpakken med Windows EXE, ikon, portable Node/npm, lokal installer og programfiler.

- `Installer_fra_lokal_pakke.bat`
  - Kun til lokal test, hvis zip-pakken ligger i samme mappe.

## GitHub release workflow

1. Opret en ny Release paa GitHub.
2. Upload `AgOpenGPS_FencePlanner_package.zip`.
3. Upload `FencePlanner_Installer.bat`.
4. Upload eventuelt `Installer_fra_lokal_pakke.bat` til lokal test.

Brugeren skal normalt kun hente `FencePlanner_Installer.bat`.
