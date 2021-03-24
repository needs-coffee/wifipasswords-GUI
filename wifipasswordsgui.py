#!/usr/bin/env python3
""" wifipasswords.gui.py
    GUI for viewing wifi passwords.
    Windows support only at present -macos and linux in progress.
    Creation date: 15-01-2021
    Modified date: 24-03-2021
    Dependencies: wifipasswords, pyqt5
"""

__copyright__ = "Copyright (C) 2021 Joe Campbell"
# GNU GENERAL PUBLIC LICENSE(GPLv3)

# This program is free software: you can redistribute it and / or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY
# without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see < https: // www.gnu.org/licenses/>.

__version__ = "0.1.0-beta"
__licence__ = "GPLv3"  # GNU General Public Licence v3

from wifipasswords import WifiPasswords
from wifipasswords import __version__ as wifipasswords_version

import os
import sys
import json
import locale
from datetime import datetime
import platform
from PyQt5.QtWidgets import (QCheckBox, QComboBox, QDialog, QFileDialog, QFrame, QGridLayout, QHBoxLayout, QLabel, QLineEdit, QApplication, QMessageBox, 
                            QPushButton, QTextEdit, QTableWidget, QTableWidgetItem, QVBoxLayout, QStyleFactory)
from PyQt5.QtGui import QColor, QFont, QIcon, QPalette
from PyQt5.QtCore import Qt, QThread, QObject,pyqtSignal

############################ CLASSES ############################

