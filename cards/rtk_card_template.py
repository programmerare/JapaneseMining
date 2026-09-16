RTK_FRONT_HTML = r"""
<div class="card-content">

  <div class="keyword">
    {{#Heisig Number}}
      <a href="https://hochanh.github.io/rtk/{{Kanji}}/index.html">
        {{Keyword}}
      </a>
    {{/Heisig Number}}

    {{^Heisig Number}}
      <div class="not-found">
        <span>Kanji not found</span>
        <a href="https://jisho.org/search/{{Kanji}}%20%23kanji">
          Jisho: {{Kanji}}
        </a>
      </div>
    {{/Heisig Number}}
  </div>

</div>
"""

RTK_BACK_HTML = r"""
<div class="card-content">

  <!-- Header -->
  <div class="keyword">
    {{#Heisig Number}}
      <a href="https://hochanh.github.io/rtk/{{Kanji}}/index.html">
        {{Keyword}}
      </a>
    {{/Heisig Number}}

    {{^Heisig Number}}
      <span class="keyword-unknown">Kanji not found</span>
    {{/Heisig Number}}
  </div>

  {{#Meanings}}
  <div class="meanings">{{Meanings}}</div>
  {{/Meanings}}

  <hr id="answer">

  <!-- Main Kanji -->
  <section class="kanji-section">

    <div class="section-label">Kanji</div>

    <div class="kanji-main">
      <span class="kanji-font yumin">{{Kanji}}</span>
      <span class="kanji-font yugothb">{{Kanji}}</span>
      <span class="kanji-font hgrkk">{{Kanji}}</span>
      <span class="kanji-font stroke-order">{{Kanji}}</span>
    </div>

  </section>

  <!-- Alternative Kanji -->
  {{#Alternative Kanji}}
  <section class="alternative-section">

    <div class="section-label">
      Alternative Kanji
    </div>

    <div class="kanji-alternative">
      <span class="kanji-font yumin">{{Alternative Kanji}}</span>
      <span class="kanji-font yugothb">{{Alternative Kanji}}</span>
      <span class="kanji-font hgrkk">{{Alternative Kanji}}</span>
      <span class="kanji-font stroke-order">{{Alternative Kanji}}</span>
    </div>

  </section>
  {{/Alternative Kanji}}

  <!-- Story -->
  {{#Story}}
  <section class="story-section">

    <div class="section-label">Story</div>

    <div class="story">
      {{Story}}
    </div>

  </section>
  {{/Story}}

  <!-- Note -->
  {{#Note}}
  <section class="note-section">

    <div class="section-label">Note</div>

    <div class="note">
      {{Note}}
    </div>

  </section>
  {{/Note}}

  <!-- Meta -->
  <section class="meta">

    {{#Stroke Count}}
    <div class="meta-item">
      <span class="meta-label">Strokes</span>
      <span class="meta-value">{{Stroke Count}}</span>
    </div>
    {{/Stroke Count}}

    {{#Heisig Number}}
    <div class="meta-item">
      <span class="meta-label">RTK</span>
      <span class="meta-value">#{{Heisig Number}}</span>
    </div>
    {{/Heisig Number}}

  </section>

</div>
"""

