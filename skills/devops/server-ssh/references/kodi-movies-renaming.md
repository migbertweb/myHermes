# Renombrado de películas a convención KODI (serverhogar)

## Convención

- Carpeta por película: `Título (Año)/`
- Archivo dentro de la carpeta: `Título (Año).ext`
  - Ejemplo: `Perfume de Mujer (1992)/Perfume de Mujer (1992).mp4`
  - Ejemplo: `Esencia de mujer (1992)/Esencia de mujer (1992).mkv`

El año es el de estreno de la película según TMDB. Usar el título en español latino cuando exista; si el archivo original está en inglés, mantener consistencia con el nombre de carpeta.

## Procedimiento de copia con renombrado

1. Determinar año y título canónico (web_search si no está seguro).
2. Crear carpeta destino en el servidor:
   ```bash
   ssh serverhogar "mkdir -p '/home/piro/multimedia/movies/Título (Año)'"
   ```
3. Transferir con rsync renombrando:
   ```bash
   rsync -av --progress "/ruta/local/ArchivoOriginal.ext" "serverhogar:/home/piro/multimedia/movies/Título (Año)/Título (Año).ext"
   ```
4. Verificar:
   ```bash
   ssh serverhogar "ls -lh '/home/piro/multimedia/movies/Título (Año)/'"
   ```

## Pitfalls

- No usar `~/movies/` — la carpeta correcta es `~/multimedia/movies/`.
- Paréntesis en nombres de ruta: siempre entrecomillar la ruta completa en SSH/rsync para evitar expansión de shell.
- No fabricar el año: verificar con TMDB/Wikipedia antes de crear la carpeta.
- Mantener la extensión real del contenedor; no cambiar .mp4 a .mkv.
- Transferencias interrumpidas con rsync en background dejan archivos temporales ocultos `.Nombre.ext.<rand>`; confirmar finalización con `ls -lh` y tamaño esperado; volver a lanzar rsync para completar.
- Para copias masivas, verificar que la carpeta destino no existe ya antes de crearla y evitar duplicados.

## Regla de oro: inspeccionar antes de nombrar

Probar resolución y audio antes de la transferencia:
```bash
ffprobe -v error -select_streams v:0 -show_entries stream=width,height,codec_name -of default=noprint_wrappers=1:nokey=0 "archivo.mp4"
ffprobe -v error -select_streams a -show_entries stream=index,codec_name,tags=language -of default=noprint_wrappers=1 "archivo.mp4"
```
