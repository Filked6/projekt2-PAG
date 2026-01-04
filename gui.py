from PySide6.QtCore import QCoreApplication, QMetaObject, QRect, Qt
from PySide6.QtWidgets import (QApplication, QComboBox, QFrame, QLabel,
                               QMainWindow, QMenuBar, QPushButton, QStatusBar,
                               QTableWidget, QWidget, QHeaderView)
from read_meteo import *


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName(u"MainWindow")
        MainWindow.setFixedSize(800, 560)
        self.centralwidget = QWidget(MainWindow)
        self.frame = QFrame(self.centralwidget)
        self.frame.setGeometry(QRect(0, 0, 791, 71))
        self.frame.setFrameShape(QFrame.Shape.StyledPanel)

        self.yearComboBox = QComboBox(self.frame)
        self.yearComboBox.setGeometry(QRect(10, 20, 71, 31))

        self.monthComboBox = QComboBox(self.frame)
        self.monthComboBox.setGeometry(QRect(85, 20, 60, 31))

        self.voivodeshipComboBox = QComboBox(self.frame)
        self.voivodeshipComboBox.setGeometry(QRect(150, 20, 150, 31))

        self.measurComboBox = QComboBox(self.frame)
        self.measurComboBox.setGeometry(QRect(305, 20, 210, 31))

        self.searchButton = QPushButton(self.frame)
        self.searchButton.setGeometry(QRect(620, 10, 161, 51))

        self.frame_2 = QFrame(self.centralwidget)
        self.frame_2.setGeometry(QRect(0, 80, 791, 461))
        self.tableWidget = QTableWidget(self.frame_2)
        self.tableWidget.setGeometry(QRect(10, 10, 771, 441))

        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(MainWindow)
        MainWindow.setStatusBar(self.statusbar)

        voivodeships = [
            ("Dolnośląskie", "02"), ("Kujawsko-pomorskie", "04"),
            ("Lubelskie", "06"), ("Lubuskie", "08"),
            ("Łódzkie", "10"), ("Małopolskie", "12"),
            ("Mazowieckie", "14"), ("Opolskie", "16"),
            ("Podkarpackie", "18"), ("Podlaskie", "20"),
            ("Pomorskie", "22"), ("Śląskie", "24"),
            ("Świętokrzyskie", "26"), ("Warmińsko-mazurskie", "28"),
            ("Wielkopolskie", "30"), ("Zachodniopomorskie", "32")
        ]
        for name, teryt in sorted(voivodeships):
            self.voivodeshipComboBox.addItem(name, teryt)

        measurement_types = [
            ("Temperatura powietrza", 1), ("Temperatura gruntu", 2),
            ("Kierunek wiatru", 3), ("Średnia prędkość wiatru", 4),
            ("Maksymalna prędkość", 5), ("Suma opadu 10-minutowego", 6),
            ("Suma opadu dobowego", 7), ("Suma opadu godzinnego", 8),
            ("Wilgotność względna powietrza", 9),
            ("Największy poryw w okresie 10m", 10), ("Zapas wody w śniegu", 11)
        ]
        for name, id in measurement_types:
            self.measurComboBox.addItem(name, id)

        self.retranslateUi(MainWindow)
        QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"Meteo Data Browser", None))
        self.searchButton.setText(QCoreApplication.translate("MainWindow", u"Szukaj", None))


class MyApp(QMainWindow):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.ui.tableWidget.setColumnCount(3)
        self.ui.tableWidget.setHorizontalHeaderLabels(["Stacja", "Średnia (dzień)", "Średnia (noc)"])
        self.ui.tableWidget.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        self.dictYearMonths = get_available_months(self.db)

        self.ui.yearComboBox.currentTextChanged.connect(self.update_months)

        self.ui.yearComboBox.clear()
        for year in sorted(self.dictYearMonths.keys(), reverse=True):
            self.ui.yearComboBox.addItem(year)

        if self.ui.yearComboBox.count() > 0:
            self.update_months(self.ui.yearComboBox.currentText())

    def update_months(self, selected_year):
        self.ui.monthComboBox.clear()
        if selected_year in self.dictYearMonths:
            for month in sorted(self.dictYearMonths[selected_year], reverse=True):
                self.ui.monthComboBox.addItem(month)

    def get_measurement_type(self):
        return self.ui.measurComboBox.currentData()

    def get_selected_voivodeship(self):
        return self.ui.voivodeshipComboBox.currentData()
