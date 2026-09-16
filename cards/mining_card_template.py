MINING_FORWARD_FRONT_HTML = r"""
<div class="kanji" style="margin-top:0.3em;">
  <ruby class="{{^No Kanji}}{{#Usually Kana}}is-always-visible{{/Usually Kana}}{{/No Kanji}}">
    {{Word}}
    <rt>{{Reading}}</rt>
  </ruby>
</div>

<div class="top-right">
	<!-- Indicators -->
		<div class="indicators">
		<!-- Usually Kana indicator -->
		<div class="usually-kana-indicator {{#Usually Kana}}true{{/Usually Kana}}{{^Usually Kana}}false{{/Usually Kana}}">
  			<span class="tooltip">
				{{#Usually Kana}}Usually Kana{{/Usually Kana}}
				{{^Usually Kana}}Usually Kanji{{/Usually Kana}}
  			</span>
		</div>

		<!-- Kanji indicator -->
		<div class="kanji-indicator {{#No Kanji}}no-kanji{{/No Kanji}}{{^No Kanji}}{{#Kanji is known}}known{{/Kanji is known}}{{^Kanji is known}}unknown{{/Kanji is known}}{{/No Kanji}}">
  			<span class="tooltip">
				{{#No Kanji}}No Kanji{{/No Kanji}}
				{{^No Kanji}}
    				{{#Kanji is known}}Kanji known{{/Kanji is known}}
    				{{^Kanji is known}}Kanji unknown{{/Kanji is known}}
				{{/No Kanji}}
  			</span>
		</div>
	</div>
</div>

<div id="hint" style="display:none; margin-top:0.3em;">
  <div class="example">{{Example Sentence}}</div>
</div>

{{#Example Sentence}}
<button onclick="document.getElementById('hint').style.display='block'; this.style.display='none';">
  Show Sentence
</button>
{{/Example Sentence}}
"""

