pluginManagement {
    val flutterSdkPath = run {
        val properties = java.util.Properties()
        val archivo = file("local.properties")
        require(archivo.exists()) { "falta local.properties" }
        archivo.inputStream().use { properties.load(it) }
        val ruta = properties.getProperty("flutter.sdk")
        require(ruta != null) { "flutter.sdk not set in local.properties" }
        // Gradle 9 rechaza rutas con barras invertidas mezcladas.
        ruta.replace("\\", "/")
    }

    includeBuild("$flutterSdkPath/packages/flutter_tools/gradle")

    repositories {
        google()
        mavenCentral()
        gradlePluginPortal()
    }
}

plugins {
    id("dev.flutter.flutter-plugin-loader") version "1.0.0"
    id("com.android.application") version "9.3.1" apply false
    id("org.jetbrains.kotlin.android") version "2.4.20" apply false
}

include(":app")
