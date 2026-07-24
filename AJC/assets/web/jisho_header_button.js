(function () {
    "use strict";

    var STATE_CMD = "ajc_jisho_header:get_state";
    var OPEN_PREFIX = "ajc_jisho_header:open:";
    var BUTTON_CLASS = "ajc-jisho-header-btn";
    var ORDERED_CLASSES = [
        "ajc-jisho-header-btn",
        "ajc-db-header-btn",
        "ajc-toolkit-translator-header-btn",
        "ajc-audio-editor-btn",
    ];

    var lastState = {
        search_ord: -1,
        search_field: "",
        has_search_term: false,
    };

    function normalizeText(value) {
        return String(value || "").replace(/\s+/g, " ").trim().toLowerCase();
    }

    function normalizeState(payload) {
        var value = payload;
        if (typeof value === "string") {
            try {
                value = JSON.parse(value);
            } catch (_err) {
                value = {};
            }
        }
        if (!value || typeof value !== "object") {
            value = {};
        }
        var ord = Number(value.search_ord);
        return {
            search_ord: isFinite(ord) ? ord : -1,
            search_field: String(value.search_field || "").trim(),
            has_search_term: Boolean(value.has_search_term),
        };
    }

    function requestState(onDone) {
        if (typeof pycmd !== "function") {
            if (typeof onDone === "function") {
                onDone(lastState);
            }
            return;
        }
        pycmd(STATE_CMD, function (payload) {
            lastState = normalizeState(payload);
            if (typeof onDone === "function") {
                onDone(lastState);
            }
        });
    }

    function findLabelContainers() {
        var containers = document.querySelectorAll(".label-container > span:last-child");
        if (containers && containers.length) {
            return containers;
        }
        containers = document.querySelectorAll(".label-container");
        return containers || [];
    }

    function createButton(ord) {
        var btn = document.createElement("span");
        btn.classList.add(BUTTON_CLASS);
        btn.setAttribute("data-ajc-jisho-ord", String(ord));
        btn.setAttribute("role", "button");
        btn.setAttribute("tabindex", "0");
        btn.title = "Search Dictionary";
        btn.textContent = "J";
        function trigger(ev) {
            ev.preventDefault();
            ev.stopPropagation();
            if (typeof pycmd !== "function") {
                return;
            }
            pycmd(OPEN_PREFIX + ord);
        }
        btn.addEventListener("click", trigger);
        btn.addEventListener("keydown", function (ev) {
            if (ev.key === "Enter" || ev.key === " ") {
                trigger(ev);
            }
        });
        return btn;
    }

    function resolveTargetIndex(labelContainers, normalized) {
        var wantedField = normalizeText(normalized.search_field);
        if (wantedField) {
            for (var idx = 0; idx < labelContainers.length; idx++) {
                var text = normalizeText(labelContainers[idx].textContent);
                if (text === wantedField || text.indexOf(wantedField) !== -1) {
                    return idx;
                }
            }
        }
        return normalized.search_ord;
    }

    function placeButton(container, btn) {
        if (!container || !btn) {
            return;
        }

        var playAnchor = null;
        try {
            playAnchor = container.querySelector(
                ".ajt-play-icon, .audio-play-button, .play-button, .play-icon, button[title*='Play'], button[title*='play'], button[aria-label*='Play'], button[aria-label*='play']"
            );
        } catch (_err) {
            playAnchor = null;
        }

        if (!btn.isConnected || btn.parentElement !== container) {
            if (playAnchor && playAnchor.parentElement === container) {
                playAnchor.insertAdjacentElement("afterend", btn);
            } else {
                container.prepend(btn);
            }
        }

        var anchor = playAnchor && playAnchor.parentElement === container ? playAnchor : null;
        for (var clsIdx = 0; clsIdx < ORDERED_CLASSES.length; clsIdx++) {
            var className = ORDERED_CLASSES[clsIdx];
            var nodes = container.querySelectorAll("." + className);
            for (var nodeIdx = 0; nodeIdx < nodes.length; nodeIdx++) {
                var node = nodes[nodeIdx];
                if (node.parentElement !== container) {
                    continue;
                }
                if (anchor) {
                    if (node.previousElementSibling !== anchor) {
                        anchor.insertAdjacentElement("afterend", node);
                    }
                    anchor = node;
                } else {
                    if (container.firstElementChild !== node) {
                        container.prepend(node);
                    }
                    anchor = node;
                }
            }
        }
    }

    function applyState(state) {
        var normalized = normalizeState(state);
        lastState = normalized;

        var labelContainers = findLabelContainers();
        if (!labelContainers || labelContainers.length === 0) {
            return;
        }

        var targetIndex = resolveTargetIndex(labelContainers, normalized);
        for (var i = 0; i < labelContainers.length; i++) {
            var container = labelContainers[i];
            var btn = container.querySelector('.' + BUTTON_CLASS + '[data-ajc-jisho-ord="' + i + '"]');
            if (!btn) {
                btn = createButton(i);
            }
            placeButton(container, btn);
            var show = i === targetIndex;
            btn.toggleAttribute("hidden", !show);
            btn.classList.toggle("is-empty", !normalized.has_search_term);
        }
    }

    var retryTimer = null;
    function scheduleRetry() {
        if (retryTimer) {
            clearTimeout(retryTimer);
        }
        retryTimer = setTimeout(function () {
            applyState(lastState);
            retryTimer = null;
        }, 350);
    }

    window.AjcJishoHeaderButton = {
        load_state: function (state) {
            applyState(state || {});
            setTimeout(function () { applyState(lastState); }, 40);
            setTimeout(function () { applyState(lastState); }, 120);
        },
        reload: function () {
            requestState(function (state) {
                applyState(state);
            });
        },
    };

    function bootstrap() {
        requestState(function (state) {
            applyState(state);
        });
        setTimeout(function () {
            requestState(function (state) {
                applyState(state);
            });
        }, 100);
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", bootstrap, { once: true });
    } else {
        setTimeout(bootstrap, 0);
    }

    try {
        var observer = new MutationObserver(scheduleRetry);
        observer.observe(document.body, { childList: true, subtree: true });
    } catch (_err) {
        // ignore
    }
})();
