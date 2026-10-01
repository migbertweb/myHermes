# Descripciones OWM en español (lang=es)

Lista completa de las 55 descripciones que OpenWeatherMap puede devolver
para el parámetro `lang=es`. Verificadas contra la API 2.5.
Usan solo ASCII (sin acentos).

## Grupo 2xx: Tormentas (10)
| Código | Descripción | Chars |
|--------|-------------|-------|
| 200 | tormenta electrica con lluvia ligera | 36 |
| 201 | tormenta electrica con lluvia | 28 |
| 202 | tormenta electrica con lluvia intensa | 37 |
| 210 | tormenta electrica ligera | 24 |
| 211 | tormenta electrica | 18 |
| 212 | tormenta electrica intensa | 25 |
| 221 | tormenta electrica irregular | 27 |
| 230 | tormenta electrica con llovizna ligera | 38 |
| 231 | tormenta electrica con llovizna | 30 |
| 232 | tormenta electrica con llovizna intensa | **39** ← más larga |

## Grupo 3xx: Llovizna (7)
| Código | Descripción | Chars |
|--------|-------------|-------|
| 300/310 | llovizna de intensidad ligera | 29 |
| 301/311 | llovizna | 8 |
| 302/312 | llovizna de intensidad intensa | 30 |
| 313 | chubascos de lluvia y llovizna | 29 |
| 314 | chubascos de lluvia y llovizna intensa | 38 |
| 321 | chubascos de llovizna | 20 |

## Grupo 5xx: Lluvia (10)
| Código | Descripción | Chars |
|--------|-------------|-------|
| 500 | lluvia ligera | 12 |
| 501 | lluvia moderada | 14 |
| 502 | lluvia intensa | 13 |
| 503 | lluvia muy intensa | 17 |
| 504 | lluvia extrema | 13 |
| 511 | lluvia helada | 12 |
| 520 | lluvia intensa de corta duracion | **31** |
| 521 | chubascos de lluvia | 18 |
| 522 | chubascos de lluvia intensa | 26 |
| 531 | chubascos de lluvia irregular | 28 |

## Grupo 6xx: Nieve (11)
| Código | Descripción | Chars |
|--------|-------------|-------|
| 600 | nevada ligera | 12 |
| 601 | nieve | 5 |
| 602 | nevada intensa | 14 |
| 611 | aguanieve | 9 |
| 612 | aguanieve ligera | 15 |
| 613 | aguanieve intensa | 16 |
| 615/616 | lluvia y nieve | 13 |
| 620 | nevada ligera de corta duracion | **29** |
| 621 | chubascos de nieve | 17 |
| 622 | chubascos de nieve intensa | 25 |

## Grupo 7xx: Atmósfera (9)
| Código | Descripción | Chars |
|--------|-------------|-------|
| 701/741 | niebla | 6 |
| 711 | humo | 4 |
| 721 | calina | 6 |
| 731 | polvo en suspension | 18 |
| 751 | arena | 5 |
| 761 | polvo | 5 |
| 762 | ceniza volcanica | 15 |
| 771 | turbonada | 9 |
| 781 | tornado | 7 |

## Grupo 8xx: Nubes (5)
| Código | Descripción | Chars |
|--------|-------------|-------|
| 800 | cielo claro | 11 |
| 801 | algo de nubes | 13 |
| 802 | nubes dispersas | 15 |
| 803 | muy nuboso | 10 |
| 804 | nubes | 5 |

## Notas de diseño para DeskMate

Fuente 8x13 en display 240x240:

| Escala | Ancho/char | Max chars | Uso |
|--------|------------|-----------|-----|
| scale 2 | 18px | 13 | Línea de temperatura |
| scale 1 | 9px | 26 | Línea de sensación |

**Problema**: Con formato `"{temp}C {desc}"` a scale 2:
- Con "5C ": queda espacio para 10 chars de descripción
- Con "20C ": queda espacio para 9 chars
- Con "-15C ": queda espacio para 8 chars

De 55 descripciones, solo ~11 caben completas con prefijo "-15C " (~20%).
Ver `scripts/check_fit.py` para test interactivo.
