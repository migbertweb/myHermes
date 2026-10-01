# Instagram Reels Publication via Composio

The Instagram publication is a two-step process using the Instagram Business API.

## Workflow
1. **Create Media Container**:
   Call `INSTAGRAM_POST_IG_USER_MEDIA`.
   - `ig_user_id`: The Business account ID (find with `INSTAGRAM_GET_USER_INFO`).
   - `video_url`: Direct public HTTPS link to the MP4 file. **Signed URLs with JWT in query params work** if token lifetime exceeds Meta's fetch + processing time (~2-3 min typical). Verify with `curl -I` first.
   - `media_type`: `REELS`.
   - `caption`: Caption text for the post. Hashtags as `#tag` (auto-encoded).
   - `share_to_feed`: `true` to also appear in Feed tab (default `false`).
   - Result: `creation_id`.

2. **Publish Container**:
   Call `INSTAGRAM_POST_IG_USER_MEDIA_PUBLISH`.
   - `creation_id`: From the previous step.
   - `ig_user_id`: The Business account ID.
   - `max_wait_seconds`: 120 recommended for video/reels (processing is async; actual ~30s observed).

## Listing Published Reels
Call `INSTAGRAM_GET_IG_USER_MEDIA` with:
- `ig_user_id`: Business account ID or `me`
- `fields`: `id,caption,media_type,media_url,permalink,thumbnail_url,timestamp,username,media_product_type,total_like_count,total_comments_count,total_views_count`
- `limit`: Up to 100 per page (paginated via `after` cursor)
- Filter client-side: `media_type == 'VIDEO' && media_product_type == 'REELS'`

## Pitfalls
- **Video Processing**: Publishing will fail if the container is not in `FINISHED` status. The `PUBLISH` tool in Composio handles polling automatically if `max_wait_seconds > 0`.
- **URL Accessibility**: Meta servers must be able to fetch the video. Avoid URLs with complex redirects or short-lived signed tokens if possible. Use direct download links from file servers. **JWT query-param URLs work but verify token expiry > 5 min before posting.** Verified: tokens with ~2h lifetime work reliably.
- **Account Type**: Only supports Instagram Business or Creator accounts. Personal accounts are not supported.
- **Duplicates**: Instagram allows posting identical videos multiple times. Compare local library with `INSTAGRAM_GET_IG_USER_MEDIA` captions/filenames before publishing to avoid accidental duplicates. Match by title/filename substring in caption.

## Batch Publishing Workflow
For multiple videos:
1. Call `INSTAGRAM_GET_USER_INFO` once to get `ig_user_id`.
2. For each video, call `INSTAGRAM_POST_IG_USER_MEDIA` (create container) — collect all `creation_id`s.
3. Call `INSTAGRAM_POST_IG_USER_MEDIA_PUBLISH` in parallel for all `creation_id`s with `max_wait_seconds: 120`.
4. This avoids sequential wait times; total time ≈ longest single video processing (~30-50s).

## Caption Generation
- Generate from video title: descriptive first line + context paragraph + CTA question + hashtag block.
- Keep total under 2200 chars (Instagram limit). Typical: 300-500 chars.
- Include relevant hashtags: `#linux #hyprland #archlinux #cachyos #devops #foss #privacidad #localai` per topic.
- Use `share_to_feed: true` for Reels to also appear in Feed tab.