MINING_FORWARD_BACK_HTML = r"""
<style>
.card {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
	font-size: 1.2em;
  color: #2f2f2f;
  line-height: 1.5;
  position: relative;
  padding: 0.8em 1em;
  background: #fcfcfc;
  border-radius: 8px;
  box-shadow: 0 2px 6px rgba(0,0,0,0.05);
}

/* Badges */
.badges {
  display: flex;
  flex-direction: column;
  gap: 0.2em;
}

.badge {
  font-size: 0.5em;
  font-weight: 600;
  padding: 0.1em 0.35em;
  border-radius: 10px;
  color: #fff;
  text-align: center;
  white-space: nowrap;
}

.badge.jlpt { background-color: #4d8dff; }
.badge.wk { background-color: #c04dff; }
.badge.common { background-color: #4fbf6a; }

/* Section labels */
h1 {
  font-size: 0.75em;
  font-weight: 600;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  margin: 1em 0 0.3em;
  color: #777;
}

/* Dividers */
hr {
  border: none;
  border-top: 1px solid #ddd;
  margin: 0.8em 0;
}

/* Note section */
.note {
  font-size: 0.9em;
  color: #555;
  background: #f6f6f6;
  padding: 0.5em 0.6em;
  border-radius: 6px;
}

/* Mnemonic section */
.mnemonic {
  font-size: 0.9em;
  color: #555;
  background: #f6f6f6;
  padding: 0.5em 0.6em;
  border-radius: 6px;
}

/* Meta info */
.meta {
  font-size: 0.82em;
  color: #666;
  margin-top: 0.6em;
}

/* Kanji Meanings Tooltip */
#kanji-tooltip {
  position: fixed;
  display: none;
  background: #222;
  color: #fff;
  padding: 6px 8px;
  border-radius: 6px;
  font-size: 0.85em;
  pointer-events: none;
  max-width: 220px;
  z-index: 9999;
}

/* Audio Play Button */
.audio-button {
  display: flex;
  justify-content: flex-end;
}
</style>

<div class="kanji" style="margin-top:0.3em;">
  <ruby>
    {{Word}}
    <rt>{{Reading}}</rt>
  </ruby>
</div>

<!-- Top-right info area -->
<div class="top-right">
	<!-- Indicators -->
		<div class="indicators">
		<!-- Usually Kana indicator -->
		<div class="usually-kana-indicator {{#Usually Kana}}true{{/Usually Kana}}{{^Usually Kana}}false{{/Usually Kana}}">
  			<span class="tooltip">
				{{#Usually Kana}}Usually Kana{{/Usually Kana}}
				{{^Usually Kana}}Usually Kanji{{/Usually Kana}}
  			</span>
		</div>

		<!-- Kanji indicator -->
		<div class="kanji-indicator {{#No Kanji}}no-kanji{{/No Kanji}}{{^No Kanji}}{{#Kanji is known}}known{{/Kanji is known}}{{^Kanji is known}}unknown{{/Kanji is known}}{{/No Kanji}}">
  			<span class="tooltip">
				{{#No Kanji}}No Kanji{{/No Kanji}}
				{{^No Kanji}}
    				{{#Kanji is known}}Kanji known{{/Kanji is known}}
    				{{^Kanji is known}}Kanji unknown{{/Kanji is known}}
				{{/No Kanji}}
  			</span>
		</div>
	</div>

	<!-- Badges in top-right corner -->
  <div class="badges">
    <div class="badge jlpt">JLPT {{JLPT Level}}</div>
    <div class="badge wk">WK {{Wanikani Level}}</div>
    <div class="badge common">{{#Is Common}}Common{{/Is Common}}{{^Is Common}}Rare{{/Is Common}}</div>
  </div>

	<!-- Audio Play Button -->
  <div class="audio-button">
    {{Audio}}
  </div>
</div>

<h1>Reading</h1>
<div class="reading">
  {{Reading}}
</div>

<h1>Meaning</h1>
<div class="meaning">{{Meaning}}</div>

<h1>Example Sentence</h1>
<div class="example">{{Example Sentence}}</div>
<div class="example">{{Translation}}</div>

{{#Note}}
<h1>Note</h1>
<div class="note">{{Note}}</div>
{{/Note}}

{{#Mnemonic}}
<h1>Mnemonic</h1>
<div class="mnemonic">{{Mnemonic}}</div>
{{/Mnemonic}}

<hr>

<div class="meta">
  <strong>Part of speech:</strong> {{Part of speech}} ·<br>
  <strong>Info:</strong> {{Info}} ·<br>
  <strong>Tags:</strong> {{Tags}} ·<br>
  <strong>Other forms:</strong> {{Other forms}} ·
</div>

<!-- Kanji Keywords -->
{{#Kanji Keywords}}
<h1>Kanji Keywords</h1>
<div class="kanji-keywords">
  <div class="kanji-list">
    {{Kanji Keywords}}
  </div>
</div>
{{/Kanji Keywords}}

<!-- Kanji Meanings Tooltip-->
<div id="kanji-tooltip"></div>

<!-- Java Script -->
<script>
(() => {
    <!-- Format Kanji Meanings -->
    const rawMeanings = `{{Kanji Meanings}}`;

    const kanjiMeanings = Object.fromEntries(
        rawMeanings.split("|").map(part => {
            const [kanji, meanings] = part.split(":").map(s => s.trim());
            return [kanji, meanings];
        }).filter(x => x[0] && x[1])
    );

    <!-- Wrap Kanji in spans -->
    function wrapKanji(root) {
        if (!root) return;
        if (root.dataset.wrapped) return;
        root.dataset.wrapped = "1";

        const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
        const kanjiRegex = /[\u4e00-\u9faf]/g;

        const nodes = [];
        let node;

        while (node = walker.nextNode()) {
            if (kanjiRegex.test(node.nodeValue)) {
                nodes.push(node);
            }
        }

        for (const textNode of nodes) {
            const span = document.createElement("span");
            span.innerHTML = textNode.nodeValue.replace(
                kanjiRegex,
                c => `<span class="kanji-hover" data-kanji="${c}">${c}</span>`
            );
            textNode.replaceWith(span);
        }
    }

    function initializeCard() {
        const targets = [
            document.querySelector(".kanji"),
            document.querySelector(".kanji-list")
        ];

        targets.forEach(wrapKanji);
    }

    initializeCard();

    <!-- Hover logic to show Kanji Meaning Tooltip -->
    const tooltip = document.getElementById("kanji-tooltip");

    document.addEventListener("mouseover", (e) => {
        const el = e.target.closest(".kanji-hover");
        if (!el) return;

        const kanji = el.dataset.kanji;
        const meaning = kanjiMeanings[kanji];

        if (!meaning) return;

        tooltip.textContent = `${kanji}: ${meaning}`;
        tooltip.style.display = "block";
    });

    document.addEventListener("mousemove", (e) => {
        const margin = 12;

        let cursorX = e.clientX;
        let cursorY = e.clientY;

        let windowWidth = window.innerWidth;
        let windowHeight = window.innerHeight;

        let tooltipWidth = tooltip.offsetWidth;
        let tooltipHeight = tooltip.offsetHeight;

        let tooltipX = cursorX + margin;
        let tooltipY = cursorY + margin;

        tooltip.style.left = (tooltipX) + "px";
        tooltip.style.top = (tooltipY) + "px";

        if (tooltipX + tooltipWidth > windowWidth) {
            tooltipX = cursorX - tooltipWidth - margin;
        }

        if (tooltipY + tooltipHeight > windowHeight) {
            tooltipY = cursorY - tooltipHeight - margin;
        }

        tooltip.style.left = `${tooltipX}px`;
        tooltip.style.top = `${tooltipY}px`;
    });

    document.addEventListener("mouseout", (e) => {
        if (e.target.closest(".kanji-hover")) {
            tooltip.style.display = "none";
        }
    });
})();
</script>
"""

