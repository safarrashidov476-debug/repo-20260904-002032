# Telegram source findings

Analysis target: `DrKLO/Telegram` revision `62b56a07ca7e30e39f7fd00a6728d6bbd716ca1c` (`12.10.1`, build `7038`). The revision is reachable from GitHub and was checked out locally under `telegram-src-analysis`.

## Download completion

`DownloadController.didReceivedNotification()` handles both `NotificationCenter.fileLoaded` and `NotificationCenter.httpFileDidLoad` at the same branch. The event supplies a filename, then the controller calls `checkDownloadFinished(fileName, 0)`. The current Tiflogram patch injects sound playback before that lifecycle completes and tries to infer user intent by scanning `downloadingFiles` and `recentDownloadingFiles`.

The current sound filter only checks `MessageObject.getDocument()` and compares `fileName` with `FileLoader.getAttachFileName(document)`. Telegram also represents photo downloads through `PhotoSize`, and `MessageObject.getFileName()` explicitly handles documents, photos, and webpage documents. Therefore the current filter can miss valid photo/media downloads. Filename-only matching is also ambiguous when multiple downloads share a generated name or when the list transitions during completion.

## Progress accessibility

Telegram uses `RadialProgress2` in `ChatMessageCell` for both `radialProgress` and `videoRadialProgress`, while other cells and media components have their own progress renderers. The current Tiflogram patch announces only from `RadialProgress2.setProgress()` and only when that renderer's `parent.isAccessibilityFocused()` is true. This can miss updates when focus is represented by ChatMessageCell's virtual accessibility node rather than the renderer parent, when the video renderer is the active one, or when another cell handles the media.

`ChatMessageCell` builds a virtual accessibility node through `MessageAccessibilityNodeProvider`. Its content description is assembled on demand and currently reads progress from `radialProgress` in one sending branch, but download progress is not centrally announced from the download event stream. A robust solution should track download progress by file identity/message association in the cell/controller path and emit a virtual-node content-change event only for the focused message, rather than relying solely on a renderer view's focus state.

## Translation

`TranslateController.pushToTranslate()` batches message text and, when `translationsAutoEnabled` is `alternative` or `system`, calls `TranslateAlert2.alternativeTranslate()` for each queued text. The current patch forces `method = "alternative"`, but the bundled `TiflogramTranslate.java` is not referenced anywhere by the patch scripts or upstream call sites. The alternative implementation performs an unauthenticated HTTP request to Google Translate's `translate_a/single` endpoint, URL-encodes the text, and parses the first result array. It has a hard 5000-character split path and reports one failure if any part fails.

The upstream translation controller's source text is `message.messageOwner.message` for normal messages, voice transcription for open final transcriptions, and it batches by message/dialog. Captions and rich media have separate translation paths. Consequently, forcing the alternative branch fixes only the normal text batch path; captions, polls, photo/story/rich-message paths, empty/non-text messages, and requests that are not routed through `pushToTranslate()` can still behave differently or fail.
