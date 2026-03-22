from textual.screen import Screen
from textual.widgets import Static

class GenerateScreen(Screen):

    def compose(self):
        yield Static("Generate Configuration", id="title")
        yield Static("TODO: implement config generator", id="gen")
