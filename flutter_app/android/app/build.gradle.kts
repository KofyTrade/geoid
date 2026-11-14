import java.util.Properties

plugins {
    id("com.android.application")
    // The Flutter Gradle Plugin must be applied after the Android and Kotlin Gradle plugins.
    id("dev.flutter.flutter-gradle-plugin")
}

// Firma estable: la misma clave que la app Kotlin, para que cualquier APK
// compile donde se compile pueda instalarse encima del anterior.
// En local se lee de keystore.properties; en CI, de variables de entorno.
val firma = Properties().apply {
    val archivo = rootProject.file("keystore.properties")
    if (archivo.exists()) {
        archivo.inputStream().use { load(it) }
    }
}

fun valor(clave: String, entorno: String): String? =
    firma.getProperty(clave) ?: System.getenv(entorno)

val rutaKeystore = valor("storeFile", "KEYSTORE_PATH")
val hayFirma = rutaKeystore != null && file(rutaKeystore).exists()

android {
    namespace = "com.geoid.geoid_vpn"
    compileSdk = flutter.compileSdkVersion
    ndkVersion = flutter.ndkVersion

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

    defaultConfig {
        applicationId = "com.geoid.vpn"
        minSdk = flutter.minSdkVersion
        targetSdk = flutter.targetSdkVersion
        versionCode = flutter.versionCode
        versionName = flutter.versionName
    }

    signingConfigs {
        if (hayFirma) {
            create("geoid") {
                storeFile = file(rutaKeystore!!)
                storePassword = valor("storePassword", "KEYSTORE_PASSWORD")
                keyAlias = valor("keyAlias", "KEY_ALIAS")
                keyPassword = valor("keyPassword", "KEY_PASSWORD")
            }
        }
    }

    buildTypes {
        getByName("debug") {
            if (hayFirma) signingConfig = signingConfigs.getByName("geoid")
        }
        getByName("release") {
            if (hayFirma) signingConfig = signingConfigs.getByName("geoid")
        }
    }
}

kotlin {
    compilerOptions {
        jvmTarget = org.jetbrains.kotlin.gradle.dsl.JvmTarget.JVM_17
    }
}

flutter {
    source = "../.."
}
