import sys
import re
from PyQt6.QtWidgets import ( 
    QApplication, QWidget, QVBoxLayout, QGridLayout, QHBoxLayout,
    QLineEdit, QLabel, QPushButton, QGroupBox, QFormLayout, QMessageBox
)
from PyQt6.QtCore import pyqtSignal, QTimer
from PyQt6.QtGui import QIntValidator

# Import the new Bleak-based Bluetooth service and existing modules
from wifi_service import ESP32detailsManager,ESP32_IP
import locker_logic
from send_automated_email import send_automated_email

EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$')

# --- Custom Locker Widget ---
class LockerWidget(QPushButton):
    clicked_signal = pyqtSignal(str)
    def __init__(self, locker_id: str, is_occupied: bool = False, parent=None):
        super().__init__(locker_id, parent)
        self.locker_id = locker_id
        self.is_occupied = is_occupied
        self.is_selected = False
        self.clicked.connect(self._handle_click)
        self.update_style()
    def _handle_click(self):
        self.clicked_signal.emit(self.locker_id)
    def update_style(self):
        if self.is_occupied:
            color, border = ("#D32F2F", "3px solid black" if self.is_selected else "1px solid #555")
        else:
            color, border = ("#4CAF50" if self.is_selected else "#388E3C", "3px solid black" if self.is_selected else "1px solid #555")
        self.setStyleSheet(f"""
            QPushButton {{ background-color: {color}; color: white; font-weight: bold; border: {border}; border-radius: 4px; min-height: 50px; min-width: 50px; }}
            QPushButton:hover {{ background-color: #E0E0E0; color: black; }}
        """)


