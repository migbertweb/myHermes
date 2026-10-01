# Cambiar versión de un APK (Android TV)

## Caso real: Xuper 5.1.4 → 5.1.5

### Estado inicial

- APK: `Xuper 5.1.4.apk` (34 MB)
- `versionCode: 50104`
- `versionName: 5.1.4`
- Package: `com.android.mgstv`
- Paquete original con proteccion Ijiami (ijiami.ajm, ijiami.dat)

### Herramientas instaladas

```bash
# From chaotic-aur
sudo pacman -S chaotic-aur/android-apktool
sudo pacman -S chaotic-aur/android-sdk-build-tools
```

### Proceso

```bash
# 1. Descompilar (8 threads automáticos)
apktool d -f "Xuper 5.1.4.apk" -o xuper_decoded

# 2. Editar version en apktool.yml
# versionCode: 50104 → 50105
# versionName: 5.1.4 → 5.1.5

# 3. Recompilar
apktool b xuper_decoded -o xuper_5.1.5_unsigned.apk

# 4. Crear debug keystore (solo la primera vez)
keytool -genkey -v -keystore debug.keystore -alias debug \
  -keyalg RSA -keysize 2048 -validity 10000 \
  -dname "CN=Debug, OU=Debug, O=Debug, L=, S=, C=US" \
  -storepass android -keypass android

# 5. Firmar
jarsigner -verbose -keystore debug.keystore \
  -storepass android -keypass android \
  xuper_5.1.5_unsigned.apk debug

# 6. Alinear y generar APK final
zipalign -v 4 xuper_5.1.5_unsigned.apk Xuper_5.1.5.apk
```

### Resultado

- APK firmado: 35 MB
- Firma: debug (self-signed — normal para APK modificados)
- `versionCode`: 50105
- `versionName`: 5.1.5

### Nota sobre AndroidManifest.xml

El `AndroidManifest.xml` NO tenía `versionName`/`versionCode` porque las apps modernas los definen en `build.gradle`. `apktool` los extrae a `apktool.yml` automáticamente.
