# OpenCodeBlock an open-source tool for modular visual programing in python
# Copyright (C) 2021 Mathïs FEDERICO <https://www.gnu.org/licenses/>

""" Module for the base OCB Code Block. """

from PyQt5.QtCore import QByteArray
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QPushButton, QTextEdit

from ansi2html import Ansi2HTMLConverter

from opencodeblocks.graphics.blocks.block import OCBBlock
from opencodeblocks.graphics.pyeditor import PythonEditor
from opencodeblocks.graphics.worker import Worker

conv = Ansi2HTMLConverter()


class OCBCodeBlock(OCBBlock):

    """
    Code Block

    Features an area to edit code as well as a panel to display the output.

    The following is always true:
    output_panel_height + source_panel_height + edge_size*2 + title_height == height

    """

    def __init__(self, **kwargs):
        super().__init__(block_type='code', **kwargs)

        self.output_panel_height = self.height / 3
        self._min_output_panel_height = 20
        self._min_source_editor_height = 20

        self.output_closed = False
        self.previous_splitter_size = [0, 0]

        self.source_editor = self.init_source_editor()
        self.output_panel = self.init_output_panel()
        self.run_button = self.init_run_button()
        self.stdout = ""
        self.image = ""
        self.title_left_offset = 3 * self.edge_size

        self.holder.setWidget(self.root)

        self.update_all()  # Set the geometry of display and source_editor

    def init_source_editor(self):
        """ Initialize the python source code editor. """
        source_editor = PythonEditor(self)
        self.splitter.addWidget(source_editor)
        return source_editor

    def update_all(self):
        """ Update the code block parts. """
        super().update_all()
        if hasattr(self, 'run_button'):
            self.run_button.setGeometry(
                int(self.edge_size),
                int(self.edge_size / 2),
                int(2.5 * self.edge_size),
                int(2.5 * self.edge_size)
            )

        # Close output panel if no output
        if self.stdout == "" and self.image == "":
            self.previous_splitter_size = self.splitter.sizes()
            self.output_closed = True
            self.splitter.setSizes([1, 0])

    @property
    def source(self) -> str:
        """ Source code. """
        return self._source

    @source.setter
    def source(self, value: str):
        self._source = value
        if hasattr(self, 'source_editor'):
            self.source_editor.setText(self._source)

    @property
    def stdout(self) -> str:
        """ Code output. Be careful, this also includes stderr """
        return self._stdout

    @stdout.setter
    def stdout(self, value: str):
        self._stdout = value
        if hasattr(self, 'output_closed'):
            # If output panel is closed and there is output, open it
            if self.output_closed == True and value != "":
                self.output_closed = False
                self.splitter.setSizes(self.previous_splitter_size)
            # If output panel is open and there is no output, close it
            elif self.output_closed == False and value == "":
                self.previous_splitter_size = self.splitter.sizes()
                self.output_closed = True
                self.splitter.setSizes([1, 0])
        if hasattr(self, 'source_editor'):
            # If there is a text output, erase the image output and display the
            # text output
            self.image = ""

            # Remove ANSI backspaces
            text = value.replace("\x08", "")
            # Convert ANSI escape codes to HTML
            text = conv.convert(text)
            # Replace background color
            text = text.replace('background-color: #000000',
                                'background-color: #434343')

            self.output_panel.setText(text)

    @property
    def image(self) -> str:
        """ Code output. """
        return self._image

    @image.setter
    def image(self, value: str):
        self._image = value
        # open or close output panel, same as stdout
        if hasattr(self, 'output_closed') and value != "":
            if self.output_closed == True and value != "":
                self.output_closed = False
                self.splitter.setSizes(self.previous_splitter_size)
            elif self.output_closed == False and value == "":
                self.previous_splitter_size = self.splitter.sizes()
                self.output_closed = True
                self.splitter.setSizes([1, 0])
        if hasattr(self, 'source_editor') and self.image != "":
            # If there is an image output, erase the text output and display
            # the image output
            text = ""
            ba = QByteArray.fromBase64(str.encode(self.image))
            pixmap = QPixmap()
            pixmap.loadFromData(ba)
            text = f'<img src="data:image/png;base64,{self.image}">'
            self.output_panel.setText(text)

    @source.setter
    def source(self, value: str):
        self._source = value
        if hasattr(self, 'source_editor'):
            editor_widget = self.source_editor
            editor_widget.setText(self._source)

    def init_output_panel(self):
        """ Initialize the output display widget: QLabel """
        output_panel = QTextEdit()
        output_panel.setReadOnly(True)
        output_panel.setFont(self.source_editor.font())
        self.splitter.addWidget(output_panel)
        return output_panel

    def init_run_button(self):
        """ Initialize the run button """
        run_button = QPushButton(">", self.root)
        run_button.setMinimumWidth(int(self.edge_size))
        run_button.clicked.connect(self.run_code)
        run_button.raise_()

        return run_button

    def run_code(self):
        """Run the code in the block"""
        code = self.source_editor.text()
        self.source = code
        # Create a worker to handle execution
        worker = Worker(self.source_editor.kernel, self.source)
        worker.signals.stdout.connect(self.handle_stdout)
        worker.signals.image.connect(self.handle_image)
        self.source_editor.threadpool.start(worker)

    def handle_stdout(self, stdout):
        """ Handle the stdout signal """
        self.stdout = stdout

    def handle_image(self, image):
        """ Handle the image signal """
        self.image = image