class WifiPasswordsGUI(QDialog):
    def __init__(self, data=None, parent=None):
        super().__init__(parent)
        
        self.original_palette = QApplication.palette()
        QApplication.setStyle(QStyleFactory.create('fusion'))
        QApplication.setPalette(self.original_palette)
        
        if self.detect_darkmode_in_windows():
            self.dark_mode = True
            self.set_dark_palette(self)
        else:
            self.dark_mode = False

        self.resize(800, 500)
        self.setWindowTitle(f'WifiPasswords-GUI {__version__}')
        self.setWindowIcon(QIcon(resource_path('icons8-flatcolor-unlock.ico')))

        self.placeholder_data = {
            'Loading': {'auth': ' ', 'psk': ' ', 'metered': False, 'macrandom': 'Disabled'}
        }
        
        if data == None:
            self.data = self.placeholder_data
        else:
            self.data = data

        self.create_table_group()
        self.run_get_data_thread()

        self.create_button_group()
        self.buttons_disabled(True)

        main = QGridLayout()
        main.setContentsMargins(3, 3, 3, 3)
        self.setContentsMargins(3, 3, 3, 3)
        main.addWidget(self.table_group, 1, 0)
        main.addWidget(self.button_group, 2, 0)
        self.setLayout(main)


    def run_get_data_thread(self):
        """
        get data in separate thread. use qthread as is threadsafe in pyside2.
        """
        self.thread = QThread()
        self.worker = GetDataWorker()
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.finished_sig.connect(self.thread.quit)
        self.worker.finished_sig.connect(self.worker.deleteLater)
        self.worker.finished_sig.connect(self.thread.deleteLater)
        self.worker.finished_sig.connect(lambda: self.buttons_disabled(False))
        self.worker.data_sig.connect(self.set_table_data)
        self.thread.start()


    def set_table_data(self,data,connected):
        """
        set the data for the table afexoter init.\n
        also a callback for the Qthread for getting data.
        """
        self.table.set_data(data,connected)


    def create_table_group(self):
        self.table_group = QFrame()
        self.table = TableView(self.data,self.dark_mode)
        layout = QVBoxLayout()
        layout.addWidget(self.table)
        self.table_group.setLayout(layout)


    def create_button_group(self):
        self.button_group = QFrame()
        self.currently_visible_button = QPushButton(
            'Currently Visible Networks')
        self.currently_visible_button.clicked.connect(
            self.currently_visible_on_click)

        self.exit_button = QPushButton('Exit')
        self.exit_button.clicked.connect(self.exit_on_click)
        self.exit_button.setDefault(True)

        self.save_data_button = QPushButton('Save to file..')
        self.save_data_button.clicked.connect(self.save_data_on_click)

        self.dns_button = QPushButton('Current DNS config')
        self.dns_button.clicked.connect(self.dns_button_on_click)

        self.settings_button = QPushButton('Settings/About')
        self.settings_button.clicked.connect(self.settings_and_about_on_click)

        layout = QHBoxLayout()
        layout.addWidget(self.currently_visible_button)
        layout.addWidget(self.dns_button)
        layout.addWidget(self.save_data_button)
        layout.addWidget(self.settings_button)
        layout.addWidget(self.exit_button)
        self.button_group.setLayout(layout)


    def buttons_disabled(self, disabled):
        self.currently_visible_button.setDisabled(disabled)
        self.dns_button.setDisabled(disabled)
        self.save_data_button.setDisabled(disabled)


    def currently_visible_on_click(self):
        dia = VisibleNetworksDialog(self)
        if self.dark_mode:
            self.set_dark_palette(dia)
        dia.exec_()


    def dns_button_on_click(self):
        dia = DNSDialog(self)
        if self.dark_mode:
            self.set_dark_palette(dia)
        dia.exec_()


    def save_data_on_click(self):
        dia = SaveData(self, self.table.data, self.dark_mode)
        if self.dark_mode:
            self.set_dark_palette(dia)
        dia.exec_()


    def settings_and_about_on_click(self):
        dia = SettingsAndAboutDialog(self)
        if self.dark_mode:
            self.set_dark_palette(dia)
        dia.exec_()


    @staticmethod
    def exit_on_click():
        sys.exit(0)


    @staticmethod
    def set_dark_palette(app) -> None:
        """
        sets a dark mode palette on the specified widget.\n
        # https://gist.github.com/lschmierer/443b8e21ad93e2a2d7eb\n
        # source of dark theme code, slightly modified
        """
        dark_palette = QPalette()
        dark_palette.setColor(QPalette.Window, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.WindowText, Qt.white)
        dark_palette.setColor(QPalette.Base, QColor(25, 25, 25))
        dark_palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.ToolTipBase, Qt.white)
        dark_palette.setColor(QPalette.ToolTipText, Qt.white)
        dark_palette.setColor(QPalette.Text, Qt.white)
        dark_palette.setColor(QPalette.Button, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.ButtonText, Qt.white)
        dark_palette.setColor(QPalette.BrightText, Qt.red)
        dark_palette.setColor(QPalette.Link, QColor(42, 130, 218))
        dark_palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
        dark_palette.setColor(QPalette.HighlightedText, Qt.black)
        dark_palette.setColor(QPalette.Disabled, QPalette.ButtonText, Qt.gray)

        app.setPalette(dark_palette)


    @staticmethod
    def detect_darkmode_in_windows() -> bool:
        """
        For detecting windows systemwide theme to follow.\n
        returns a bool value - True if dark mode is set.\n
        source: https://stackoverflow.com/questions/65294987/detect-os-dark-mode-in-python
        """
        try:
            import winreg
        except ImportError:
            return False
        registry = winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER)
        reg_keypath = r'SOFTWARE\Microsoft\Windows\CurrentVersion\Themes\Personalize'
        try:
            reg_key = winreg.OpenKey(registry, reg_keypath)
        except FileNotFoundError:
            return False

        for i in range(1024):
            try:
                value_name, value, _ = winreg.EnumValue(reg_key, i)
                if value_name == 'AppsUseLightTheme':
                    return value == 0
            except OSError:
                break
        return False