RTK_CARD_CSS = r"""
.card {
  font-family:
    -apple-system,
    BlinkMacSystemFont,
    "Segoe UI",
    Arial,
    sans-serif;

  font-size: 20px;
  line-height: 1.5;

  color: #2f2f2f;
  background: #fcfcfc;

  margin: 0;
  padding: 1.2em 1.1em;

  text-align: center;

  -webkit-text-size-adjust: none;
}

.card-content {
  max-width: 850px;
  margin: 0 auto;
}


/* Keyword */

.keyword {
  font-size: 1.7em;
  font-weight: 500;
  line-height: 1.2;
  margin: 0.15em 0 0.35em;
}

.keyword a {
  color: #222;
  text-decoration: none;
}

.keyword a:hover {
  color: #555;
  text-decoration: underline;
}

.keyword-unknown {
  color: #777;
}

.not-found {
  display: flex;
  flex-direction: column;
  gap: 0.25em;
  font-size: 1em;
  color: #777;
}

.not-found a {
  color: #555;
  font-size: 0.75em;
}


/* Dictionary meanings — under keyword, supportive only */

.meanings {
  margin: 0.15em auto 0.45em;
  max-width: 28em;
  font-size: 0.68em;
  font-weight: 400;
  line-height: 1.4;
  letter-spacing: 0.01em;
  color: #8a8a8a;
  text-align: center;
}


/* Divider */

hr#answer {
  border: none;
  border-top: 1px solid #dedede;
  margin: 1em 0 1.2em;
}


/* Section labels */

.section-label {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5em;

  margin: 0 0 0.55em;

  color: #777;

  font-size: 0.62em;
  font-weight: 700;

  letter-spacing: 0.12em;
  text-transform: uppercase;
}

.section-label::before,
.section-label::after {
  content: "";
  width: 2em;
  height: 1px;
  background: #ddd;
}


/* Main Kanji */

.kanji-section {
  margin-bottom: 1.3em;
}

.kanji-main {
  display: flex;
  justify-content: center;
  align-items: baseline;
  flex-wrap: wrap;

  gap: 0.05em;

  color: #181818;
  line-height: 1;
}

.kanji-font {
  display: inline-block;

  font-size: 5.8em;
  line-height: 1;

  margin: 0 0.015em;
}

.yumin {
  font-family: YUMIN;
}

.yugothb {
  font-family: YUGOTHB;
}

.hgrkk {
  font-family: HGRKK;
}

.stroke-order {
  font-family: StrokeOrder;
}


/* Alternative Kanji */

.alternative-section {
  margin-top: 1.3em;
  padding-top: 1em;

  border-top: 1px solid #eee;
}

.kanji-alternative {
  display: flex;
  justify-content: center;
  align-items: baseline;
  flex-wrap: wrap;

  gap: 0.05em;

  color: #444;
  line-height: 1;
}

.kanji-alternative .kanji-font {
  font-size: 3.8em;
}


/* Story */

.story-section {
  margin-top: 1.5em;
}

.story {
  max-width: 700px;
  margin: 0 auto;

  padding: 0.75em 0.9em;

  background: #f5f5f5;

  border: 1px solid #e8e8e8;
  border-radius: 7px;

  color: #555;

  font-family: Arial, sans-serif;
  font-size: 0.95em;

  text-align: center;
}


/* Note — same visual language as Story */

.note-section {
  margin-top: 1.5em;
}

.note {
  max-width: 700px;
  margin: 0 auto;

  padding: 0.75em 0.9em;

  background: #f5f5f5;

  border: 1px solid #e8e8e8;
  border-radius: 7px;

  color: #555;

  font-family: Arial, sans-serif;
  font-size: 0.95em;

  text-align: center;
}


/* Metadata */

.meta {
  display: flex;
  justify-content: center;
  flex-wrap: wrap;

  gap: 0.45em;

  margin-top: 1.2em;
  padding-top: 0.9em;

  border-top: 1px solid #e5e5e5;
}

.meta-item {
  display: inline-flex;
  align-items: center;

  gap: 0.35em;

  padding: 0.25em 0.65em;

  background: #f3f3f3;

  border: 1px solid #e3e3e3;
  border-radius: 999px;

  font-size: 0.65em;
}

.meta-label {
  color: #888;
  font-weight: 600;
}

.meta-value {
  color: #444;
}


/* Fonts */

@font-face {
  font-family: YUMIN;
  src: url('_YUMIN.ttf');
}

@font-face {
  font-family: StrokeOrder;
  src: url('_StrokeOrder.ttf');
}

@font-face {
  font-family: HGRKK;
  src: url('_HGRKK.ttc');
}

@font-face {
  font-family: YUGOTHB;
  src: url('_YUGOTHB.ttc');
}


/* Mobile */

@media (max-width: 600px) {
  .card {
    font-size: 18px;
    padding: 1em 0.7em;
  }

  .keyword {
    font-size: 1.45em;
  }

  .kanji-font {
    font-size: 4.4em;
  }

  .kanji-alternative .kanji-font {
    font-size: 3em;
  }

  .font-labels {
    font-size: 0.42em;
  }

  .meanings {
    font-size: 0.64em;
    max-width: 22em;
  }
}


/* Dark mode */

.nightMode .card {
  color: #ddd;
  background: #202020;
}

.nightMode .keyword a {
  color: #f0f0f0;
}

.nightMode .keyword a:hover {
  color: #fff;
}

.nightMode .keyword-unknown {
  color: #aaa;
}

.nightMode .not-found {
  color: #aaa;
}

.nightMode .not-found a {
  color: #bbb;
}

.nightMode hr#answer,
.nightMode .alternative-section,
.nightMode .meta {
  border-color: #383838;
}

.nightMode .section-label {
  color: #999;
}

.nightMode .section-label::before,
.nightMode .section-label::after {
  background: #444;
}

.nightMode .kanji-main {
  color: #f2f2f2;
}

.nightMode .kanji-alternative {
  color: #ccc;
}

.nightMode .font-labels {
  color: #777;
}

.nightMode .story {
  background: #292929;
  border-color: #3a3a3a;
  color: #ccc;
}

.nightMode .note {
  background: #292929;
  border-color: #3a3a3a;
  color: #ccc;
}

.nightMode .meanings {
  color: #8e8e8e;
}

.nightMode .meta-item {
  background: #292929;
  border-color: #3a3a3a;
}

.nightMode .meta-label {
  color: #999;
}

.nightMode .meta-value {
  color: #ccc;
}
"""
