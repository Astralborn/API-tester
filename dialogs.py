from PySide6.QtWidgets import (QDialog,
                               QVBoxLayout,
                               QHBoxLayout,
                               QListWidget,
                               QPushButton,
                               QCheckBox,
                               QListWidgetItem,
                               QLabel)

class MultiSelectDialog(QDialog):
    def __init__(self, items):
        super().__init__()
        self.setWindowTitle("Select Presets")
        self.resize(500, 600)  # Bigger window

        self.selected = []

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
        layout.addWidget(self.list_widget, 1)  # Stretch = 1 to fill space

        for item in items:
            list_item = QListWidgetItem(item)
            self.list_widget.addItem(list_item)

        # Buttons
        btn_layout = QHBoxLayout()
        ok_btn = QPushButton("OK")
        cancel_btn = QPushButton("Cancel")
        ok_btn.clicked.connect(self.accept_selection)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)

        layout.addLayout(btn_layout)

    def toggle_select_all(self, state):
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            item.setSelected(state == 2)  # 2 = Checked

    def accept_selection(self):
        self.selected = [item.text() for item in self.list_widget.selectedItems()]
        self.accept()
