import java.util.Properties

plugins {
    alias(libs.plugins.android.application)
}

// Firma de la version release.
// En local se lee de keystore.properties (que no se sube al repositorio);
// en GitHub Actions se pasa por variables de entorno desde los secretos.
val firma = Properties().apply {
    val archivo = rootProject.file("keystore.properties")
    if (archivo.exists()) {
        archivo.inputStream().use { load(it) }
    }
}

fun valor(clave: String, entorno: String): String? =
    firma.getProperty(clave) ?: System.getenv(entorno)

val rutaKeystore = valor("storeFile", "KEYSTORE_PATH")

android {
    namespace = "com.geoid.vpn"
    compileSdk {
        version = release(37)
    }

    defaultConfig {
        applicationId = "com.geoid.vpn"
        minSdk = 24
        targetSdk = 37
        versionCode = 2
        versionName = "1.1"

        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
    }

    signingConfigs {
        if (rutaKeystore != null && file(rutaKeystore).exists()) {
            create("release") {
                storeFile = file(rutaKeystore)
                storePassword = valor("storePassword", "KEYSTORE_PASSWORD")
                keyAlias = valor("keyAlias", "KEY_ALIAS")
                keyPassword = valor("keyPassword", "KEY_PASSWORD")
            }
        }
    }

    buildTypes {
        release {
            optimization {
                enable = true
                packageScope = setOf("androidx.**", "kotlin.**", "kotlinx.**")
            }
            if (rutaKeystore != null && file(rutaKeystore).exists()) {
                signingConfig = signingConfigs.getByName("release")
            }
        }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_11
        targetCompatibility = JavaVersion.VERSION_11
    }
}

dependencies {
    implementation(files("libs/awg.aar"))

    implementation(libs.androidx.activity.ktx)
    implementation(libs.androidx.appcompat)
    implementation(libs.androidx.constraintlayout)
    implementation(libs.androidx.core.ktx)
    implementation(libs.material)
    testImplementation(libs.junit)
    androidTestImplementation(libs.androidx.espresso.core)
    androidTestImplementation(libs.androidx.junit)
}