class TableView(QTableWidget):

    def __init__(self, data, dark_mode, connected_networks=[], *args):
        QTableWidget.__init__(self, *args)
        horHeaders = ["Network", "Auth", "PSK", "Metered?","Random MAC?"]
        
        self.setColumnCount(len(horHeaders))
        self.setHorizontalHeaderLabels(horHeaders)
        self.horizontalHeader().setStretchLastSection(True)
        
        self.dark_mode = dark_mode
        self.data = data
        self.connected_networks = connected_networks
        self.set_data(self.data)
        # self.resizeColumnsToContents()
        self.setColumnWidth(0, 230)
        self.setColumnWidth(1, 100)
        self.setColumnWidth(2, 250)
        self.setColumnWidth(3, 60)
        self.setColumnWidth(4, 80)

    def set_data(self, data,connected_networks=[]):
        self.setRowCount(len(data))
        self.setSortingEnabled(False)
        
        self.data = data
        self.connected_networks = connected_networks

        for num, (network, values) in enumerate(self.data.items()):
            if values['metered']:
                is_metered = "Yes"
            else:
                is_metered = ''

            if values['macrandom'] == 'Disabled':
                mac_is_random = ''
            else:
                mac_is_random = values['macrandom']

            if self.dark_mode:
                font_color = Qt.green
            else:
                font_color = Qt.blue

            net_formatted = QTableWidgetItem(network)
            auth_formatted = QTableWidgetItem(values['auth'])
            psk_formatted = QTableWidgetItem(values['psk'])
            metered_formatted = QTableWidgetItem(is_metered)
            mac_is_random_formatted = QTableWidgetItem(mac_is_random)

            if network in self.connected_networks:
                net_formatted.setForeground(font_color) 
                auth_formatted.setForeground(font_color) 
                psk_formatted.setForeground(font_color) 
                metered_formatted.setForeground(font_color) 
                mac_is_random_formatted.setForeground(font_color) 

            self.setItem(num, 0, net_formatted)
            self.setItem(num, 1, auth_formatted)
            self.setItem(num, 2, psk_formatted)
            self.setItem(num, 3, metered_formatted)
            self.setItem(num, 4, mac_is_random_formatted)

        self.resizeRowsToContents()
        self.setSortingEnabled(True)


