import os
from kivy.core.text import LabelBase
from kivymd.theming import ThemeManager
from kivymd.font_definitions import theme_font_styles

from kivymd.app import MDApp
from kivy.lang import Builder

from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.list import OneLineIconListItem, MDList
from kivymd.theming import ThemableBehavior
from kivy.properties import StringProperty, ListProperty, ObjectProperty
from typing import List

colors = {
    "Teal": {
        "50": "#E0F2F1",
        "100": "#B2DFDB",
        "200": "#80CBC4",
        "300": "#4DB6AC",
        "400": "#26A69A",
        "500": "#009688",
        "600": "#00897B",
        "700": "#00796B",
        "800": "#00695C",
        "900": "#004D40",
        "A100": "#A7FFEB",
        "A200": "#64FFDA",
        "A400": "#1DE9B6",
        "A700": "#00BFA5",
    },
    "Red": {
        "50": "#FFEBEE",
        "100": "#FFCDD2",
        "200": "#EF9A9A",
        "300": "#E57373",
        "400": "#EF5350",
        "500": "#F44336",
        "600": "#E53935",
        "700": "#D32F2F",
        "800": "#C62828",
        "900": "#B71C1C",
        "A100": "#FF8A80",
        "A200": "#FF5252",
        "A400": "#FF1744",
        "A700": "#D50000",
    },
    "Gray": {
        "50": "#FAFAFA",
        "100": "#F5F5F5",
        "200": "#EEEEEE",
        "300": "#E0E0E0",
        "400": "#BDBDBD",
        "500": "#9E9E9E",
        "600": "#757575",
        "700": "#616161",
        "800": "#424242",
        "900": "#212121",
    },
    "LightGreen": {
        "50": "#F1F8E9",
        "100": "#DCEDC8",
        "200": "#C5E1A5",
        "300": "#AED581",
        "400": "#9CCC65",
        "500": "#8BC34A",
        "600": "#7CB342",
        "700": "#689F38",
        "800": "#558B2F",
        "900": "#33691E",
        "A100": "#CCFF90",
        "A200": "#B2FF59",
        "A400": "#76FF03",
        "A700": "#64DD17",
    },
    "Light": {
        "StatusBar": "E0E0E0",
        "AppBar": "F5F5F5",
        "Background": "FAFAFA",
        "CardsDialogs": "FFFFFF",
        "FlatButtonDown": "cccccc",
    },
    "Dark": {
        "StatusBar": "000000",
        "AppBar": "212121",
        "Background": "303030",
        "CardsDialogs": "424242",
        "FlatButtonDown": "999999",
    }
}


class ThemeService(object):
    DIR = os.path.dirname(os.path.abspath(__file__))
    LOGO_DIR = os.path.join(DIR, "logo/")
        
    def __init__(self):
        self.__dark_on = False
        self.__theme_cls = ThemeManager()

    def set_theme(self, dark: bool = False) -> ThemeManager:
        self.__dark_on = dark

        self.__theme_cls.colors = colors

        self.__theme_cls.primary_palette = "Teal"
        self.__theme_cls.primary_hue = "A400"

        self.__theme_cls.accent_palette = "Gray"

        self.__theme_cls.theme_style = "Dark" if dark else "Light"
        # self.__theme_cls.primary_palette = "LightGreen" if dark else "LightGreen"

        return self.__theme_cls

    @property
    def logo(self) -> str:
        return self.LOGO_DIR + "/logo_white.png" if self.__dark_on else self.LOGO_DIR + "/logo_black.png"

    @property
    def text_color(self) -> List[float]:
        return self.white_rgba if self.__dark_on else self.black_rgba

    @property
    def primary_color(self):
        return self.__theme_cls.primary_color
    
    @property
    def error_color(self):
        return self.__theme_cls.error_color
    
    @property
    def success_color(self) -> List[float]:
        return [0.5647, 0.7882, 0.2823, 1]
    
    @property
    def black_rgba(self) -> List[float]:
        return [0, 0, 0, 1]

    @property
    def dark_primary(self) -> List[float]:
        return [0.2, 0.2, 0.2392, 1]

    @property
    def dark_secondary(self) -> List[float]:
        return [0.2156, 0.2156, 0.2509, 1]

    @property
    def white_rgba(self) -> List[float]:
        return [1, 1, 1, 1]
