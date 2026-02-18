from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QListWidget,
    QPushButton,
    QCheckBox,
    QListWidgetItem,
    QLabel,
)


class MultiSelectDialog(QDialog):
    def __init__(self, items: list[str]) -> None:
        super().__init__()

        self.setWindowTitle("Select Presets")
        self.resize(500, 600)

        self.selected: list[str] = []

        layout = QVBoxLayout(self)

        # Label
        layout.addWidget(QLabel("Select presets to run:"))

        # Select All checkbox
        self.select_all_cb = QCheckBox("Select All")
        self.select_all_cb.stateChanged.connect(self.toggle_select_all)
        layout.addWidget(self.select_all_cb)

        # List of presets
        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QListWidget.MultiSelection)
        layout.addWidget(self.list_widget, 1)

        for item in items:
            self.list_widget.addItem(QListWidgetItem(item))

        # Buttons
        btn_layout = QHBoxLayout()

        ok_btn = QPushButton("OK")
        cancel_btn = QPushButton("Cancel")

        ok_btn.clicked.connect(self.accept_selection)
        cancel_btn.clicked.connect(self.reject)

        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)

        layout.addLayout(btn_layout)

    # ================= Slots =================

    def toggle_select_all(self, state: int) -> None:
        """Select or deselect all items based on checkbox state."""
        checked = state == Qt.Checked

        for i in range(self.list_widget.count()):
            self.list_widget.item(i).setSelected(checked)

    def accept_selection(self) -> None:
        """Store selected items and close dialog with Accepted state."""
        self.selected = [item.text() for item in self.list_widget.selectedItems()]
        self.accept()