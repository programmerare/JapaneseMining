"""Glowing Update reminder on the Deck Browser."""

from aqt import gui_hooks, mw

_DOT_HTML = (
    '<div id="jm--update-indicator" class="jm--update-indicator" '
    'title="Kanji knowledge may be outdated. '
    'Run Any Update Option from the JapaneseMining menu.">'
    '<span class="jm--update-dot"></span>'
    '<span class="jm--update-label">Update</span>'
    '</div>'
)

_DOT_CSS = """
.jm--update-indicator {
    position: fixed;
    top: 0px;
    right: 16px;
    z-index: 1000;
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 4px 10px 4px 8px;
    border-radius: 999px;
    background: rgba(245, 158, 11, 0.12);
    border: 1px solid rgba(245, 158, 11, 0.35);
    cursor: help;
    pointer-events: auto;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    font-size: 12px;
    font-weight: 600;
    color: #b45309;
    user-select: none;
}

.jm--update-dot {
    display: inline-block;
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: #f59e0b;
    box-shadow: 0 0 0 0 rgba(245, 158, 11, 0.55);
    animation: jm-pulse 1.6s ease-out infinite;
    flex-shrink: 0;
}

@keyframes jm-pulse {
    0%   { box-shadow: 0 0 0 0   rgba(245, 158, 11, 0.55); }
    70%  { box-shadow: 0 0 0 8px rgba(245, 158, 11, 0); }
    100% { box-shadow: 0 0 0 0   rgba(245, 158, 11, 0); }
}

.jm--update-label {
    line-height: 1;
}
"""

_STYLE_ID = "jm--update-style"


def setup_update_indicator(kanji_data_service) -> None:
    """Register Deck Browser hooks for the Update reminder."""

    def inject_css(web_content, context) -> None:
        if _STYLE_ID not in (web_content.head or ""):
            web_content.head += f'<style id="{_STYLE_ID}">{_DOT_CSS}</style>'

    def on_deck_browser_will_render_content(deck_browser, content) -> None:
        if not kanji_data_service.needs_update:
            return
        # Fixed top-right overlay; append to stats so it lands in the page body.
        content.stats = (content.stats or "") + _DOT_HTML

    gui_hooks.webview_will_set_content.append(inject_css)
    gui_hooks.deck_browser_will_render_content.append(
        on_deck_browser_will_render_content
    )


def refresh_deck_browser() -> None:
    """Redraw Deck Browser on the main thread so the indicator updates safely."""

    def _do_refresh() -> None:
        try:
            if mw.state == "deckBrowser" and getattr(mw, "deckBrowser", None) is not None:
                mw.deckBrowser.refresh()
        except Exception:
            pass

    # Update (and other CollectionOps) run off the main thread.
    # UI must always be scheduled back onto it.
    try:
        mw.taskman.run_on_main(_do_refresh)
    except Exception:
        # Fallback if taskman is unavailable (very early startup).
        _do_refresh()