# AgOpenGPS Fence Planner - GitHub upload

Upload filerne i denne mappe til en GitHub Release.

## Filer

- `AgOpenGPS_FencePlanner_package.zip`
  - Selve programpakken.
  - Indeholder Windows EXE, ikon, portable Node/npm til mobilguidens HTTPS-link og release-installer.

- `FencePlanner_Installer.bat`
  - Anbefalet installer til brugeren.
  - En enkelt fil, som selv downloader nyeste release-pakke og installerer programmet.

- `Installer_fra_lokal_pakke.bat`
  - Kun til lokal test.
  - Installerer fra zippen, hvis zippen ligger i samme mappe.

## GitHub release workflow

1. Opret en ny Release på GitHub.
2. Upload `AgOpenGPS_FencePlanner_package.zip`.
3. Upload `FencePlanner_Installer.bat`.
4. Upload `Installer_fra_lokal_pakke.bat`, hvis lokal offline-installation skal tilbydes.

Brugeren skal derefter kun downloade `FencePlanner_Installer.bat` og køre den.