MINING_BACKWARD_FRONT_HTML = r"""
<div class="meaning" id="readingFront">
  {{Meaning}}
</div>

<div class="top-right">
	<!-- Indicators -->
		<div class="indicators">
		<!-- Usually Kana indicator -->
		<div class="usually-kana-indicator {{#Usually Kana}}true{{/Usually Kana}}{{^Usually Kana}}false{{/Usually Kana}}">
  			<span class="tooltip">
				{{#Usually Kana}}Usually Kana{{/Usually Kana}}
				{{^Usually Kana}}Usually Kanji{{/Usually Kana}}
  			</span>
		</div>

		<!-- Kanji indicator -->
		<div class="kanji-indicator {{#No Kanji}}no-kanji{{/No Kanji}}{{^No Kanji}}{{#Kanji is known}}known{{/Kanji is known}}{{^Kanji is known}}unknown{{/Kanji is known}}{{/No Kanji}}">
  			<span class="tooltip">
				{{#No Kanji}}No Kanji{{/No Kanji}}
				{{^No Kanji}}
    				{{#Kanji is known}}Kanji known{{/Kanji is known}}
    				{{^Kanji is known}}Kanji unknown{{/Kanji is known}}
				{{/No Kanji}}
  			</span>
		</div>
	</div>
</div>

<div id="hint" style="display:none; margin-top:0.3em;">
  <div class="example">{{Translation}}</div>
</div>

{{#Example Sentence}}
<button onclick="document.getElementById('hint').style.display='block'; this.style.display='none';">
  Show Sentence
</button>
{{/Example Sentence}}
"""

