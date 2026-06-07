# Fence Guide Android

Mobilapp til Fence Planner. Appen importerer den `*_FenceGuide.html`, som Windows-programmet eksporterer, og bruger telefonens GPS til at vise afstand til valgt hegnslinje.

## Nemmeste test

1. Installer Node.js LTS og Android Studio:

   ```bat
   install_prerequisites_windows.bat
   ```

2. Installer `Expo Go` på telefonen fra Google Play.

3. Start dev-serveren:

   ```bat
   start_dev.bat
   ```

4. Scan QR-koden med Expo Go.

5. I appen: tryk `Importér` og vælg den `*_FenceGuide.html`, som Windows-programmet har lavet.

## Byg APK

Når appen virker i Expo Go:

```bat
build_apk_eas.bat
```

Første gang beder Expo om login. Preview-profilen bygger en APK.

## Funktioner

- Importerer `*_FenceGuide.html`
- Viser satellitkort
- Viser markgrænse, hegn og pælepunkter
- Bruger telefonens GPS
- Viser afstand til valgt hegnslinje
- Viser venstre/højre side

## Status

Dette er første rigtige app-version. Den er klar til test, men APK-build kræver Node/Expo og enten Expo cloud-build eller lokal Android SDK.
