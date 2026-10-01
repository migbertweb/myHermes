# Kodi Naming Conventions

## Movies
- Carpeta: `/home/piro/multimedia/movies/Título (Año)/`
- Archivo: `Título (Año).mkv`
- Ejemplo: `/home/piro/multimedia/movies/Moana (2026)/Moana (2026).mkv`

## Series
- Carpeta serie: `/home/piro/multimedia/series/Título (Año)/` (título limpio en español + año)
- Archivo episodio: `Título (Año) - S01E0X - [Calidad] [Audio].mkv`
- Ejemplo: `/home/piro/multimedia/series/Stuart no logra salvar el universo (2026)/Stuart no logra salvar el universo (2026) - S01E08 - 1080p WEB-DL Dual-Lat.mkv`

## Workflow after torrent completion
1. Esperar a que el torrent alcance 100% y estado `Seeding` o `Done`.
2. Identificar la carpeta raíz del torrent (usualmente bajo `/home/piro/multimedia/movies/` o `/home/piro/multimedia/series/` con nombre de release).
3. Para películas:
   ```bash
   mkdir -p "/home/piro/multimedia/movies/Título (Año)"
   mv "/home/piro/multimedia/movies/ReleaseName/ReleaseName.mkv" "/home/piro/multimedia/movies/Título (Año)/Título (Año).mkv"
   rmdir "/home/piro/multimedia/movies/ReleaseName"  # solo si está vacía
   ```
4. Para series:
   ```bash
   # 1. Mapear estructura real (los torrents pueden crear carpetas duplicadas con/sin año)
   ssh serverhogar 'find /home/piro/multimedia/series/ -maxdepth 3 -iname "*<serie>*" -exec ls -lh {} \;'
   
   # 2. Mover el archivo .mkv a la carpeta serie CON AÑO y renombrar
   mkdir -p "/home/piro/multimedia/series/Título (Año)"
   mv "/home/piro/multimedia/series/ReleaseName/ReleaseName.mkv" "/home/piro/multimedia/series/Título (Año)/Título (Año) - S01E0X - 1080p WEB-DL Dual-Lat.mkv"
   
   # 3. Si existe carpeta duplicada SIN año, consolidar episodios ahí también
   mv "/home/piro/multimedia/series/Título sin año/*" "/home/piro/multimedia/series/Título (Año)/"
   rmdir "/home/piro/multimedia/series/Título sin año"
   
   # 4. Limpiar carpeta temporal del release
   rmdir "/home/piro/multimedia/series/ReleaseName"  # solo si está vacía
   ```
5. Verificar que el archivo existe y es reproducible con `ffprobe`.

## Notas
- La carpeta serie DEBE incluir el año `(Año)` para coincidir con la convención del mediacenter (ver `references/mediacenter-naming.md`).
- Los marcadores `S01E0X` son esenciales para el scraper de Kodi.
- Mantener el idioma en el nombre del archivo: `Dual-Lat` para audio dual latino, `Latino` para solo latino, etc.
- Consolidar carpetas duplicadas (con/sin año) ANTES de borrar la carpeta temporal del release.