MINING_BACKWARD_BACK_HTML = r"""
<style>
.card {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
	font-size: 1.2em;
  color: #2f2f2f;
  line-height: 1.5;
  position: relative;
  padding: 0.8em 1em;
  background: #fcfcfc;
  border-radius: 8px;
  box-shadow: 0 2px 6px rgba(0,0,0,0.05);
}

/* Badges */
.badges {
  display: flex;
  flex-direction: column;
  gap: 0.2em;
}

.badge {
  font-size: 0.5em;
  font-weight: 600;
  padding: 0.1em 0.35em;
  border-radius: 10px;
  color: #fff;
  text-align: center;
  white-space: nowrap;
}

.badge.jlpt { background-color: #4d8dff; }
.badge.wk { background-color: #c04dff; }
.badge.common { background-color: #4fbf6a; }

/* Section labels */
h1 {
  font-size: 0.75em;
  font-weight: 600;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  margin: 1em 0 0.3em;
  color: #777;
}

/* Dividers */
hr {
  border: none;
  border-top: 1px solid #ddd;
  margin: 0.8em 0;
}

/* Note section */
.note {
  font-size: 0.9em;
  color: #555;
  background: #f6f6f6;
  padding: 0.5em 0.6em;
  border-radius: 6px;
}

/* Mnemonic section */
.mnemonic {
  font-size: 0.9em;
  color: #555;
  background: #f6f6f6;
  padding: 0.5em 0.6em;
  border-radius: 6px;
}

/* Meta info */
.meta {
  font-size: 0.82em;
  color: #666;
  margin-top: 0.6em;
}

/* Kanji Meanings Tooltip */
#kanji-tooltip {
  position: fixed;
  display: none;
  background: #222;
  color: #fff;
  padding: 6px 8px;
  border-radius: 6px;
  font-size: 0.85em;
  pointer-events: none;
  max-width: 220px;
  z-index: 9999;
}

/* Audio Play Button */
.audio-button {
  display: flex;
  justify-content: flex-end;
}
</style>

<div class="kanji" style="margin-top:0.3em;">
  <ruby>
    {{Word}}
    <rt>{{Reading}}</rt>
  </ruby>
</div>

<!-- Top-right info area -->
<div class="top-right">
	<!-- Indicators -->
		<div class="indicators">
		<!-- Usually Kana indicator -->
		<div class="usually-kana-indicator {{#Usually Kana}}true{{/Usually Kana}}{{^Usually Kana}}false{{/Usually Kana}}">
  			<span class="tooltip">
				{{#Usually Kana}}Usually Kana{{/Usually Kana}}
				{{^Usually Kana}}Usually Kanji{{/Usually Kana}}
  			</span>
		</div>

		<!-- Kanji indicator -->
		<div class="kanji-indicator {{#No Kanji}}no-kanji{{/No Kanji}}{{^No Kanji}}{{#Kanji is known}}known{{/Kanji is known}}{{^Kanji is known}}unknown{{/Kanji is known}}{{/No Kanji}}">
  			<span class="tooltip">
				{{#No Kanji}}No Kanji{{/No Kanji}}
				{{^No Kanji}}
    				{{#Kanji is known}}Kanji known{{/Kanji is known}}
    				{{^Kanji is known}}Kanji unknown{{/Kanji is known}}
				{{/No Kanji}}
  			</span>
		</div>
	</div>

	<!-- Badges in top-right corner -->
  <div class="badges">
    <div class="badge jlpt">JLPT {{JLPT Level}}</div>
    <div class="badge wk">WK {{Wanikani Level}}</div>
    <div class="badge common">{{#Is Common}}Common{{/Is Common}}{{^Is Common}}Rare{{/Is Common}}</div>
  </div>

	<!-- Audio Play Button -->
  <div class="audio-button">
    {{Audio}}
  </div>
</div>

<h1>Reading</h1>
<div class="reading">
  {{Reading}}
</div>

<h1>Meaning</h1>
<div class="meaning">{{Meaning}}</div>

<h1>Example Sentence</h1>
<div class="example">{{Example Sentence}}</div>
<div class="example">{{Translation}}</div>

{{#Note}}
<h1>Note</h1>
<div class="note">{{Note}}</div>
{{/Note}}

{{#Mnemonic}}
<h1>Mnemonic</h1>
<div class="mnemonic">{{Mnemonic}}</div>
{{/Mnemonic}}

<hr>

<div class="meta">
  <strong>Part of speech:</strong> {{Part of speech}} ·<br>
  <strong>Info:</strong> {{Info}} ·<br>
  <strong>Tags:</strong> {{Tags}} ·<br>
  <strong>Other forms:</strong> {{Other forms}} ·
</div>

<!-- Kanji Keywords -->
{{#Kanji Keywords}}
<h1>Kanji Keywords</h1>
<div class="kanji-keywords">
  <div class="kanji-list">
    {{Kanji Keywords}}
  </div>
</div>
{{/Kanji Keywords}}

<!-- Kanji Meanings Tooltip-->
<div id="kanji-tooltip"></div>

<!-- Java Script -->
<script>
(() => {
    <!-- Format Kanji Meanings -->
    const rawMeanings = `{{Kanji Meanings}}`;

    const kanjiMeanings = Object.fromEntries(
        rawMeanings.split("|").map(part => {
            const [kanji, meanings] = part.split(":").map(s => s.trim());
            return [kanji, meanings];
        }).filter(x => x[0] && x[1])
    );

    <!-- Wrap Kanji in spans -->
    function wrapKanji(root) {
        if (!root) return;
        if (root.dataset.wrapped) return;
        root.dataset.wrapped = "1";

        const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
        const kanjiRegex = /[\u4e00-\u9faf]/g;

        const nodes = [];
        let node;

        while (node = walker.nextNode()) {
            if (kanjiRegex.test(node.nodeValue)) {
                nodes.push(node);
            }
        }

        for (const textNode of nodes) {
            const span = document.createElement("span");
            span.innerHTML = textNode.nodeValue.replace(
                kanjiRegex,
                c => `<span class="kanji-hover" data-kanji="${c}">${c}</span>`
            );
            textNode.replaceWith(span);
        }
    }

    function initializeCard() {
        const targets = [
            document.querySelector(".kanji"),
            document.querySelector(".kanji-list")
        ];

        targets.forEach(wrapKanji);
    }

    initializeCard();

    <!-- Hover logic to show Kanji Meaning Tooltip -->
    const tooltip = document.getElementById("kanji-tooltip");

    document.addEventListener("mouseover", (e) => {
        const el = e.target.closest(".kanji-hover");
        if (!el) return;

        const kanji = el.dataset.kanji;
        const meaning = kanjiMeanings[kanji];

        if (!meaning) return;

        tooltip.textContent = `${kanji}: ${meaning}`;
        tooltip.style.display = "block";
    });

    document.addEventListener("mousemove", (e) => {
        const margin = 12;

        let cursorX = e.clientX;
        let cursorY = e.clientY;

        let windowWidth = window.innerWidth;
        let windowHeight = window.innerHeight;

        let tooltipWidth = tooltip.offsetWidth;
        let tooltipHeight = tooltip.offsetHeight;

        let tooltipX = cursorX + margin;
        let tooltipY = cursorY + margin;

        tooltip.style.left = (tooltipX) + "px";
        tooltip.style.top = (tooltipY) + "px";

        if (tooltipX + tooltipWidth > windowWidth) {
            tooltipX = cursorX - tooltipWidth - margin;
        }

        if (tooltipY + tooltipHeight > windowHeight) {
            tooltipY = cursorY - tooltipHeight - margin;
        }

        tooltip.style.left = `${tooltipX}px`;
        tooltip.style.top = `${tooltipY}px`;
    });

    document.addEventListener("mouseout", (e) => {
        if (e.target.closest(".kanji-hover")) {
            tooltip.style.display = "none";
        }
    });
})();
</script>
"""

