#!/usr/bin/env python3
"""Reliability fixes for download progress announcements.

This script runs after fix_accessibility.py.  It deliberately patches the
already-accessibility-patched source so the older renderer-level logic is
removed rather than duplicated.
"""
import sys

MODE = sys.argv[1] if len(sys.argv) > 1 else "check"

FIXES = [
    {
        "id": "progress-renderer-field",
        "path": "TMessagesProj/src/main/java/org/telegram/ui/Components/RadialProgress2.java",
        "old": "    private int lastAnnouncedPercent = -1;\n\n",
        "new": "",
    },
    {
        "id": "progress-renderer-body",
        "path": "TMessagesProj/src/main/java/org/telegram/ui/Components/RadialProgress2.java",
        "old": '''        // Tiflogram: foizni alohida, xabarni bo'ladigan e'lon bilan aytmaymiz.
        // Buning o'rniga, xabar TalkBack fokusida bo'lsa, "kontent o'zgardi"
        // signalini yuboramiz - shunda TalkBack xabarning TO'LIQ tavsifini
        // (foiz + rasm/caption + qabul qilingan vaqt) birgalikda, bitta
        // yaxlit gap sifatida qayta o'qiydi (ChatMessageCell ichida yig'iladi).
        if (parent != null && parent.isAccessibilityFocused()) {
            int percent = Math.round(Math.max(0f, Math.min(1f, value)) * 100);
            if (percent != lastAnnouncedPercent && percent > 0 && percent < 100) {
                lastAnnouncedPercent = percent;
                parent.sendAccessibilityEvent(android.view.accessibility.AccessibilityEvent.TYPE_WINDOW_CONTENT_CHANGED);
            }
            // 100% da TalkBack aytmaydi — faqat tovush (DownloadController)
        }''',
        "new": '''        // Tiflogram: accessibility progress is announced by ChatMessageCell,
        // which owns the virtual accessibility node for the message.''',
    },
    {
        "id": "message-progress-state",
        "path": "TMessagesProj/src/main/java/org/telegram/ui/Cells/ChatMessageCell.java",
        "old": '''    @Override
    public void onProgressDownload(String fileName, long downloadedSize, long totalSize) {''',
        "new": '''    private int tiflogramAccessibilityProgressPercent = -1;
    private long tiflogramAccessibilityProgressTotal;

    @Override
    public void onProgressDownload(String fileName, long downloadedSize, long totalSize) {
        if (totalSize > 0) {
            int percent = Math.round(Math.max(0f, Math.min(1f, downloadedSize / (float) totalSize)) * 100);
            if (percent != tiflogramAccessibilityProgressPercent) {
                tiflogramAccessibilityProgressPercent = percent;
                tiflogramAccessibilityProgressTotal = totalSize;
                if (percent > 0 && percent < 100) {
                    sendAccessibilityEventForVirtualView(AccessibilityNodeProvider.HOST_VIEW_ID, AccessibilityEvent.TYPE_WINDOW_CONTENT_CHANGED);
                }
            }
        }''',
    },
    {
        "id": "message-progress-description",
        "path": "TMessagesProj/src/main/java/org/telegram/ui/Cells/ChatMessageCell.java",
        "old": '''                    // Tiflogram: yuklash foizi ENG BOSHIDA aytiladi
                    if (documentAttach != null && (documentAttachType == DOCUMENT_ATTACH_TYPE_DOCUMENT || documentAttachType == DOCUMENT_ATTACH_TYPE_GIF || documentAttachType == DOCUMENT_ATTACH_TYPE_VIDEO)) {
                        if (buttonState == 1 && loadingProgressLayout != null) {
                            int tiflogramPercent = 0;
                            if (lastLoadingSizeTotal > 0) {
                                tiflogramPercent = Math.round(Math.max(0f, Math.min(1f,
                                        (float) currentMessageObject.loadedFileSize / (float) lastLoadingSizeTotal)) * 100);
                            }
                            sb.append(String.valueOf(tiflogramPercent)).append(" foiz");
                            sb.append("\\n");
                        }
                    }''',
        "new": '''                    // Tiflogram: progress comes first for every attachment
                    // whose ChatMessageCell observer receives download updates.
                    if (tiflogramAccessibilityProgressPercent >= 0 && tiflogramAccessibilityProgressTotal > 0 && currentMessageObject != null && currentMessageObject.loadedFileSize < tiflogramAccessibilityProgressTotal) {
                        sb.append(String.valueOf(tiflogramAccessibilityProgressPercent)).append(" foiz");
                        sb.append("\\n");
                    }''',
    },
]


def main():
    if MODE not in ("check", "apply"):
        raise SystemExit("mode must be check or apply")
    cache = {}
    ok = True
    for fix in FIXES:
        path = fix["path"]
        if path not in cache:
            try:
                cache[path] = open(path, encoding="utf-8").read()
            except FileNotFoundError:
                cache[path] = None
        found = cache[path] is not None and fix["old"] in cache[path]
        print(("✅" if found else "❌") + " [" + fix["id"] + "] reliable feedback patch")
        ok = ok and found
    if not ok:
        raise SystemExit(1)
    if MODE == "check":
        return
    modified = dict(cache)
    for fix in FIXES:
        path = fix["path"]
        modified[path] = modified[path].replace(fix["old"], fix["new"], 1)
    for path, content in modified.items():
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(content)
        print("Wrote " + path)


if __name__ == "__main__":
    main()
