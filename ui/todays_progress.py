from aqt import mw
from aqt.qt import (
    QDialog,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QWidget,
    QFrame,
    Qt,
)


def make_show_todays_progress(kanji_data_service):
    def show_todays_progress():
        dialog = QDialog(mw)
        dialog.setWindowTitle("Today's Progress")
        dialog.resize(820, 680)
        dialog.setMinimumSize(720, 560)

        # Main layout
        root = QVBoxLayout(dialog)
        root.setContentsMargins(20, 18, 20, 16)
        root.setSpacing(14)

        # ── Summary header ──────────────────────────────────────────────
        summary = kanji_data_service.get_todays_summary()
        header = QLabel(
            f"<span style='font-size:15px; font-weight:600; color:#1a1a1a;'>"
            f"{summary['words']}</span> "
            f"<span style='color:#666;'>words</span>  ·  "
            f"<span style='font-size:15px; font-weight:600; color:#1a1a1a;'>"
            f"{summary['kanji']}</span> "
            f"<span style='color:#666;'>kanji</span>  ·  "
            f"<span style='font-size:15px; font-weight:600; color:#1a1a1a;'>"
            f"{summary['known_cards']}</span> "
            f"<span style='color:#666;'>cards became known</span>"
        )
        header.setStyleSheet("padding: 2px 0 6px 0;")
        root.addWidget(header)

        # ── Scrollable content ──────────────────────────────────────────
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 6, 0)  # room for scrollbar
        content_layout.setSpacing(16)

        def make_section(title: str, count: int, empty_msg: str, build_items):
            """Create one modern section card."""
            card = QFrame()
            card.setObjectName("sectionCard")
            card.setStyleSheet("""
                QFrame#sectionCard {
                    background: #fafafa;
                    border: 1px solid #e8e8e8;
                    border-radius: 10px;
                }
            """)
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(16, 14, 16, 14)
            card_layout.setSpacing(10)

            # Section header row
            header_row = QHBoxLayout()
            header_row.setSpacing(10)

            title_label = QLabel(title)
            title_label.setStyleSheet(
                "font-size: 14px; font-weight: 700; color: #222; letter-spacing: 0.2px;"
            )
            header_row.addWidget(title_label)

            badge = QLabel(str(count))
            badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
            badge.setFixedHeight(22)
            badge.setMinimumWidth(28)
            badge.setStyleSheet("""
                background: #e8f0fe;
                color: #1a73e8;
                border-radius: 11px;
                font-size: 12px;
                font-weight: 700;
                padding: 0 8px;
            """)
            header_row.addWidget(badge)
            header_row.addStretch()
            card_layout.addLayout(header_row)

            # Thin separator
            sep = QFrame()
            sep.setFixedHeight(1)
            sep.setStyleSheet("background: #ececec;")
            card_layout.addWidget(sep)

            # Items
            items_layout = QVBoxLayout()
            items_layout.setSpacing(0)
            items_layout.setContentsMargins(0, 2, 0, 0)

            if count == 0:
                empty = QLabel(empty_msg)
                empty.setStyleSheet("color: #999; font-size: 13px; font-style: italic; padding: 8px 0;")
                items_layout.addWidget(empty)
            else:
                build_items(items_layout)

            card_layout.addLayout(items_layout)
            return card

        # ── Words section ───────────────────────────────────────────────
        def build_words(layout):
            for word, reading, meaning in kanji_data_service.get_todays_words():
                row = QWidget()
                row_l = QVBoxLayout(row)
                row_l.setContentsMargins(0, 8, 0, 8)
                row_l.setSpacing(2)

                top = QHBoxLayout()
                top.setSpacing(10)
                w = QLabel(word)
                w.setStyleSheet("font-size: 16px; font-weight: 600; color: #111;")
                top.addWidget(w)
                if reading:
                    r = QLabel(reading)
                    r.setStyleSheet("font-size: 13px; color: #666; font-weight: 500;")
                    top.addWidget(r)
                top.addStretch()
                row_l.addLayout(top)

                if meaning:
                    m = QLabel(meaning)
                    m.setWordWrap(True)
                    m.setStyleSheet("font-size: 13px; color: #444; line-height: 1.35;")
                    row_l.addWidget(m)

                layout.addWidget(row)

                # subtle divider between items (except last)
                # (we keep it simple – the spacing already helps)

        words_card = make_section(
            "Words learned today",
            summary["words"],
            "No words learned today.",
            build_words,
        )
        content_layout.addWidget(words_card)

        # ── Kanji section ───────────────────────────────────────────────
        def build_kanji(layout):
            for kanji, keyword in kanji_data_service.get_todays_kanji():
                row = QWidget()
                row_l = QHBoxLayout(row)
                row_l.setContentsMargins(0, 7, 0, 7)
                row_l.setSpacing(12)

                k = QLabel(kanji)
                k.setStyleSheet("font-size: 22px; font-weight: 600; color: #111;")
                row_l.addWidget(k)

                if keyword:
                    kw = QLabel(keyword)
                    kw.setStyleSheet("font-size: 13px; color: #555;")
                    row_l.addWidget(kw)

                row_l.addStretch()
                layout.addWidget(row)

        kanji_card = make_section(
            "Kanji learned today",
            summary["kanji"],
            "No kanji learned today.",
            build_kanji,
        )
        content_layout.addWidget(kanji_card)

        # ── Known cards section ─────────────────────────────────────────
        def build_known(layout):
            for word, reading, meaning in kanji_data_service.get_todays_known_cards():
                row = QWidget()
                row_l = QVBoxLayout(row)
                row_l.setContentsMargins(0, 8, 0, 8)
                row_l.setSpacing(2)

                top = QHBoxLayout()
                top.setSpacing(10)
                w = QLabel(word)
                w.setStyleSheet("font-size: 16px; font-weight: 600; color: #111;")
                top.addWidget(w)
                if reading:
                    r = QLabel(reading)
                    r.setStyleSheet("font-size: 13px; color: #666; font-weight: 500;")
                    top.addWidget(r)
                top.addStretch()
                row_l.addLayout(top)

                if meaning:
                    m = QLabel(meaning)
                    m.setWordWrap(True)
                    m.setStyleSheet("font-size: 13px; color: #444;")
                    row_l.addWidget(m)

                layout.addWidget(row)

        known_card = make_section(
            "Cards that became known today",
            summary["known_cards"],
            "No cards became known today.",
            build_known,
        )
        content_layout.addWidget(known_card)

        content_layout.addStretch()
        scroll.setWidget(content)
        root.addWidget(scroll)

        # ── Close button ────────────────────────────────────────────────
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        close_btn = QPushButton("Close")
        close_btn.setFixedWidth(110)
        close_btn.setStyleSheet("""
            QPushButton {
                background: #1a73e8;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 0;
                font-weight: 600;
                font-size: 13px;
            }
            QPushButton:hover {
                background: #1557b0;
            }
            QPushButton:pressed {
                background: #0d47a1;
            }
        """)
        close_btn.clicked.connect(dialog.accept)
        btn_row.addWidget(close_btn)
        root.addLayout(btn_row)

        dialog.exec()

    return show_todays_progress