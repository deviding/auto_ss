# -*- coding: utf-8 -*-
import os, sys, time, threading

from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import *

from datetime import datetime
from PIL import ImageGrab


class ScreenShot(threading.Thread):
    """ スクリーンショットを実行するスレッドクラス
    """
    def __init__(self, func, interval):
        """ コンストラクタ
        """
        threading.Thread.__init__(self)
        self.func = func
        self.interval = interval
        self.is_screenshot_run = True


    def run_stop(self):
        """ スレッドを停止させる関数
        """
        self.is_screenshot_run = False


    def run(self):
        """ スクリーンショットを実行する関数
        """
        self.func() # スクリーンショット実行

        old_time = time.time()
        while True:
            if self.is_screenshot_run:
                new_time = time.time() - old_time

                if new_time >= self.interval:
                    self.func() # スクリーンショット実行
                    old_time = time.time()
            else:
                break


class AutoSSGui(QDialog):
    """
    自動でスクリーンショットを撮影するGUIクラス
    """
    VERSION = "1.0"
    TITLE = "Auto SS v{}".format(VERSION)
    WINDOW_WIDTH    = 420
    WINDOW_HEIGHT   = 270
    TEXT_BOX_WIDTH  = 400
    TEXT_BOX_HEIGHT = 100
    PB_WIDTH        = 380
    EXTENTION_LIST  = [".jpg", ".png", ".bmp"]
    SAVE_FILE_NAME  = "_screen_shot"
    BTN_RUN  = "撮影開始"
    BTN_STOP = "停止"


    def __init__(self, parent=None):
        """ コンストラクタ
        """
        super(AutoSSGui, self).__init__(parent)
        # ウインドウの最小化と閉じるボタンのみ有効
        self.setWindowFlags(Qt.MSWindowsFixedSizeDialogHint)

        # スクリーンショット実行フラグ
        self.is_screenshot_run = False

        # 実行時のディレクトリパスを取得
        self.my_dir_path = os.path.abspath(os.path.dirname(sys.argv[0]))

        # アイコン画像を設定
        if sys.platform.startswith('win'):
            self.setWindowIcon(QPixmap(self.temp_path('icon.ico')))

        # Widgetsの設定(タイトル、固定横幅、固定縦幅)
        self.setWindowTitle(self.TITLE)
        self.setFixedWidth(self.WINDOW_WIDTH)
        self.setFixedHeight(self.WINDOW_HEIGHT)

        # 保存フォルダ部分
        save_layout = QHBoxLayout()
        self.save_path = QLineEdit("")
        self.save_path.setEnabled(False) # テキスト入力を禁止
        self.save_select_button = QPushButton("参照")
        self.save_select_button.clicked.connect(self.save_folder_dialog)
        save_layout.addWidget(QLabel("保存フォルダ:"), 1)
        save_layout.addWidget(self.save_path, 5)
        save_layout.addWidget(self.save_select_button, 1)

        # 撮影間隔・保存拡張子部分
        interval_layout = QHBoxLayout()
        self.interval_sp = QSpinBox()
        self.interval_sp.setRange(0, 86400)
        self.interval_sp.setValue(10)

        self.combobox = QComboBox(self)
        self.combobox.addItems(self.EXTENTION_LIST)
        self.combobox.setCurrentIndex(0)

        interval_layout.addWidget(QLabel("撮影間隔(秒):"), 1)
        interval_layout.addWidget(self.interval_sp, 2)
        interval_layout.addWidget(QLabel("保存拡張子:"), 1)
        interval_layout.addWidget(self.combobox, 1)

        # 保存ファイル名表示部分
        log_layout = QHBoxLayout()
        self.textbox = QListView()
        self.text_list = QStringListModel()
        self.textbox.setModel(self.text_list)
        self.textbox.setFixedSize(self.TEXT_BOX_WIDTH, self.TEXT_BOX_HEIGHT)
        log_layout.addWidget(self.textbox )

        # プログレスバー部分
        pb_layput = QHBoxLayout()
        self.pb = QProgressBar()
        self.pb.setFixedWidth(self.PB_WIDTH)
        self.pb.setTextVisible(False)
        pb_layput.addWidget(self.pb)

        # ボタン部分
        btn_layout = QHBoxLayout()
        self.button = QPushButton(self.BTN_RUN)
        self.button.clicked.connect(self.run_stop_screenshot)
        btn_layout.addWidget(QLabel(""), 1)
        btn_layout.addWidget(self.button, 1)
        btn_layout.addWidget(QLabel(""), 1)

        # レイアウトを作成して各要素を配置
        layout = QVBoxLayout()
        layout.addLayout(save_layout)
        layout.addSpacing(6)
        layout.addLayout(interval_layout)
        layout.addSpacing(6)
        layout.addLayout(log_layout)
        layout.addSpacing(6)
        layout.addLayout(pb_layput)
        layout.addSpacing(6)
        layout.addLayout(btn_layout)

        # レイアウトを画面に設定
        self.setLayout(layout)

        self.ss_thread = None


    def temp_path(self, relative_path):
        """ 実行時のパスを取得する関数

            Args:
                relative_path (str): 相対ファイルパス
            
            Returns:
                実行時のパス文字列
        """
        try:
            #Retrieve Temp Path
            base_path = sys._MEIPASS
        except Exception:
            #Retrieve Current Path Then Error 
            base_path = os.path.abspath(".")
        return os.path.join(base_path, relative_path)


    def save_folder_dialog(self):
        """ 保存先フォルダ選択ダイアログを表示する関数
        """
        # すでに設定されているフォルダがあればそれを開く
        path = self.my_dir_path
        path_save = self.save_path.text()

        if not path_save == "":
            path = path_save

        dir_path = QFileDialog.getExistingDirectory(self, "保存先フォルダ選択", path)

        if dir_path:
            self.save_path.setText(dir_path)


    def run_stop_screenshot(self):
        """ 自動のスクリーンショットを実行/停止する関数
        """
        save_folder = self.save_path.text()
        interval_value = int(self.interval_sp.value())

        # 保存フォルダチェック
        if save_folder == "":
            QMessageBox.warning(self, "注意", "保存フォルダが設定されていません。")
            return

        # インターバルチェック
        if interval_value == 0:
            ok_button = QMessageBox.StandardButton.Ok
            cancel_button = QMessageBox.StandardButton.Cancel
            result = QMessageBox.warning(self, "注意", "撮影間隔(秒)が0の場合はスクリーンショットを1回だけ実行します。よろしいですか？", ok_button, cancel_button)
            if result == QMessageBox.StandardButton.Cancel:
                return

        self.is_screenshot_run = not self.is_screenshot_run

        if self.is_screenshot_run:
            # GUI非活性化
            self.set_all_enabled(False)
            self.button.setText(self.BTN_STOP)

            # プログレスバーの開始
            self.pb.setMinimum(0)
            self.pb.setMaximum(0)

            # ログ表示をクリア
            self.text_list.removeRows(0, self.text_list.rowCount())

            if interval_value == 0:
                # スクリーンショットを1回だけ実行
                self.screenshot()
                self.is_screenshot_run = False
            else:
                # スクリーンショットを実行するスレッドを設定して実行
                # self.ss_thread = threading.Thread(target=self.screenshot_thread)
                # self.ss_thread.setDaemon(True)
                # self.ss_thread.start()
                self.ss_thread = ScreenShot(self.screenshot, int(self.interval_sp.value()))
                self.ss_thread.setDaemon(True)
                self.ss_thread.start()

        if not self.is_screenshot_run:
            # スレッド停止
            self.ss_thread.run_stop()
            # GUI活性化
            self.set_all_enabled(True)
            # プログレスバーの停止
            self.pb.setMinimum(0)
            self.pb.setMaximum(100)
            # スクリーンショット終了
            self.button.setText(self.BTN_RUN)
            # 終了ダイアログ表示
            QMessageBox.information(self, "終了", "スクリーンショットを停止しました。保存フォルダを確認してください。")


    def screenshot(self):
        """ スクリーンショットを実行する関数
        """
        # スクリーンショットを実行
        screenshot = ImageGrab.grab()
        save_file_name = datetime.now().strftime("%Y-%m-%d_%H%M.%S") + self.SAVE_FILE_NAME + self.combobox.currentText()
        screenshot.save(self.save_path.text() + "/" + save_file_name)
        # ログとして画面に表示
        self.show_log(save_file_name)


    def set_all_enabled(self, is_enable):
        """ GUIの有効/無効を設定する関数

            Args:
                is_enable (bool): True/有効化、False/無効化
        """
        self.save_select_button.setEnabled(is_enable)
        self.interval_sp.setEnabled(is_enable)
        self.combobox.setEnabled(is_enable)


    # def screenshot_thread(self):
    #     """ スクリーンショットを実行する関数
    #     """
    #     self.screenshot() # スクリーンショット実行

    #     old_time = time.time()
    #     while True:
    #         if self.is_screenshot_run:
    #             new_time = time.time() - old_time

    #             if new_time >= int(self.interval_sp.value()):
    #                 self.screenshot() # スクリーンショット実行
    #                 old_time = time.time()
    #         else:
    #             break


    def show_log(self, log_text):
        # ログ表示を更新
        log_list = self.text_list.stringList()
        log_list.append(log_text)
        self.text_list.setStringList(log_list)
        self.textbox.scrollToBottom()


if __name__ == '__main__':
    # Qtアプリケーションの作成
    app = QApplication(sys.argv)

    # フォームを作成して表示
    form = AutoSSGui()
    form.show()

    # 画面表示のためのループ
    sys.exit(app.exec())