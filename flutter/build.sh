#!/usr/bin/env bash
# Build the Schedule Manager Flutter app. Finished files are copied to dist/.
#
#   ./build.sh apk        Android, one universal APK (all phone CPUs, ~55 MB)
#   ./build.sh apk-split  Android, one APK per CPU type (~18 MB; phones: arm64-v8a)
#   ./build.sh ios        iPhone .ipa            (macOS + Xcode + Apple signing)
#   ./build.sh macos      macOS .app, zipped     (macOS + Xcode)
#   ./build.sh linux      Linux desktop, .tar.gz (Linux)
#   ./build.sh web        static web build, .tar.gz
#   ./build.sh all        everything this OS can build
#
# Environment:
#   API_URL       backend URL baked into the app (default: the Google Cloud VM)
#   BUILD_NAME    version shown to users   (default: from pubspec.yaml, e.g. 1.0.0)
#   BUILD_NUMBER  integer build number     (default: from pubspec.yaml, e.g. 1)
#                 Android/iOS only install an update if BUILD_NUMBER is higher.

set -euo pipefail
cd "$(dirname "$0")"

API_URL="${API_URL:-http://35.207.134.118:8000}"
PUBSPEC_VERSION="$(sed -n 's/^version: *//p' pubspec.yaml)"
BUILD_NAME="${BUILD_NAME:-${PUBSPEC_VERSION%%+*}}"
BUILD_NUMBER="${BUILD_NUMBER:-${PUBSPEC_VERSION##*+}}"
DIST="dist"
APP="schedule-manager-${BUILD_NAME}"
OS="$(uname -s)"

FLUTTER_ARGS=(--release --build-name="$BUILD_NAME" --build-number="$BUILD_NUMBER"
              --dart-define=API_URL="$API_URL")

log() { printf '\n\033[1;34m==> %s\033[0m\n' "$*"; }
die() { printf '\033[1;31mError:\033[0m %s\n' "$*" >&2; exit 1; }

require_os() {
  [[ "$OS" == "$1" ]] || die "$2 can only be built on $3 (this is $OS)."
}

require_xcode() {
  require_os Darwin "$1" macOS
  command -v xcodebuild >/dev/null && xcodebuild -version >/dev/null 2>&1 \
    || die "Xcode is required: install it from the App Store, then run: sudo xcode-select -s /Applications/Xcode.app && sudo xcodebuild -runFirstLaunch"
  command -v pod >/dev/null || die "CocoaPods is required: brew install cocoapods"
}

check_jdk() {
  # Android builds need a full JDK (with javac); a JRE alone fails in Gradle.
  local java_bin
  java_bin="$(flutter doctor -v 2>/dev/null | sed -n 's/.*Java binary at: *//p' | head -1)"
  if [[ -n "$java_bin" && ! -x "$(dirname "$java_bin")/javac" ]]; then
    die "Flutter uses $java_bin, which has no javac (JRE only). Point Flutter at a full JDK 17/21: flutter config --jdk-dir <path-to-jdk>"
  fi
}

build_apk() {
  check_jdk
  log "Android APK (universal) → $API_URL"
  flutter build apk "${FLUTTER_ARGS[@]}"
  cp build/app/outputs/flutter-apk/app-release.apk "$DIST/$APP.apk"
}

build_apk_split() {
  check_jdk
  log "Android APK per CPU type → $API_URL"
  flutter build apk --split-per-abi "${FLUTTER_ARGS[@]}"
  for abi in arm64-v8a armeabi-v7a x86_64; do
    cp "build/app/outputs/flutter-apk/app-$abi-release.apk" "$DIST/$APP-$abi.apk"
  done
}

build_ios() {
  require_xcode "iOS"
  log "iOS .ipa → $API_URL"
  flutter build ipa "${FLUTTER_ARGS[@]}" || die "iOS build failed. If it's about signing: open ios/Runner.xcworkspace in Xcode → Runner → Signing & Capabilities → pick your Team, then run again."
  cp build/ios/ipa/*.ipa "$DIST/$APP-ios.ipa"
}

build_macos() {
  require_xcode "macOS"
  log "macOS app → $API_URL"
  flutter build macos "${FLUTTER_ARGS[@]}"
  local app
  app="$(find build/macos/Build/Products/Release -maxdepth 1 -name '*.app' | head -1)"
  ditto -c -k --keepParent "$app" "$DIST/$APP-macos.zip"
}

build_linux() {
  require_os Linux "The Linux desktop app" Linux
  log "Linux desktop → $API_URL"
  flutter build linux "${FLUTTER_ARGS[@]}"
  tar -czf "$DIST/$APP-linux-x64.tar.gz" -C build/linux/x64/release bundle
}

build_web() {
  log "Web → $API_URL"
  flutter build web "${FLUTTER_ARGS[@]}"
  tar -czf "$DIST/$APP-web.tar.gz" -C build/web .
}

target="${1:-}"
case "$target" in
  apk|apk-split|ios|macos|linux|web|all) ;;
  *) sed -n '2,17s/^# \{0,1\}//p' "$0"; exit 1 ;;
esac

mkdir -p "$DIST"
flutter pub get >/dev/null

case "$target" in
  apk)       build_apk ;;
  apk-split) build_apk_split ;;
  ios)       build_ios ;;
  macos)     build_macos ;;
  linux)     build_linux ;;
  web)       build_web ;;
  all)
    if [[ "$OS" == Darwin ]]; then
      build_ios; build_macos; build_web
    else
      build_apk; build_apk_split; build_linux; build_web
    fi
    ;;
esac

log "Done: version $BUILD_NAME ($BUILD_NUMBER), backend $API_URL"
ls -lh "$DIST"
