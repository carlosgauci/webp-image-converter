import sys
import webbrowser
from PyQt5.QtWidgets import QMainWindow, QApplication, QWidget, QLabel, QSizePolicy, QHBoxLayout, QPushButton, QVBoxLayout, QFileDialog, QSpacerItem, QFormLayout, QSlider, QLineEdit, QStatusBar, QGridLayout
from PyQt5.QtCore import Qt, QPoint, QEvent, pyqtSignal, QObject, QThread, QPointF, QFile, QIODevice, QTextStream
from PyQt5.QtGui import QFont, QFontDatabase, QGuiApplication, QCursor, QIcon, QPixmap
from PIL import Image
from pathlib import Path
from time import sleep
import os
import resources

basedir = os.path.dirname(__file__)

if hasattr(Qt, 'AA_EnableHighDpiScaling'):
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
if hasattr(Qt, 'AA_UseHighDpiPixmaps'):
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)


class Worker(QObject):
    def __init__(self, input:str, output:str, imageQuality:int, delay:str):
        super().__init__()
        self.__input = input
        self.__output = output
        self.__imageQuality = imageQuality
        
        try:
            self.__delay = float(delay)
        except: self.__delay = 0
            
        
    finished = pyqtSignal()
    progress = pyqtSignal(str, str)
    
    def uniqueFilename(self, f):
        fnew = f
        root, ext = os.path.splitext(f)
        i = 0
        while os.path.exists(fnew):
            i += 1
            fnew = '%s_%i%s' % (root, i, ext)
        return fnew


    def convertImages(self):
        files = (p.resolve() for p in Path(self.__input).glob("**/*") if p.suffix.lower() in {".png", ".jpg", ".jpeg", ".jp2", ".jpx", ".j2k", ".j2c", ".jpe", ".jps", ".gif", ".jfif", ".ico", ".tif", ".tiff",".bmp", ".dng", ".pcx"})
        i=1
        for file in files:
            try:
                self.progress.emit(str(i), str(file.name))
                destination = f"{os.path.join(self.__output, file.stem)}.webp"
                uniqueDestination = self.uniqueFilename(destination)

                image = Image.open(file) 
                image.save(uniqueDestination, format="webp", quality=self.__imageQuality)  
                i+=1
                
                if self.__delay > 0:
                    sleep(self.__delay)
            except: pass
        self.finished.emit()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.setWindowFlags(Qt.FramelessWindowHint|Qt.WindowMaximizeButtonHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowTitle("WebP Image Converter")
        self.resize(500,420)
        self.mainWidget = QWidget()
        self.mainWidget.setObjectName("mainWidget")
        self.setCentralWidget(self.mainWidget)
        
        QFontDatabase.addApplicationFont(":/Lato-Regular.ttf")
        font = QFont("Lato")
        
        self.inputFolder = ""
        self.outputFolder = ""
        self.imageQuality = 80
        self.delay = "0"
        self.prevGeo = self.geometry()
        
        self.statusBar = QStatusBar()
        self.statusBar.setObjectName("statusbar")
        self.setStatusBar(self.statusBar)
        
        # Header btns
        self.closeBtn = QPushButton("x", clicked = self.close)
        self.closeBtn.setObjectName("headerBtn")
        self.minimizeBtn = QPushButton("-", clicked = self.showMinimized)
        self.minimizeBtn.setObjectName("headerBtn")
        self.closeBtn.setCursor(QCursor(Qt.PointingHandCursor))
        self.minimizeBtn.setCursor(QCursor(Qt.PointingHandCursor))
        githubIcon = QPixmap(":/github.svg")
        self.githubBtn = QLabel("", pixmap=githubIcon)
        self.githubBtn.setObjectName("githubBtn")
        self.githubBtn.setCursor(QCursor(Qt.PointingHandCursor))
        
        self.btnLayout = QGridLayout()
        self.btnLayout.addWidget(self.githubBtn,0,0,2,1, Qt.AlignTop)
        self.btnLayout.addWidget(QLabel(""),0,1,1,1)
        self.btnLayout.addWidget(self.closeBtn,0,2,1,1)
        self.btnLayout.addWidget(self.minimizeBtn,1,2,1,1)
        
        # Title
        self.title = QLabel("Bulk WebP")
        self.subtitle = QLabel("Image Converter")
        self.title.setObjectName("title")
        self.subtitle.setObjectName("subtitle")
        
        self.titleBox = QWidget()
        self.titleLayout = QVBoxLayout()
        self.titleLayout.setContentsMargins(0,0,0,0)
        self.titleLayout.addWidget(self.title)
        self.titleLayout.addWidget(self.subtitle)
        self.titleBox.setLayout(self.titleLayout)
        
        # Header
        horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum) 
        verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding) 
        self.header = QWidget()
        self.header.setObjectName("header")
        self.header.installEventFilter(self)
        self.headerLayout = QHBoxLayout()
        self.headerLayout.setContentsMargins(0,0,0,0)
        self.headerLayout.addWidget(self.titleBox)
        self.headerLayout.addItem(horizontalSpacer)
        self.headerLayout.addLayout(self.btnLayout)
        self.header.setLayout(self.headerLayout)
        self.header.setCursor(QCursor(Qt.SizeAllCursor))
        
        # Form
        self.inputFolderBtn = QPushButton("Select Folder", clicked = self.selectInputFolder)
        self.outputFolderBtn = QPushButton("Select Folder", clicked = self.selectOutputFolder)
        
        self.imageQualitySliderLayout = QHBoxLayout()
        self.imageQualitySlider = QSlider(Qt.Horizontal)
        self.imageQualitySlider.setRange(1, 100)
        self.imageQualitySlider.setFocusPolicy(Qt.NoFocus)
        self.imageQualitySlider.setValue(self.imageQuality)
        self.imageQualitySlider.valueChanged.connect(self.changeImageQuality)
        self.imageQualityLabel = QLabel(str(self.imageQuality))
        self.imageQualityLabel.setObjectName("imgQualityLabel")
        self.imageQualitySliderLayout.addWidget(self.imageQualitySlider)
        self.imageQualitySliderLayout.addWidget(self.imageQualityLabel)
        
        self.inputFolderBtn.setCursor(QCursor(Qt.PointingHandCursor))
        self.outputFolderBtn.setCursor(QCursor(Qt.PointingHandCursor))
        self.imageQualitySlider.setCursor(QCursor(Qt.PointingHandCursor))
        
        self.delayInputLayout = QHBoxLayout()
        self.delayInput = QLineEdit()
        self.delayInput.setAlignment(Qt.AlignCenter)
        self.delayInput.setText(self.delay)
        self.delayInput.textChanged.connect(self.changeDelay)
        self.delayInput.setObjectName("delayInput")
        self.delayInput.setFixedSize(40,30)
        self.delayInputLabel = QLabel("second(s)")
        self.delayInputLayout.addWidget(self.delayInput)
        self.delayInputLayout.addWidget(self.delayInputLabel)
        
        self.form = QFormLayout()
        self.form.addRow(QLabel(""))
        self.form.addRow(QLabel("Input Folder:"), self.inputFolderBtn)
        self.form.addRow(QLabel("Output Folder:"), self.outputFolderBtn)
        self.form.addRow(QLabel(""))
        self.form.addRow(QLabel("Quality:"), self.imageQualitySliderLayout)
        self.form.addRow(QLabel("Delay:"), self.delayInputLayout)
        
        # Convert btn
        self.convertBtn = QPushButton("Convert", clicked = self.convert)
        self.convertBtn.setObjectName("convertBtn")
        self.convertBtn.setCursor(QCursor(Qt.PointingHandCursor))
        
        # Main layout
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(20,20,20,5)
        self.layout.addWidget(self.header)
        self.layout.addItem(verticalSpacer)
        self.layout.addLayout(self.form)
        self.mainWidget.setLayout(self.layout)
        self.layout.addItem(verticalSpacer)
        self.layout.addWidget(self.convertBtn)
        
        self.show()
        
    def eventFilter(self, obj, event):
        if obj.objectName() == "header":
            if self.githubBtn.underMouse():
                if event.type() == QEvent.MouseButtonRelease:
                    webbrowser.open("https://github.com/carlosgauci/webp-image-converter/")
                    return True
            if self.closeBtn.underMouse() or self.minimizeBtn.underMouse():
                return True
            else:
                if event.type() == QEvent.MouseButtonDblClick:
                    self.setWindowState(self.windowState() ^ Qt.WindowFullScreen)
                    return True
                

                if event.type() == QEvent.MouseButtonRelease:
                    if event.globalPos().y() < 10 and self.moved:
                        self.prevGeo = self.geometry()
                        self.showMaximized()
                        return True
                    
                if event.type() == QEvent.MouseButtonPress:
                    focused_widget = QApplication.focusWidget()
                    if focused_widget:
                        focused_widget.clearFocus()
                    self.prevMousePos = event.windowPos()
                    self.moved = False
                    
                if event.type() == QEvent.MouseMove:
                    if self.windowState() == Qt.WindowFullScreen or self.windowState() == Qt.WindowMaximized:
                        self.showNormal()
                        self.prevMousePos = QPointF(self.prevGeo.width()*.5,50)
                        
                    gr = self.geometry()
                    screenPos= event.globalPos()
                    pos = screenPos - self.prevMousePos
                    x = max(pos.x(),0)
                    y = max(pos.y(),0)
                    screen = QGuiApplication.screenAt(QPoint(int(x), int(y))).size()
                    x = min(x,screen.width() - gr.width())
                    y = min(y,screen.height() - gr.height())
                    
                    self.move(int(x), int(y))
                    self.moved = True
                        
        return QMainWindow.eventFilter(self,obj,event)
    
    def selectInputFolder(self):
        folder = QFileDialog.getExistingDirectory(self, 'Select Folder')
        self.inputFolder = folder
        if folder:
            if len(folder) > 40:
                self.inputFolderBtn.setText(f"...{folder[len(folder) - 40 :]}")
            else: self.inputFolderBtn.setText(folder)
        
    def selectOutputFolder(self):
        folder = QFileDialog.getExistingDirectory(self, 'Select Folder')
        self.outputFolder = folder
        if folder:
            if len(folder) > 40:
                self.outputFolderBtn.setText(f"...{folder[len(folder) - 40 :]}")
            else: self.outputFolderBtn.setText(folder)
    
    def changeImageQuality(self, value):
        self.imageQuality = value
        self.imageQualityLabel.setText(str(value))

    def changeDelay(self, value):
        self.delay = value
        
    def convert(self):
        if self.inputFolder == "" or self.outputFolder == "":
            self.statusBar.showMessage("    Please select input/output folders!", 3000)
        else:
            self.convertBtn.setText("Converting...")
            self.convertBtn.setEnabled(False)
            self.imageQualitySlider.setEnabled(False)
            self.inputFolderBtn.setEnabled(False)
            self.outputFolderBtn.setEnabled(False)
            self.thread = QThread()
            self.worker = Worker(self.inputFolder, self.outputFolder, self.imageQuality, self.delay)
            self.worker.moveToThread(self.thread)
            self.thread.started.connect(self.worker.convertImages)
            self.worker.finished.connect(self.thread.quit)
            self.worker.finished.connect(self.worker.deleteLater)
            self.thread.finished.connect(self.thread.deleteLater)
            self.thread.finished.connect(self.finished)
            self.worker.progress.connect(self.reportProgress)
            self.thread.start()

    
    def finished(self):
        self.convertBtn.setText("Convert")
        self.statusBar.showMessage("    Done!")
        self.convertBtn.setEnabled(True)
        self.imageQualitySlider.setEnabled(True)
        self.inputFolderBtn.setEnabled(True)
        self.outputFolderBtn.setEnabled(True)
        
    
    def reportProgress(self, i, n):
        self.statusBar.showMessage(f"    Converting ({i}) - {n}")
        if len(n) > 40:
            self.statusBar.showMessage(f"    Converting ({i}) - ...{n[len(n) - 40 :]}")
        else: self.statusBar.showMessage(f"    Converting ({i}) - {n}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    stream = QFile(":/stylesheet.qss")
    stream.open(QIODevice.ReadOnly)
    app.setStyleSheet(QTextStream(stream).readAll())
    app.setWindowIcon(QIcon(":/icon.ico"))
    window = MainWindow()
    sys.exit(app.exec_())