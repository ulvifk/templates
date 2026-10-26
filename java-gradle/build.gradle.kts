plugins {
    id("java")
    id("application")
    id("com.diffplug.spotless") version "8.10.4"
    id("io.freefair.lombok") version "9.8.2"
    id("com.github.spotbugs") version "6.5.13"
}

java {
    toolchain {
        languageVersion.set(JavaLanguageVersion.of(27))
    }
}

application {
    mainClass = "template.Main"
    applicationDefaultJvmArgs = listOf("--enable-native-access=ALL-UNNAMED")
}

repositories {
    mavenCentral()
}

dependencies {
    implementation("com.fasterxml.jackson.core:jackson-databind:2.22.3")
    implementation("org.slf4j:slf4j-api:2.0.20")
    runtimeOnly("org.slf4j:slf4j-simple:2.0.20")

    implementation("com.gurobi:gurobi:13.0.3")

    testImplementation(platform("org.junit:junit-bom:6.1.3"))
    testImplementation("org.junit.jupiter:junit-jupiter")
    testRuntimeOnly("org.junit.platform:junit-platform-launcher")
}

spotless {
    java {
        palantirJavaFormat()
    }
}

spotbugs {
    excludeFilter.set(file("config/spotbugs/exclusions.xml"))
}

tasks.withType<JavaCompile>().configureEach {
    options.isFork = true
    options.forkOptions.jvmArgs = listOf("--sun-misc-unsafe-memory-access=allow")
}

tasks.test {
    useJUnitPlatform()
    jvmArgs("--enable-native-access=ALL-UNNAMED")
}

tasks.compileJava {
    mustRunAfter("spotlessApply")
}

tasks.register("formatAndCheck") {
    group = "verification"
    description = "Formats source files, then runs all checks."
    dependsOn("spotlessApply", "check")
}