class SettingsAndAboutDialog(QDialog):
    """
    settings and about dialog. \n
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        self.resize(200, 50)
        self.setWindowTitle('Settings and About')

        layout = QVBoxLayout()

        self.wifipasswords_version_label = QLabel("wifipaswords version          : {}\n".format(wifipasswords_version))
        self.gui_version_label = QLabel("wifipasswords GUI version : {}\n".format(__version__))

        close_button = QPushButton('Close')
        close_button.clicked.connect(self.accept)

        # layout.addWidget(self.title_label)
        layout.addWidget(self.wifipasswords_version_label)
        layout.addWidget(self.gui_version_label)
        layout.addSpacing(10)
        layout.addWidget(close_button)
        self.setLayout(layout)


class SaveData(QDialog):
    def __init__(self, parent, data, dark_mode):
        super().__init__(parent)

        # set the default save directory to the users desktop.
        self.save_directory = os.path.join(
            os.environ['USERPROFILE'], 'Desktop')
        
        self.json_filename = 'networks_data.json'
        self.wpa_supplicant_filename = 'wpa_supplicant.conf'
        
        # Get current windows locale
        self.detected_country_code = locale.getdefaultlocale()[0].split('_')[1]
        self.current_country_code = self.detected_country_code

        #https: // en.wikipedia.org/wiki/ISO_3166-1_alpha-2
        # all 249 (242 original and 7 reasigned) currently in ISO standard.
        self.iso_country_codes_alpha2 = ['AD', 'AE', 'AF', 'AG', 'AI', 'AL', 'AM', 'AO', 'AQ', 'AR', 'AS', 'AT', 'AU', 'AW', 'AX', 'AZ', 'BA', 
                            'BB', 'BD', 'BE', 'BF', 'BG', 'BH', 'BI', 'BJ', 'BL', 'BM', 'BN', 'BO', 'BQ', 'BR', 'BS', 'BT', 'BV', 'BW', 'BY', 
                            'BZ', 'CA', 'CC', 'CD', 'CF', 'CG', 'CH', 'CI', 'CK', 'CL', 'CM', 'CN', 'CO', 'CR', 'CU', 'CV', 'CW', 'CX', 'CY', 
                            'CZ', 'DE', 'DJ', 'DK', 'DM', 'DO', 'DZ', 'EC', 'EE', 'EG', 'EH', 'ER', 'ES', 'ET', 'FI', 'FJ', 'FK', 'FM', 'FO', 
                            'FR', 'GA', 'GB', 'GD', 'GE', 'GF', 'GG', 'GH', 'GI', 'GL', 'GM', 'GN', 'GP', 'GQ', 'GR', 'GS', 'GT', 'GU', 'GW', 
                            'GY', 'HK', 'HM', 'HN', 'HR', 'HT', 'HU', 'ID', 'IE', 'IL', 'IM', 'IN', 'IO', 'IQ', 'IR', 'IS', 'IT', 'JE', 'JM', 
                            'JO', 'JP', 'KE', 'KG', 'KH', 'KI', 'KM', 'KN', 'KP', 'KR', 'KW', 'KY', 'KZ', 'LA', 'LB', 'LC', 'LI', 'LK', 'LR', 
                            'LS', 'LT', 'LU', 'LV', 'LY', 'MA', 'MC', 'MD', 'ME', 'MF', 'MG', 'MH', 'MK', 'ML', 'MM', 'MN', 'MO', 'MP', 'MQ', 
                            'MR', 'MS', 'MT', 'MU', 'MV', 'MW', 'MX', 'MY', 'MZ', 'NA', 'NC', 'NE', 'NF', 'NG', 'NI', 'NL', 'NO', 'NP', 'NR', 
                            'NU', 'NZ', 'OM', 'PA', 'PE', 'PF', 'PG', 'PH', 'PK', 'PL', 'PM', 'PN', 'PR', 'PS', 'PT', 'PW', 'PY', 'QA', 'RE', 
                            'RO', 'RS', 'RU', 'RW', 'SA', 'SB', 'SC', 'SD', 'SE', 'SG', 'SH', 'SI', 'SJ', 'SK', 'SL', 'SM', 'SN', 'SO', 'SR', 
                            'SS', 'ST', 'SV', 'SX', 'SY', 'SZ', 'TC', 'TD', 'TF', 'TG', 'TH', 'TJ', 'TK', 'TL', 'TM', 'TN', 'TO', 'TR', 'TT', 
                            'TV', 'TW', 'TZ', 'UA', 'UG', 'UM', 'US', 'UY', 'UZ', 'VA', 'VC', 'VE', 'VG', 'VI', 'VN', 'VU', 'WF', 'WS', 'YE', 
                            'YT', 'ZA', 'ZM', 'ZW']

        self.data = data
        self.dark_mode = dark_mode

        self.resize(600, 100)
        self.setWindowTitle('Save')

        file_path_label = QLabel('Select save directory:')

        self.file_path_textbox = QLineEdit()
        self.file_path_textbox.setText(self.save_directory)
        self.file_path_textbox.textChanged.connect(self.save_path_changed)

        file_path_selector_button = QPushButton('..')
        file_path_selector_button.setMaximumWidth(40)
        file_path_selector_button.clicked.connect(self.select_directory)

        self.save_open_networks_checkbox = QCheckBox("Save open networks?")
        self.save_open_networks_checkbox.setChecked(True)

        save_json_button = QPushButton('Save as JSON')
        save_json_button.clicked.connect(self.save_json_on_click)

        save_wpa_supplicant = QPushButton('Save as WPA Supplicant')
        save_wpa_supplicant.clicked.connect(
            self.save_wpa_supplicant_on_click)

        locale_combo_label = QLabel('Locale:')
        self.locale_combo = QComboBox()
        self.locale_combo.addItems(self.iso_country_codes_alpha2)
        self.locale_combo.setCurrentText(self.current_country_code)
        self.locale_combo.currentTextChanged.connect(self.locale_change)

        #dummy button for spacing, is hidden
        dummy_button = QPushButton()
        dummy_button.setFlat(True)
        dummy_button.setDisabled(True)

        close_button = QPushButton('Close')
        close_button.clicked.connect(self.accept)

        head_layout = QHBoxLayout()
        head_layout.addWidget(file_path_label)

        top_layout = QHBoxLayout()
        top_layout.addWidget(self.file_path_textbox)
        top_layout.addWidget(file_path_selector_button)

        mid_layout = QHBoxLayout()
        mid_layout.addWidget(self.save_open_networks_checkbox)
        mid_layout.addWidget(save_json_button)
        mid_layout.addWidget(save_wpa_supplicant)

        bottom_left_layout = QHBoxLayout()
        bottom_left_layout.addWidget(locale_combo_label)
        bottom_left_layout.addWidget(self.locale_combo)
        bottom_left_layout.addSpacing(100)

        bottom_layout = QHBoxLayout()
        bottom_layout.addLayout(bottom_left_layout)
        bottom_layout.addWidget(dummy_button)
        bottom_layout.addWidget(close_button)

        layout = QVBoxLayout()
        layout.addLayout(head_layout)
        layout.addSpacing(5)
        layout.addLayout(top_layout)
        layout.addSpacing(10)
        layout.addLayout(mid_layout)
        layout.addSpacing(10)
        layout.addLayout(bottom_layout)
        self.setLayout(layout)


    def locale_change(self,value):
        # print(f'combo box changed to {value}')
        self.current_country_code = value


    def select_directory(self):
        file_dialog = QFileDialog(self, 'Directory', self.save_directory)
        file_dialog.setFileMode(QFileDialog.DirectoryOnly)
        if file_dialog.exec_() == QDialog.Accepted:
            path = file_dialog.selectedFiles()[0]
            self.file_path_textbox.setText(path)


    def save_path_changed(self):
        self.save_directory = self.file_path_textbox.text()

    def save_json_on_click(self):
        if not os.path.isdir(self.save_directory):
            alert = QMessageBox()
            alert.setText(f'{self.save_directory} is not a directory!')
            if self.dark_mode:
                self.set_dark_pallete(alert)
            alert.exec_()
            return
        else:
            if os.path.exists(os.path.join(self.save_directory, self.json_filename)):
                overwrite_alert = QMessageBox()
                overwrite_alert.setText(
                    f'{os.path.join(self.save_directory, "networks_data.json")} exists! Overwrite?')
                overwrite_alert.setWindowTitle('Overwrite?')
                overwrite_alert.setStandardButtons(QMessageBox.Yes)
                overwrite_alert.addButton(QMessageBox.No)
                overwrite_alert.setDefaultButton(QMessageBox.No)

                if self.dark_mode:
                    self.set_dark_pallete(overwrite_alert)

                if overwrite_alert.exec_() == QMessageBox.No:
                    return

            with open(os.path.join(self.save_directory, self.json_filename),'w') as fout:
                json.dump(self.data, fout)
            alert = QMessageBox()
            alert.setText(
                f'JSON saved to networks_data.json!\nPath: {os.path.join(self.save_directory,self.json_filename)}')
            if self.dark_mode:
                self.set_dark_pallete(alert)
            alert.exec_()


    def save_wpa_supplicant_on_click(self):
        if not os.path.isdir(self.save_directory):
            alert = QMessageBox()
            alert.setText(f'{self.save_directory} is not a directory!')
            if self.dark_mode:
                self.set_dark_pallete(alert)
            alert.exec_()
            return
        else:
            if os.path.exists(os.path.join(self.save_directory, self.wpa_supplicant_filename)):
                overwrite_alert = QMessageBox()
                overwrite_alert.setText(
                    f'{os.path.join(self.save_directory, self.wpa_supplicant_filename)} exists! Overwrite?')
                overwrite_alert.setWindowTitle('Overwrite?')
                overwrite_alert.setStandardButtons(QMessageBox.Yes)
                overwrite_alert.addButton(QMessageBox.No)
                overwrite_alert.setDefaultButton(QMessageBox.No)

                if self.dark_mode:
                    self.set_dark_pallete(overwrite_alert)

                if overwrite_alert.exec_() == QMessageBox.No:
                    return

            with open(os.path.join(self.save_directory, self.wpa_supplicant_filename), 'w', newline='\n') as fout:
                fout.write(f'# Generated by wifipasswords {__version__}\n')
                fout.write(f'# Created: {datetime.today()}\n')
                fout.write(
                    f'# Device: {platform.uname().system} {platform.uname().version} - {platform.uname().node}\n')
                fout.write(f'# Detected country code: {self.current_country_code}\n')
                fout.write('\n')
                fout.write(
                    'ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev\n')
                fout.write('update_config=1\n')
                fout.write(f'country={self.current_country_code}\n')
                fout.write('\n')
                fout.write('# ######## WPA ########\n')
                for key, n in self.data.items():
                    if(n['auth'] == 'WPA2-Personal'):
                        fout.write('network={\n')
                        fout.write('\tssid="{}"\n'.format(key))
                        fout.write('\tpsk="{}"\n'.format(n['psk']))
                        fout.write('\tkey_mgmt=WPA-PSK\n')
                        fout.write('\tid_str="{}"\n'.format(key))
                        fout.write('}\n')
                fout.write('\n')
                if self.save_open_networks_checkbox.isChecked():
                    fout.write('# ######## OPEN ########\n')
                    for key, n in self.data.items():
                        if(n['auth'] == '' or n['auth'] == 'Open'):
                            fout.write('network={\n')
                            fout.write('\tssid="{}"\n'.format(key))
                            fout.write('\tkey_mgmt=NONE\n')
                            fout.write('\tid_str="{}"\n'.format(key))
                            fout.write('\tpriority=-999\n')
                            fout.write('}\n')

            alert = QMessageBox()
            alert.setText(
                f'Networks saved to {self.wpa_supplicant_filename}!\nPath: {os.path.join(self.save_directory,self.wpa_supplicant_filename)}')
            if self.dark_mode:
                self.set_dark_pallete(alert)
            alert.exec_()


    @staticmethod
    def set_dark_pallete(app):
        # https://gist.github.com/lschmierer/443b8e21ad93e2a2d7eb
        # source of dark theme code
        dark_palette = QPalette()
        dark_palette.setColor(QPalette.Window, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.WindowText, Qt.white)
        dark_palette.setColor(QPalette.Base, QColor(25, 25, 25))
        dark_palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.ToolTipBase, Qt.white)
        dark_palette.setColor(QPalette.ToolTipText, Qt.white)
        dark_palette.setColor(QPalette.Text, Qt.white)
        dark_palette.setColor(QPalette.Button, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.ButtonText, Qt.white)
        dark_palette.setColor(QPalette.BrightText, Qt.red)
        dark_palette.setColor(QPalette.Link, QColor(42, 130, 218))
        dark_palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
        dark_palette.setColor(QPalette.HighlightedText, Qt.black)
        dark_palette.setColor(QPalette.Disabled, QPalette.ButtonText, Qt.gray)

        app.setPalette(dark_palette)


class VisibleNetworksDialog(QDialog):
    """
    dialog for showing the currently visible networks.
    """
    def __init__(self, parent=None):
        super().__init__(parent)

        self.resize(400, 500)
        self.setWindowTitle('Visible Networks')

        layout = QVBoxLayout()

        self.title_label = QLabel("Currently Visible WiFi Networks:")
        self.footnote_label = QLabel("Note:\n"
                            "Only the currently connected WiFi network may be visible.\n"
                            "To show all networks disconnect from the current network and retry.")

        close_button = QPushButton('Close')
        close_button.clicked.connect(self.accept)
        text_box = QTextEdit()
        text_box.setPlainText(wifipw.get_visible_networks(False))

        layout.addWidget(self.title_label)
        layout.addWidget(text_box)
        layout.addWidget(self.footnote_label)
        layout.addSpacing(10)
        layout.addWidget(close_button)
        self.setLayout(layout)


class DNSDialog(QDialog):
    """
    Child dialog that shows the dns config.
    """
    def __init__(self, parent=None):
        super().__init__(parent)

        self.resize(400, 500)
        self.setWindowTitle('DNS Config')
        
        layout = QVBoxLayout()
        self.label = QLabel("Current DNS config:")
        
        close_button = QPushButton('Close')
        close_button.clicked.connect(self.accept)
        
        text_box = QTextEdit()
        text_box.setPlainText(wifipw.get_dns_config())

        layout.addWidget(self.label)
        layout.addWidget(text_box)
        layout.addSpacing(10)
        layout.addWidget(close_button)
        self.setLayout(layout)


class GetDataWorker(QObject):
    finished_sig = pyqtSignal()
    data_sig = pyqtSignal(dict,list)

    def run(self):
        # net_data = wifipw.get_passwords_dummy(2,20)
        net_data = wifipw.get_passwords()
        connected = wifipw.get_currently_connected_ssids()
        self.data_sig.emit(net_data,connected)
        self.finished_sig.emit()


############################ MAIN APPLICATON ############################


#https://stackoverflow.com/questions/7674790/bundling-data-files-with-pyinstaller-onefile
# needed for packaging the icon using pyinstaller
# edit the spec file to add the data to the exe i.e.
# a = Analysis(['wifipasswords.gui.py'],
#              datas=[('icons8-flatcolor-unlock.ico', '.')],

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    base_path = getattr(
        sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)

if __name__ == "__main__":
    wifipw = WifiPasswords()    
    app = QApplication([])
    gui = WifiPasswordsGUI()
    gui.show()
    sys.exit(app.exec_())
