# Sådan opretter du GitHub Release

## 1. Gå til dit GitHub repository

Åbn repoet i browseren.

## 2. Opret ny release

Klik:

```text
Releases -> Draft a new release
```

## 3. Udfyld release

Brug:

```text
Tag version: v1.0.0
Release title: AgOpenGPS Fence Planner v1.0.0
```

Kopier teksten fra `RELEASE_NOTES.md` ind i beskrivelsen.

## 4. Upload filer

Upload disse filer som release assets:

```text
AgOpenGPS_FencePlanner_package.zip
FencePlanner_Setup.ps1
FencePlanner_Setup.bat
Installer_fra_lokal_pakke.bat
```

## 5. Ret setup-link

Efter zippen er uploadet, får den et download-link i dette format:

```text
https://github.com/DIT_NAVN/DIT_REPO/releases/download/v1.0.0/AgOpenGPS_FencePlanner_package.zip
```

Åbn `FencePlanner_Setup.bat` og ret linjen:

```bat
set "PACKAGE_URL="
```

til:

```bat
set "PACKAGE_URL=https://github.com/DIT_NAVN/DIT_REPO/releases/download/v1.0.0/AgOpenGPS_FencePlanner_package.zip"
```

Upload derefter den rettede `FencePlanner_Setup.bat` igen til releasen.

## 6. Publicer

Klik:

```text
Publish release
```

Brugeren skal normalt kun downloade:

```text
FencePlanner_Setup.bat
FencePlanner_Setup.ps1
```
