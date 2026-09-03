# Tiflogram Android Build and Patch Workflows

This repository contains the scripts, assets, and GitHub Actions workflows used to build a patched Tiflogram APK from a fresh checkout of [DrKLO/Telegram](https://github.com/DrKLO/Telegram). The Telegram source tree is intentionally not bundled here; the build workflow clones it at runtime, runs a preflight check, applies the patches, builds the release APK, and publishes the artifact.

## Workflows

| Workflow | Purpose | Trigger |
|---|---|---|
| `build-apk.yml` | Clone Telegram, apply all source patches and assets, build, align, sign, and publish an APK | Manual dispatch or changes to scripts/assets/workflow |
| `patch-apk.yml` | Patch the account-limit smali code in an existing release APK and publish a re-signed APK | Manual dispatch |
| `fork-and-setup.yml` | Create a fork of DrKLO/Telegram and install this repository’s scripts, assets, and workflows | Manual dispatch |
| `sync-from-zip.yml` | Replace repository contents with the contents of a root-level ZIP archive | Manual dispatch or a root-level ZIP push |

## Required GitHub Secrets

The build and APK-patching workflows do not store signing material in Git. Configure these repository or organization secrets before running either workflow:

| Secret | Value |
|---|---|
| `TIFLOGRAM_KEYSTORE_BASE64` | Base64-encoded contents of the release keystore |
| `TIFLOGRAM_KEYSTORE_PASSWORD` | Keystore and `tiflogram` alias password |
| `FORK_TOKEN` | A GitHub token with permission to create and push to the requested fork; required only by `fork-and-setup.yml` |

To encode a keystore locally, use `base64 -w 0 release.keystore` and paste the result into `TIFLOGRAM_KEYSTORE_BASE64`. Keep the original keystore and password in a secure password manager. Do not commit either file.

> **Important:** Android updates require the same signing key as the installed application. If the original key has been exposed or lost, an APK signed with a newly generated key will not update an existing installation; it must be treated as a separate application or installed after removing the old application.

## Local validation

From the repository root, run:

```bash
python3 -m compileall -q scripts
python3 scripts/run_all_checks.py
```

The aggregate patch check requires a compatible Telegram source checkout. Set `TELEGRAM_SRC` to that checkout when it is not the current working directory.

## Repository security

Signing files, Android build output, Gradle state, and local Telegram checkouts are excluded by `.gitignore`. The ZIP synchronization workflow explicitly removes any signing files that might be present in an uploaded archive. If a previous version of this repository was public and contained a real signing key, rotate the key and consider the old APK signature compromised.

## Current feature assets

The patch set includes accessibility changes, branding, sponsored-message removal, Gemini safety scanning, free translation paths, automatic translation settings, custom chat/download sounds, and account-limit smali patching. The exact patch compatibility is checked against the Telegram source revision cloned by the workflow before any modifications are applied.

## Reliability fixes for download feedback

`fix_reliable_feedback.py` runs immediately after `fix_accessibility.py`. It removes the old `RadialProgress2`-parent focus test and stores progress in `ChatMessageCell`, whose virtual accessibility host is the node TalkBack actually reads. This makes the leading percentage available for documents, photos, videos, audio, GIFs, and other attachments that register a message download observer. Announcements are throttled to one event per changed percentage and are emitted only between 1% and 99% to avoid completion chatter.

`fix_download.py` now handles the shared `fileLoaded`/`httpFileDidLoad` completion point without scanning transient `downloadingFiles` lists or requiring a `Document`. That covers photo and HTTP media downloads as well as ordinary files. A short per-filename debounce prevents duplicate sound playback when both notification variants describe the same completion.

The translation controller now routes both its forced alternative branch and its server-disabled fallback through the bundled `TiflogramTranslate` helper. This removes the previous split behavior where only one controller branch used the custom translator. It still depends on the public Google Translate endpoint, so network availability and endpoint policy can affect translation results.
