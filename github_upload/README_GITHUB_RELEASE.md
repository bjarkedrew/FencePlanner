# AgOpenGPS Fence Planner - GitHub upload

Upload filerne i denne mappe til en GitHub Release.

## Filer

- `AgOpenGPS_FencePlanner_package.zip`
  - Selve programpakken.
  - Indeholder Windows EXE, ikon, portable Node/npm til mobilguidens HTTPS-link og release-installer.

- `FencePlanner_Setup.ps1`
  - Lille download-installer.
  - Kan hente zip-pakken fra en URL og installere programmet.

- `FencePlanner_Setup.bat`
  - Dobbeltklik-venlig wrapper til `FencePlanner_Setup.ps1`.
  - Rediger linjen `set "PACKAGE_URL=..."` så den peger på GitHub release-linket til zip-filen.

- `FencePlanner_Online_Installer.bat`
  - Anbefalet installer til brugeren.
  - En enkelt fil, som selv downloader nyeste release-pakke og installerer programmet.

- `Installer_fra_lokal_pakke.bat`
  - Kun til lokal test.
  - Installerer fra zippen, hvis zippen ligger i samme mappe.

## GitHub release workflow

1. Opret en ny Release på GitHub.
2. Upload `AgOpenGPS_FencePlanner_package.zip`.
3. Kopier download-linket til zip-filen.
4. Sæt linket ind i `FencePlanner_Setup.bat` på linjen:

   ```bat
   set "PACKAGE_URL=DIT_DOWNLOAD_LINK_HER"
   ```

5. Upload også `FencePlanner_Online_Installer.bat`, `FencePlanner_Setup.bat` og `FencePlanner_Setup.ps1`.

Brugeren skal derefter kun downloade `FencePlanner_Online_Installer.bat` og køre den.
