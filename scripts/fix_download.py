#!/usr/bin/env python3
"""Tiflogram download completion feedback.

The upstream controller emits both fileLoaded and httpFileDidLoad for
successful downloads.  The patch deliberately does not infer user intent from
transient downloadingFiles lists or from document-only metadata: those lists
are updated around the same callback and photos use PhotoSize rather than a
Document.  A short filename debounce prevents duplicate sounds if both event
variants are delivered for one completion.
"""

import sys

MODE = sys.argv[1] if len(sys.argv) > 1 else "check"

FIXES = [
    {
        "id": "10a",
        "label": "DownloadController: completion-sound debounce state",
        "path": "TMessagesProj/src/main/java/org/telegram/messenger/DownloadController.java",
        "old": "    private LongSparseArray<Long> typingTimes = new LongSparseArray<>();",
        "new": "    private LongSparseArray<Long> typingTimes = new LongSparseArray<>();\n\n    // Tiflogram: fileLoaded/httpFileDidLoad may describe the same completion.\n    private final HashMap<String, Long> tiflogramLastCompletionSound = new HashMap<>();",
    },
    {
        "id": "10b",
        "label": "DownloadController: all file types -> completion sound",
        "path": "TMessagesProj/src/main/java/org/telegram/messenger/DownloadController.java",
        "old": '''        } else if (id == NotificationCenter.fileLoaded || id == NotificationCenter.httpFileDidLoad) {
            listenerInProgress = true;
            String fileName = (String) args[0];''',
        "new": '''        } else if (id == NotificationCenter.fileLoaded || id == NotificationCenter.httpFileDidLoad) {
            listenerInProgress = true;
            String fileName = (String) args[0];
            // Tiflogram: do not inspect downloadingFiles/recentDownloadingFiles.
            // Those lists change during this callback, and photos/HTTP media do
            // not necessarily have a Document entry.  This is the common
            // successful-completion point for documents, photos, videos,
            // audio, stickers, and HTTP downloads.
            if (fileName != null) {
                long now = System.currentTimeMillis();
                Long previous = tiflogramLastCompletionSound.get(fileName);
                if (previous == null || now - previous > 1500L) {
                    tiflogramLastCompletionSound.put(fileName, now);
                    try {
                        android.media.MediaPlayer mp = android.media.MediaPlayer.create(
                                ApplicationLoader.applicationContext,
                                org.telegram.messenger.R.raw.tiflogram_dl_done);
                        if (mp != null) {
                            mp.setOnCompletionListener(android.media.MediaPlayer::release);
                            mp.start();
                        }
                    } catch (Throwable ignore) {
                    }
                }
            }''',
    },
]


def main():
    if MODE not in ("check", "apply"):
        print(f"Unknown mode: {MODE}")
        sys.exit(1)

    results = []
    cache = {}
    for fix in FIXES:
        path = fix["path"]
        if path not in cache:
            try:
                cache[path] = open(path, encoding="utf-8").read()
            except FileNotFoundError:
                cache[path] = None
        content = cache[path]
        ok = content is not None and fix["old"] in content
        results.append(ok)
        print(("OK" if ok else "FAIL") + f" [{fix['id']}] {fix['label']}")

    if not all(results):
        sys.exit(1)
    if MODE == "check":
        return

    modified = dict(cache)
    for fix in FIXES:
        path = fix["path"]
        modified[path] = modified[path].replace(fix["old"], fix["new"], 1)
    for path, content in modified.items():
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(content)
        print(f"Wrote {path}")


if __name__ == "__main__":
    main()