MINING_CARD_CSS = r"""
.card {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
	font-size: 1.2em;
  color: #2f2f2f;
  line-height: 1.5;
  position: relative;
  padding: 0.8em 1em;
  background: #fcfcfc;
  border-radius: 8px;
  box-shadow: 0 2px 6px rgba(0,0,0,0.05);
}

/* Text sizing */
.reading {
  font-size: 1.5em;
  margin-bottom: 0.4em;
}

.meaning {
  font-size: 1em;
  margin-bottom: 0.5em;
}

.example {
  font-size: 0.95em;
  margin-top: 0.5em;
  padding-left: 0.5em;
  border-left: 3px solid #ddd;
  color: #444;
  font-style: italic;
}

/* Smaller, top-right container */
.top-right {
  position: absolute;
  top: 0.8em;
  right: 1em;

  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 0.4em;
}

/* Kanji display */
.kanji {
  font-size: 1.5em;
  font-weight: 500;
  cursor: help;
}

/* Indicators within top-right container */
.indicators {
	display: flex;
	gap: 0.4em;
	align-items: center;
}

/* Kanji is known indicator */
.kanji-indicator {
  position: relative;
  top: 0px;
  right: 0px;
  width: 10px;
  height: 10px;
  border-radius: 50%;
}

.kanji-indicator.known {
  background-color: #4caf50;
}

.kanji-indicator.unknown {
  background-color: #ffa500;
}

.kanji-indicator.no-kanji {
	background-color: #ccc;
}

/* Usually Kana indicator */
.usually-kana-indicator {
  position: relative;
  top: 0px;
  right: 0px;
  width: 10px;
  height: 10px;
  border-radius: 50%;
	background-color: #ccc;
}

.usually-kana-indicator.true {
	background-color: #9c27b0
}

.usually-kana-indicator.false {
	background-color: #2196f3;
}

/* Tooltip */
.tooltip {
  visibility: hidden;
  opacity: 0;
  position: absolute;
  top: 140%;
  right: 0;
  background: #333;
  color: #fff;
  font-size: 0.75em;
  padding: 4px 6px;
  border-radius: 4px;
  white-space: nowrap;
  transition: opacity 0.2s;
}

.kanji-indicator:hover .tooltip {
  visibility: visible;
  opacity: 1;
}

.usually-kana-indicator:hover .tooltip {
	visibility: visible;
	opacity: 1;
}

/* Hide furigana by default */
ruby rt {
  visibility: hidden;
  font-size: 0.5em;
  color: #555;
}

/* Show furigana always */
ruby.is-always-visible rt {
  visibility: visible;
}

/* Show furigana on hover */
ruby:not(.is-always-visible):hover rt {
  visibility: visible;
}

/* Kanji Keywords */
.kanji-keywords {
  margin-top: 0em;
}

.kanji-list {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4em;
  margin-top: 0.4em;
}

.kanji-chip {
  display: inline-block;
  padding: 0.25em 0.55em;
  background: #f6f6f6;
  border: 1px solid #e3e3e3;
  border-radius: 999px;
  font-size: 0.82em;
  color: #555;
  line-height: 1.3;
}

.kanji-chip .char {
  font-size: 1.15em;
  font-weight: 600;
  color: #222;
  margin-right: 0.25em;
}
"""