# --- Main Application Window ---
class LockerGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Locker System GUI (Wifi)")
        self.setGeometry(200, 200, 500, 450)

        # State management
        self.locker_widgets = {}
        self.selected_locker_id = None
        self.is_name_valid = False
        self.is_email_valid = False
        self.is_job_number_valid = False

        # Layouts and Widgets
        self.main_layout = QVBoxLayout(self)
        self.create_user_input_group()
        self.create_lockers_group()
        self.create_action_buttons()
        self.setLayout(self.main_layout)

        self.esp32_manager = ESP32detailsManager(esp32_ip=ESP32_IP)
        # Defer initialization until the main window is shown
        QTimer.singleShot(100, self.initialize_system)

    def initialize_system(self):
        """
        Connects to Bluetooth and performs initial sync. If it fails,
        it shows an error and closes the application.
        """
        # This is a blocking call, so we inform the user
        QMessageBox.information(self, "Connecting...", "Attempting to connect to the ESP32. Please wait...")
        
        self.esp32_manager.make_backup()
        isSynced = self.esp32_manager.sync_from_esp32()
        if(not isSynced):
            QMessageBox.critical(self, "Connection Error", "Could not sync with ESP32!")
            self.close()
            return

        self.load_initial_locker_states()
        self.setEnabled(True) # Enable the main GUI content


    def create_user_input_group(self):
        user_groupbox = QGroupBox("User Information")
        layout = QFormLayout()
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Enter user's full name")
        self.name_input.textChanged.connect(self.validate_name)
        layout.addRow(QLabel("Name:"), self.name_input)
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Enter a valid email address")
        self.email_input.textChanged.connect(self.validate_email)
        layout.addRow(QLabel("Email:"), self.email_input)

        self.job_number_input = QLineEdit()
        self.job_number_input.setPlaceholderText("Enter job number")
        self.job_number_input.setValidator(QIntValidator())
        self.job_number_input.textChanged.connect(self.validate_job_number)
        layout.addRow(QLabel("Job Number:"), self.job_number_input)

        user_groupbox.setLayout(layout)
        self.main_layout.addWidget(user_groupbox)

    def create_lockers_group(self):
        lockers_groupbox = QGroupBox("Select a Locker")
        grid_layout = QGridLayout()
        lockers_to_create = [
            ("101", 0, 0, 1, 1), ("102", 0, 1, 1, 1), ("103", 0, 2, 1, 2),
            ("201", 1, 0, 1, 1), ("202", 1, 1, 2, 1), ("203", 1, 3, 1, 1),
            ("301", 2, 0, 1, 1), ("302", 2, 2, 1, 2)
        ]
        for locker_id, row, col, r_span, c_span in lockers_to_create:
            locker_widget = LockerWidget(locker_id)
            locker_widget.clicked_signal.connect(self.on_locker_selected)
            grid_layout.addWidget(locker_widget, row, col, r_span, c_span)
            self.locker_widgets[locker_id] = locker_widget
        lockers_groupbox.setLayout(grid_layout)
        self.main_layout.addWidget(lockers_groupbox)
        self.main_layout.addStretch()

    def create_action_buttons(self):
        button_layout = QHBoxLayout()
        self.unlock_button = QPushButton("Unlock")
        self.unlock_button.setEnabled(False)
        self.unlock_button.clicked.connect(self.run_unlock_process)
        button_layout.addWidget(self.unlock_button)
        self.submit_button = QPushButton("Submit")
        self.submit_button.setEnabled(False)
        self.submit_button.clicked.connect(self.run_submission_process)
        button_layout.addWidget(self.submit_button)
        self.main_layout.addLayout(button_layout)

    def load_initial_locker_states(self):
        states = locker_logic.get_all_locker_states()
        for locker_id, widget in self.locker_widgets.items():
            widget.is_occupied = states.get(locker_id, False)
            widget.update_style()

    def on_locker_selected(self, locker_id: str):
        if self.selected_locker_id and self.selected_locker_id in self.locker_widgets:
            self.locker_widgets[self.selected_locker_id].is_selected = False
            self.locker_widgets[self.selected_locker_id].update_style()
        self.selected_locker_id = locker_id
        self.locker_widgets[locker_id].is_selected = True
        self.locker_widgets[locker_id].update_style()
        self.update_button_states()

    def validate_name(self, text: str):
        self.is_name_valid = bool(text.strip())
        self.name_input.setStyleSheet("border: 2px solid #388E3C;" if self.is_name_valid else "border: 2px solid #D32F2F;")
        self.update_button_states()

    def validate_email(self, text: str):
        self.is_email_valid = bool(EMAIL_REGEX.match(text)) if text else False
        self.email_input.setStyleSheet("border: 2px solid #388E3C;" if self.is_email_valid else "border: 2px solid #D32F2F;")
        self.update_button_states()

    def validate_job_number(self, text: str):
        self.is_job_number_valid = bool(text.strip())
        self.job_number_input.setStyleSheet("border: 2px solid #388E3C;" if self.is_job_number_valid else "border: 2px solid #D32F2F;")
        self.update_button_states()

    def update_button_states(self):
        locker_is_selected = self.selected_locker_id is not None
        is_occupied = self.locker_widgets[self.selected_locker_id].is_occupied if locker_is_selected else False
        can_submit = self.is_email_valid and self.is_name_valid and locker_is_selected and not is_occupied
        self.submit_button.setEnabled(can_submit)
        can_unlock = locker_is_selected and is_occupied
        self.unlock_button.setEnabled(can_unlock)

    def run_unlock_process(self):
        locker_id = self.selected_locker_id
        if not locker_id: return

        reply = QMessageBox.question(self, "Confirm Unlock", f"Unlock Locker <b>{locker_id}</b>?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel)
        if reply == QMessageBox.StandardButton.Cancel: return

        if not locker_logic.release_locker(locker_id):
            QMessageBox.critical(self, "Error", "Failed to unlock the locker locally.")
            return

        if not self.esp32_manager.update_esp32():
            QMessageBox.warning(self, "Sync Warning", "Locker unlocked locally, but failed to sync to ESP32. Rolling back local changes.")
            # Rollback: Re-assign the locker to the previous user
        else:
            QMessageBox.information(self, "Success", f"Locker {locker_id} has been unlocked and synced.")
            self.locker_widgets[locker_id].is_occupied = False
            self.reset_ui_state()
            self.locker_widgets[locker_id].update_style()
        


    def run_submission_process(self):
        name = self.name_input.text().strip()
        email = self.email_input.text()
        locker_id = self.selected_locker_id
        job_number = self.job_number_input.text().strip()

        reply = QMessageBox.question(self, "Confirm Submission", f"<b>Name:</b> {name}<br><b>Locker:</b> {locker_id}<br><br>Proceed?", QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel)
        if reply == QMessageBox.StandardButton.Cancel: return
        self.submit_button.setEnabled(False)
        self.submit_button.setText("Processing...")
        new_passcode = locker_logic.assign_locker(locker_id, name, email)
        if not new_passcode:
            QMessageBox.critical(self, "Error", "Failed to update local database.")
            self.reset_ui_state()
            return
        
        # Note: need to add field for job number
        if not self.esp32_manager.update_esp32():
            QMessageBox.warning(self, "Sync Failed", "Locker assigned, ESP32 sync failed. Email not sent. Rolling back.")
            locker_logic.release_locker(locker_id)
            self.reset_ui_state()
            return
        if not send_automated_email(self, email, job_number, locker_id, new_passcode):
            QMessageBox.warning(self, "Email Failed", "Locker assigned, ESP32 sync success, but email failed. Rolling back.")
            locker_logic.release_locker(locker_id)
            self.reset_ui_state()
            return

        QMessageBox.information(self, "Success", f"Locker {locker_id} assigned to {name}. Passcode sent via email.")
        self.locker_widgets[locker_id].is_occupied = True
        self.reset_ui_state()
        self.locker_widgets[locker_id].update_style()

    def reset_ui_state(self):
        if self.selected_locker_id and self.selected_locker_id in self.locker_widgets:
            self.locker_widgets[self.selected_locker_id].is_selected = False
            self.locker_widgets[self.selected_locker_id].update_style()
        self.selected_locker_id = None
        self.name_input.clear()
        self.email_input.clear()
        self.submit_button.setText("Submit")
        self.update_button_states()

    def closeEvent(self, event):
        """ Overrides the default close event to delete the backup. """
        self.esp32_manager.delete_backup()
        event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = LockerGUI()
    window.show()
    # Disable the window until the bluetooth connection and sync is complete
    window.setEnabled(False) 
    sys.exit(app.exec())



    # closing and deleting 
    # 