from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import pyqtSlot, pyqtSignal
from PyQt5.QtGui import QIcon
from UI.settingWidget import Ui_Form


class Setting(QWidget):
    # 定义关闭时的信号
    _close_signal = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.ui = Ui_Form()
        self.ui.setupUi(self)
        self.setFixedSize(500, 380)
        self.setWindowTitle('设置')
        self.setWindowIcon(QIcon('res/image/setting.jpg'))

        # 默认值
        self.difficultyValue_default = 3
        self.timeLimitValue_default = 30
        self.mistakeBatchSizeValue_default = 5

        self.difficultyValue = self.difficultyValue_default
        self.timeLimitValue = self.timeLimitValue_default
        self.mistakeBatchSizeValue = self.mistakeBatchSizeValue_default

    @pyqtSlot(int)
    def on_difficultySlider_valueChanged(self, value):
        self.difficultyValue = value
        self.ui.difficultyLabel.setText('难度：{}'.format(self.difficultyValue))

    @pyqtSlot(int)
    def on_timeLimitSlider_valueChanged(self, value):
        self.timeLimitValue = value
        self.ui.timeLimitLabel.setText('时间：{}'.format(self.timeLimitValue))

    @pyqtSlot(int)
    def on_mistakeBatchSizeSlider_valueChanged(self, value):
        self.mistakeBatchSizeValue = value
        self.ui.mistakeBatchSizeLabel.setText('错题数：{}'.format(self.mistakeBatchSizeValue))

    @pyqtSlot()
    def on_resetBtn_clicked(self):
        self.ui.difficultySlider.setValue(self.difficultyValue_default)
        self.ui.timeLimitSlider.setValue(self.timeLimitValue_default)
        self.ui.mistakeBatchSizeSlider.setValue(self.mistakeBatchSizeValue_default)

    @pyqtSlot()
    def on_yesBtn_clicked(self):
        self.close()

    # 重写关闭事件：发射关闭信号以便让主窗口知道自己关闭了
    def closeEvent(self, QCloseEvent):
        self._close_signal.emit()
