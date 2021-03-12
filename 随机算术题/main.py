from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox
from PyQt5.QtCore import pyqtSlot, QUrl, QTimer
from PyQt5.QtGui import QIcon
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent, QMediaPlaylist
from UI.mainWindow import Ui_MainWindow
from setting import Setting
import sys
import random
import re
import os


class MyUi(QMainWindow):
    def __init__(self, parent=None):
        # 主窗口界面
        super().__init__(parent)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.setFixedSize(800, 600)

        self.difficulty = 3  # 难度
        self.setWindowTitle('小学算术题 难度：%d' % self.difficulty)
        self.setWindowIcon(QIcon('res/image/windowIcon.jpg'))
        self.ui.pauseBtn.setIcon(QIcon('res/image/pause.png'))

        # 设置窗口界面
        self.setting = Setting()
        self.setting._close_signal.connect(self.on_setting_closed)

        # 音效加载
        self.playlist = QMediaPlaylist()
        self.playlist.addMedia(QMediaContent(QUrl('res/audio/correct.mp3')))
        self.playlist.addMedia(QMediaContent(QUrl('res/audio/wrong.mp3')))
        self.playlist.addMedia(QMediaContent(QUrl('res/audio/complete.mp3')))
        self.playlist.addMedia(QMediaContent(QUrl('res/audio/timeOver.mp3')))
        self.playlist.setPlaybackMode(QMediaPlaylist.CurrentItemOnce)
        self.player = QMediaPlayer()
        self.player.setPlaylist(self.playlist)
        self.player.play()

        # 定义变量
        self.answer = 0
        self.total = 0
        self.correct = 0
        self.accuracy = 0.
        self.overtime = 0
        self.tmpOutput = []

        # 保存路径
        self.fpath = 'history.txt'

        # 定时器初始化
        self.timeLimit = 30
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.on_timer_timeout)
        self.currentTime = self.timeLimit
        self.ui.timeLabel.setText(str(self.currentTime))
        self.pause = False

        # 错题模式初始化
        self.mistakeBatchSize = 5
        self.mistakeMode = False
        self.exitingMistakeMode = False
        self.ui.tipLabel.clear()
        self.ui.remainingLabel.clear()
        self.questionQueue = []

        # 第一次开始运行
        self.refreshQuestion()
        self.refreshBoard()

        # 计时器开始计时
        self.timer.start(1000)

    # 刷新题目
    def refreshQuestion(self):
        # 清空self.tmpOutput以防刷新问题后将上一题也写入文件
        self.tmpOutput.clear()

        # 非错题模式随机出题
        if self.questionQueue == []:
            assert self.mistakeMode == False
            a = random.randint(0, 10 ** self.difficulty)
            b = random.randint(0, 10 ** self.difficulty)
            symbol, self.answer = (' + ', a + b) if random.random() > 0.5 else (' - ', a - b)

        # 错题模式从self.questionQueue中出题
        else:
            assert self.mistakeMode == True
            self.ui.remainingLabel.setText('剩余：{}/{}'.format(len(self.questionQueue), self.mistakeBatchSize))
            a, symbol, b = self.questionQueue.pop(0)
            self.answer = eval(a + symbol + b)
            self.tmpOutput.append('(*)')
            # 判断是否是最后一道错题
            if self.questionQueue == []:
                self.exitingMistakeMode = True

        # 将题目放入self.tmpOutput中等待写入文件
        self.tmpOutput.append('Question: ' + '{} {} {}:'.format(a, symbol, b))

        self.ui.questionLabel.setText(str(a) + symbol + str(b))
        self.ui.judgeLabel.setText('')
        self.ui.lineEdit.setFocus()

    # 更新记录板显示
    def refreshBoard(self):
        self.ui.correctLabel.setText('答对：%d/%d' % (self.correct, self.total))
        self.ui.accuracyLabel.setText('准确率：{:.0%}'.format(self.accuracy))
        self.ui.overtimeLabel.setText('超时次数：{}'.format(self.overtime))

    # 更新计时器时间
    def refreshTime(self):
        self.ui.timeLabel.setText(str(self.timeLimit))
        self.currentTime = self.timeLimit

    # 将self.tmpOutput中的字符串写入文件
    def writeFile(self):
        with open(self.fpath, 'a') as f:
            f.write('\t'.join(self.tmpOutput) + '\n')
        self.tmpOutput.clear()

    @pyqtSlot()
    def on_answerBtn_clicked(self):
        self.ui.lineEdit.setText(str(self.answer))

    @pyqtSlot()
    def on_refreshBtn_clicked(self):
        self.refreshQuestion()
        self.refreshTime()

    @pyqtSlot()
    def on_submitBtn_clicked(self):
        userInput = self.ui.lineEdit.text().strip()
        self.ui.lineEdit.clear()

        # 判断输入是否合法
        if re.match('^-?\d+$', userInput):
            # 若回答正确
            if eval(userInput) == self.answer:
                # 播放0号音效
                self.player.stop()
                self.playlist.setCurrentIndex(0)
                self.player.play()
                # UI响应
                self.ui.judgeLabel.setText('回答正确！')
                # 记录板更新变量，写入文件
                self.correct += 1
                self.total += 1
                self.accuracy = round(self.correct / self.total, 2)
                self.tmpOutput.append(userInput)
                self.writeFile()

                # 如果这是最后一个错题的话，有些地方要特殊处理
                if self.exitingMistakeMode == True:
                    # 修改状态
                    self.exitingMistakeMode = False
                    self.mistakeMode = False
                    # 播放2号音效
                    self.playlist.setCurrentIndex(2)
                    self.player.play()
                    # UI响应
                    self.ui.tipLabel.setText('完成错题模式！')
                    self.ui.remainingLabel.clear()

                # 更新问题，记录板显示，计时器时间
                self.refreshBoard()
                self.refreshQuestion()
                self.refreshTime()

            # 若回答错误
            else:
                # # 播放1号音效
                # self.player.stop()
                # self.playlist.setCurrentIndex(1)
                # self.player.play()

                # UI响应
                self.ui.judgeLabel.setText('回答错误！再思考一下！')
                # 记录板更新变量，不写入文件
                self.total += 1
                self.accuracy = round(self.correct / self.total, 2)
                self.tmpOutput.append('*' + userInput)

                # 更新记录板显示，计时器时间，不刷新问题
                self.refreshBoard()
                self.refreshTime()

    @pyqtSlot()
    def on_timer_timeout(self):
        self.currentTime -= 1
        # 若还有剩余时间
        if self.currentTime > 0:
            self.ui.timeLabel.setText(str(self.currentTime))
        # 若超时
        else:
            assert self.currentTime == 0
            # 播放3号音效
            self.player.stop()
            self.playlist.setCurrentIndex(3)
            self.player.play()

            # UI响应
            QMessageBox.information(self, '1', '超时了！')
            self.overtime += 1
            self.refreshTime()
            self.refreshBoard()

    @pyqtSlot()
    def on_pauseBtn_clicked(self):
        # 暂停
        if not self.pause:
            self.timer.stop()
            self.ui.pauseBtn.setIcon(QIcon('res/image/start.jpg'))
            self.pause = True
        # 取消暂停
        else:
            self.timer.start(1000)
            self.ui.pauseBtn.setIcon(QIcon('res/image/pause.png'))
            self.pause = False

    @pyqtSlot()
    def on_historyBtn_clicked(self):
        # 暂停
        if not self.pause:
            self.timer.stop()
            self.ui.pauseBtn.setIcon(QIcon('res/image/start.jpg'))
            self.pause = True

        # TODO 也许以后可以用QTableWidget美化输出
        # with open(self.fpath,'r') as f:
        #     content = f.read()

        # 用打开记事本的方法看历史记录
        os.system(self.fpath)

    @pyqtSlot()
    def on_mistakeModeBtn_clicked(self):
        # 开启错题模式
        self.mistakeMode = True
        # 更新计时器时间
        self.currentTime = self.timeLimit
        self.ui.timeLabel.setText(str(self.currentTime))

        # 读取历史记录中的错题（读取数不超过self.mistakeBatchSize个），并将其赋值给self.mistakeQueue
        with open(self.fpath, 'r') as f:
            lines = f.readlines()
        mistakeList = []
        for Question in lines:
            if '*' in Question:
                questionText = Question.split(':')[1].strip()
                assert len(questionText.split()) == 3
                mistakeList.append(questionText.split())
                if len(mistakeList) == self.mistakeBatchSize:
                    break
        assert len(mistakeList) <= self.mistakeBatchSize
        random.shuffle(mistakeList)  # 随机打乱这些错题
        self.questionQueue = mistakeList

        # UI响应
        self.ui.tipLabel.setText('正在重做错题模式')
        self.ui.lineEdit.clear()

        # 刷新问题
        self.refreshQuestion()

    @pyqtSlot()
    def on_settingBtn_clicked(self):
        # 暂停
        if not self.pause:
            self.timer.stop()
            self.ui.pauseBtn.setIcon(QIcon('res/image/start.jpg'))
            self.pause = True

        self.setting.show()

    @pyqtSlot()
    def on_setting_closed(self):
        # 将设置值赋予主窗口
        self.difficulty, self.timeLimit, self.mistakeBatchSize = \
            self.setting.difficultyValue, self.setting.timeLimitValue, self.setting.mistakeBatchSizeValue


if __name__ == '__main__':
    app = QApplication(sys.argv)
    myApp = MyUi()
    myApp.show()
    sys.exit(app.exec_())
