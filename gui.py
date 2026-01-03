from PySide6.QtCore import (QCoreApplication, QMetaObject, QRect, Qt)
from PySide6.QtWidgets import (QApplication, QListWidgetItem, QComboBox, QCheckBox, QFrame, QLabel, QListView,
                               QListWidget, QMainWindow, QMenuBar, QPushButton, QStatusBar, QTableView, QWidget,
                               QHeaderView, QTableWidget)

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.setFixedSize(800, 560)
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.frame = QFrame(self.centralwidget)
        self.frame.setObjectName(u"frame")
        self.frame.setGeometry(QRect(0, 0, 791, 71))
        self.frame.setFrameShape(QFrame.Shape.StyledPanel)
        self.frame.setFrameShadow(QFrame.Shadow.Raised)
        """
        self.checkBoxAstro = QCheckBox(self.frame)
        self.checkBoxAstro.setObjectName(u"checkBox")
        self.checkBoxAstro.setGeometry(QRect(373, 25, 151, 24))
        self.checkBoxAstro.setChecked(True)
        self.meteoLabel = QLabel(self.frame)
        self.meteoLabel.setObjectName(u"label")
        self.meteoLabel.setGeometry(QRect(400, 10, 121, 16))
        self.checkBoxAdministrative = QCheckBox(self.frame)
        self.checkBoxAdministrative.setObjectName(u"checkBox_2")
        self.checkBoxAdministrative.setGeometry(QRect(373, 45, 161, 24))
        self.checkBoxAdministrative.setChecked(True)
        """
        self.yearComboBox = QComboBox(self.frame)
        self.yearComboBox.setObjectName(u"listView")
        self.yearComboBox.setGeometry(QRect(10, 20, 51, 31))
        self.monthComboBox = QComboBox(self.frame)
        self.monthComboBox.setObjectName(u"listView_2")
        self.monthComboBox.setGeometry(QRect(60, 20, 51, 31))
        self.dayComboBox = QComboBox(self.frame)
        self.dayComboBox.setObjectName(u"listView_3")
        self.dayComboBox.setGeometry(QRect(110, 20, 51, 31))
        self.measurComboBox = QComboBox(self.frame)
        self.measurComboBox.setObjectName(u"listWidget")
        self.measurComboBox.setGeometry(QRect(160, 20,211, 31))
        self.searchButton = QPushButton(self.frame)
        self.searchButton.setObjectName(u"pushButton")
        self.searchButton.setGeometry(QRect(620, 10, 161, 51))
        self.frame_2 = QFrame(self.centralwidget)
        self.frame_2.setObjectName(u"frame_2")
        self.frame_2.setGeometry(QRect(0, 80, 791, 461))
        self.frame_2.setFrameShape(QFrame.Shape.StyledPanel)
        self.frame_2.setFrameShadow(QFrame.Shadow.Raised)
        self.tableWidget = QTableWidget(self.frame_2)
        self.tableWidget.setObjectName(u"tableView")
        self.tableWidget.setGeometry(QRect(10, 10, 771, 441))
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 800, 33))
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(MainWindow)
        self.statusbar.setObjectName(u"statusbar")
        MainWindow.setStatusBar(self.statusbar)

        measurment_type = [
            ("Temperatura powietrza", 1),
            ("Temperatura gruntu", 2),
            ("Kierunek wiatru", 3),
            ("Średnia prędkość wiatru", 4),
            ("Maksymalna prędkość", 5),
            ("Suma opadu 10-minutowego", 6),
            ("Suma opadu dobowego", 7),
            ("Suma opadu godzinnego", 8),
            ("Wilgotność względna powietrza", 9),
            ("Największy poryw w okresie 10m", 10),
            ("Zapas wody w śniegu", 11)
        ]

        for name, id in measurment_type:
            self.measurComboBox.addItem(name, id)

        self.retranslateUi(MainWindow)

        QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"MainWindow", None))
        #self.checkBoxAstro.setText(QCoreApplication.translate("MainWindow", u"Dane astrologiczne", None))
        #self.meteoLabel.setText(QCoreApplication.translate("MainWindow", u"Dane meteorologiczne", None))
        #self.checkBoxAdministrative.setText(QCoreApplication.translate("MainWindow", u"Dane administracyjne", None))
        self.searchButton.setText(QCoreApplication.translate("MainWindow", u"Szukaj", None))

class MyApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.setWindowTitle("Aplikacja z danymi meteorologicznymi")

        self.ui.tableWidget.setColumnCount(4)

        self.ui.tableWidget.setHorizontalHeaderLabels([
            "Dzień",
            "Średnia pomiaru (dzień)",
            "Średnia pomiaru (noc)"
        ])

        header = self.ui.tableWidget.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

    def get_measurment_type(self):
        name = self.ui.measurComboBox.currentText()
        id = self.ui.measurComboBox.currentData()

        return id