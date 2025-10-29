import sys
import re
import random
import string
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QGridLayout, QHBoxLayout,
    QLineEdit, QLabel, QPushButton, QGroupBox, QFormLayout, QMessageBox
)
from PyQt6.QtCore import pyqtSignal, QTimer
from PyQt6.QtGui import QIntValidator
from wifi_service import ESP32detailsManager, ESP32_IP
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
        self.setGeometry(200, 200, 500, 550) # Increased height for new fields

        # State management
        self.locker_widgets = {}
        self.selected_locker_id = None
        self.is_name_valid = False
        self.is_email_valid = False
        self.is_job_number_valid = False
        self.is_password_valid = False # New state for password validation

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
        Connects to the ESP32 and performs initial sync.
        """
        QMessageBox.information(self, "Connecting...", "Attempting to connect to the ESP32. Please wait...")
        
        self.esp32_manager.make_backup()
        isSynced = self.esp32_manager.sync_from_esp32()
        if not isSynced:
            QMessageBox.critical(self, "Connection Error", "Could not sync with ESP32!")
            # self.close()
            # return

        self.load_initial_locker_states()
        self.setEnabled(True)

    def create_user_input_group(self):
        user_groupbox = QGroupBox("User Information")
        layout = QFormLayout()
        
        # Name
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Enter user's full name")
        self.name_input.textChanged.connect(self.validate_name)
        layout.addRow(QLabel("Name:"), self.name_input)
        
        # Email
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Enter a valid email address")
        self.email_input.textChanged.connect(self.validate_email)
        layout.addRow(QLabel("Email:"), self.email_input)

        # Job Number
        self.job_number_input = QLineEdit()
        self.job_number_input.setPlaceholderText("Enter job number")
        self.job_number_input.setValidator(QIntValidator())
        self.job_number_input.textChanged.connect(self.validate_job_number)
        layout.addRow(QLabel("Job Number:"), self.job_number_input)

        # Password
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Enter or generate a password")
        self.password_input.textChanged.connect(self.validate_password)
        
        generate_pass_button = QPushButton("Generate")
        generate_pass_button.clicked.connect(self.generate_password)
        
        password_layout = QHBoxLayout()
        password_layout.addWidget(self.password_input)
        password_layout.addWidget(generate_pass_button)
        layout.addRow(QLabel("Password:"), password_layout)

        user_groupbox.setLayout(layout)
        self.main_layout.addWidget(user_groupbox)

    def generate_password(self):
        """Generates a random 6-digit passcode and sets it in the password input."""
        passcode = ''.join(random.choices(string.digits, k=6))
        self.password_input.setText(passcode)

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
        actions_groupbox = QGroupBox("Actions")
        button_layout = QGridLayout()

        # Occupy buttons
        self.make_occupy_email_button = QPushButton("Make Occupy & Email")
        self.make_occupy_email_button.clicked.connect(lambda: self.run_occupy_process(send_email=True))
        button_layout.addWidget(self.make_occupy_email_button, 0, 0)

        self.make_occupy_no_email_button = QPushButton("Make Occupy (No Email)")
        self.make_occupy_no_email_button.clicked.connect(lambda: self.run_occupy_process(send_email=False))
        button_layout.addWidget(self.make_occupy_no_email_button, 0, 1)

        # Unlock buttons
        self.unlock_button = QPushButton("Unlock")
        self.unlock_button.clicked.connect(lambda: self.run_unlock_process())
        button_layout.addWidget(self.unlock_button, 1, 0)

        actions_groupbox.setLayout(button_layout)
        
        # --- CORRECTED LINE ---
        # Add the entire groupbox widget to the main layout
        self.main_layout.addWidget(actions_groupbox) 

        # This call was also in the wrong place. It should be inside the QHBoxLayout, not here.
        # self.main_layout.addLayout(button_layout) # This was the old, incorrect line
        
        self.update_button_states() # Initial state

  

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

    def validate_password(self, text: str):
        self.is_password_valid = len(text.strip()) >= 4 # Example: require at least 4 digits
        self.password_input.setStyleSheet("border: 2px solid #388E3C;" if self.is_password_valid else "border: 2px solid #D32F2F;")
        self.update_button_states()

    def update_button_states(self):
        locker_is_selected = self.selected_locker_id is not None
        if not locker_is_selected:
            self.make_occupy_email_button.setEnabled(False)
            self.make_occupy_no_email_button.setEnabled(False)
            self.unlock_button.setEnabled(False)
            self.unlock_no_delete_button.setEnabled(False)
            return

        is_occupied = self.locker_widgets[self.selected_locker_id].is_occupied
        all_user_fields_valid = self.is_name_valid and self.is_email_valid and self.is_job_number_valid and self.is_password_valid

        # Enable occupy buttons only if a locker is selected, it's NOT occupied, and all fields are valid.
        self.make_occupy_email_button.setEnabled(locker_is_selected and not is_occupied and all_user_fields_valid)
        self.make_occupy_no_email_button.setEnabled(locker_is_selected and not is_occupied and all_user_fields_valid)

        # Enable unlock buttons only if a locker is selected and it IS occupied.
        self.unlock_button.setEnabled(locker_is_selected and is_occupied)
        self.unlock_no_delete_button.setEnabled(locker_is_selected and is_occupied)

    def run_unlock_process(self):
        locker_id = self.selected_locker_id
        if not locker_id: return
        
        action_text = "Unlock & Clear Data for"
        reply = QMessageBox.question(self, "Confirm Unlock", f"Are you sure you want to<br><b>{action_text}</b><br>Locker <b>{locker_id}</b>?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel)
        if reply == QMessageBox.StandardButton.Cancel: return

        try:
            self.esp32_manager.send_unlock_signal(int(locker_id))
            QMessageBox.information(self, "Signal Sent", f"Unlock signal sent to locker {locker_id}.")
        except Exception as e:
            QMessageBox.critical(self, "Signal Failed", f"Failed to send unlock signal to ESP32: {e}")
            return
        
        
    def run_occupy_process(self, send_email: bool):
        locker_id = self.selected_locker_id
        name = self.name_input.text().strip()
        email = self.email_input.text().strip()
        job_number = self.job_number_input.text().strip()
        password = self.password_input.text().strip()

        action_text = "and send email" if send_email else "without sending email"
        reply = QMessageBox.question(self, "Confirm Occupy", f"<b>Name:</b> {name}<br><b>Locker:</b> {locker_id}<br><b>Action:</b> Occupy {action_text}.<br><br>Proceed?", QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel)
        if reply == QMessageBox.StandardButton.Cancel: return
        
        self.make_occupy_email_button.setEnabled(False)
        self.make_occupy_no_email_button.setEnabled(False)
        
        # 1. Update local database
        if not locker_logic.assign_locker(locker_id, name, email, password):
            QMessageBox.critical(self, "Error", "Failed to update local database.")
            self.reset_ui_state()
            return
        
        # 2. Sync to ESP32
        if not self.esp32_manager.send_occupy_signal(locker_id,password):
            QMessageBox.warning(self, "Sync Failed", "Locker assigned locally, but ESP32 sync failed. Rolling back.")
            locker_logic.release_locker(locker_id) # Rollback local change
            self.reset_ui_state()
            return

        # 3. Send email (optional)
        if send_email:
            if not send_automated_email(self, email, job_number, locker_id, password):
                QMessageBox.warning(self, "Email Failed", "Locker assigned, ESP32 sync success, but email failed. Rolling back.")
                locker_logic.release_locker(locker_id) # Rollback local
                self.esp32_manager.update_esp32() # Attempt to sync rollback
                self.reset_ui_state()
                return

        QMessageBox.information(self, "Success", f"Locker {locker_id} assigned to {name}.")
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
        self.job_number_input.clear()
        self.password_input.clear()
        self.update_button_states()

    def closeEvent(self, event):
        """ Overrides the default close event to delete the backup. """
        self.esp32_manager.delete_backup()
        event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = LockerGUI()
    window.show()
    # Disable the window until the connection and sync is complete
    window.setEnabled(False) 
    sys.exit(app.exec())