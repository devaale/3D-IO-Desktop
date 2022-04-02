from kivymd.app import MDApp
from kivy.config import Config
Config.set('graphics','resizable', False)
from kivy.lang import Builder
from enum import Enum
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.gridlayout import MDGridLayout
from typing import List, Callable
from kivymd.uix.slider import MDSlider
from kivymd.uix.snackbar import Snackbar
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.list import OneLineIconListItem, MDList
from kivymd.uix.card import MDCard, MDSeparator
from kivymd.theming import ThemableBehavior
from kivy.properties import StringProperty, ListProperty, ObjectProperty

from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDIconButton
from sqlalchemy.sql.expression import text

from .theme_service import ThemeService

from ..services.settings import settings_reader
from ..common.logger import logger
from ..helpers import settings_helper
from kivy.core.window import Window

KV = """
# Menu item in the DrawerList list.
<IconListItem>

    IconLeftWidget:
        icon: root.icon
        theme_text_color: "Custom"
        text_color: root.text_color
        
<ActionListItem>

    IconLeftWidget:
        icon: root.icon
        theme_text_color: "Custom"
        text_color: root.text_color
        
<ItemDrawer>:
    theme_text_color: "Custom"
    on_press:
        self.parent.parent.parent.screen_manager.current = root.to_screen
        root.load_page()
    on_release:
        self.parent.set_color_item(self)

    IconLeftWidget:
        id: icon
        icon: root.icon
        theme_text_color: "Custom"
        text_color: root.text_color


<ContentNavigationDrawer>:
    orientation: "vertical"
    padding: 8
    spacing: 0
    
    MDBoxLayout:
        height: logo.height
        size_hint_y: None

        canvas:
            Color:
                rgba: app.theme_service.dark_primary
            Rectangle:
                pos: self.pos
                size: self.size

        Image:
            id: logo
            size: "56dp", "100dp"
            source: app.theme_service.logo
    
    MDSeparator:
        height: 1
        
    ScrollView:
        
        DrawerList:
            id: nav_list

MDScreen:

    MDToolbar:
        id: toolbar
        pos_hint: {"top": 1}
        title: "3D"
        elevation: 10
        md_bg_color: app.theme_service.dark_primary
        specific_text_color: app.theme_service.white_rgba
        left_action_items: [['menu', lambda x: nav_drawer.set_state('open')]]
        right_action_items: [["refresh", lambda x: app.update_results()], ["content-save", lambda x: app.save_settings()], ["dots-vertical", lambda x: app.open_settings_dropdown(x)], ["camera-control", lambda x: app.open_actions_dropdown(x)]]

    MDNavigationLayout:
    
        ScreenManager:
            id: screen_manager

            MDScreen:
                name: "settings_scr"
                size_hint_y: 1.0 - toolbar.height/root.height
                md_bg_color: app.theme_service.dark_primary
                            
                            
            MDScreen:
                name: "advanced_settings_scr"
                size_hint_y: 1.0 - toolbar.height/root.height
                md_bg_color: app.theme_service.dark_primary
            
            MDScreen:
                name: "processing_settings_scr"
                size_hint_y: 1.0 - toolbar.height/root.height
                md_bg_color: app.theme_service.dark_primary
                

        MDNavigationDrawer:
            id: nav_drawer
            md_bg_color: app.theme_service.dark_primary
            
            ContentNavigationDrawer:
                id: content_drawer
                screen_manager: screen_manager
                nav_drawer: nav_drawer
"""


class ContentNavigationDrawer(MDBoxLayout):
    screen_manager = ObjectProperty()
    nav_drawer = ObjectProperty()


class ItemDrawer(OneLineIconListItem):
    icon = StringProperty()
    to_screen = StringProperty()
    text_color = ListProperty((0, 0, 0, 1))
    load_functions = []

    def load_page(self):
        for func in self.load_functions:
            func()


class DrawerList(ThemableBehavior, MDList):
    def set_color_item(self, instance_item):
        for item in self.children:
            if item.text_color == self.theme_cls.primary_color:
                item.text_color = self.theme_cls.text_color
                break
        instance_item.text_color = self.theme_cls.primary_color


class SettingsSliderGrid(MDGridLayout):
    def __init__(self, **kwargs):
        super(SettingsSliderGrid, self).__init__(**kwargs)

        self.cols = 2
        self.padding = 20
        self.spacing = 10

    def update(self, settings):
        for data in settings:
            for setting in self.children:
                if data == setting.key:
                    setting.update(settings, settings[data], data)


class SettingsSliderCard(MDCard):
    def __init__(
        self,
        label: str,
        value,
        metric: str,
        multiplier,
        min_val,
        max_val,
        step,
        theme_service: ThemeService,
        settings,
        key,
        **kwargs,
    ):
        super(SettingsSliderCard, self).__init__(**kwargs)

        self.__settings = settings
        self.__theme_service = theme_service

        self.key = key
        self.set_properties()

        self.main_layout = MDBoxLayout(orientation="vertical")
        self.labels_layout = MDBoxLayout(orientation="horizontal")
        self.slider_layout = MDBoxLayout(orientation="horizontal")
        
        self.minus_btn = MDIconButton(
            icon="minus",
            theme_text_color="Custom",
            text_color=self.__theme_service.white_rgba,
            pos_hint={"center_x": 0.5, "center_y": 0.5},
        )
        self.plus_btn = MDIconButton(
            icon="plus",
            theme_text_color="Custom",
            text_color=self.__theme_service.white_rgba,
            pos_hint={"center_x": 0.5, "center_y": 0.5},
        )

        self.label = MDLabel()
        self.label_value = MDLabel()
        self.metric = metric
        self.multiplier = multiplier
        self.slider = MDSlider()

        self.build(label, value, min_val, max_val, step)

    def update(self, settings, value, key):
        self.key = key
        self.__settings = settings
        self.slider.value = round(float(value), 5)
        self.label_value.text = (
            str(round(self.slider.value * self.multiplier, 5)) + " " + self.metric
        )

    def build(self, label: str, value, min_val, max_val, step):
        self.set_properties()

        self.build_label(label)
        self.build_label_value(value)
        self.labels_layout.add_widget(self.label)
        self.labels_layout.add_widget(self.label_value)

        self.build_slider(value, min_val, max_val, step)

        self.slider_layout.add_widget(self.minus_btn)
        self.slider_layout.add_widget(self.slider)
        self.slider_layout.add_widget(self.plus_btn)

        self.main_layout.add_widget(self.labels_layout)
        self.main_layout.add_widget(MDSeparator(padding=5, height=1))
        self.main_layout.add_widget(self.slider_layout)

        self.add_widget(self.main_layout)

    def set_properties(self):
        self.orientation = "vertical"
        self.border_radius = 20
        self.radius = [15]
        self.padding = 20
        self.md_bg_color = self.__theme_service.dark_secondary

    def build_slider(self, value, min, max, step):
        self.slider.value = round(float(value), 5)
        self.slider.min = min
        self.slider.max = max
        self.slider.step = step
        self.slider.hint = False
        self.slider.bind(value=self.on_slider_value)
        self.minus_btn.bind(on_press=lambda x: self.btn_callback())
        self.plus_btn.bind(on_press=lambda x: self.btn_callback(increment=True))

    def on_slider_value(self, instance, value):
        self.slider.value = round(float(value), 5)
        self.label_value.text = (
            str(round(self.slider.value * self.multiplier, 5)) + " " + self.metric
        )
        self.__settings[self.key] = self.slider.value

    def btn_callback(self, increment=False):
        step_val = round(float(self.slider.step), 5)

        if increment:
            if self.slider.value + step_val > self.slider.max:
                self.slider.value = self.slider.value
            else:
                self.slider.value += step_val
        else:
            if self.slider.value - step_val < self.slider.min:
                self.slider.value = self.slider.value
            else:
                self.slider.value -= step_val

        self.label_value.text = (
            str(round(self.slider.value * self.multiplier, 5)) + " " + self.metric
        )
        self.__settings[self.key] = self.slider.value

    def build_label_value(self, value: float):
        self.label_value.text = (
            str(round(value * self.multiplier, 5)) + " " + self.metric
        )
        self.label_value.theme_text_color = "Custom"
        self.label_value.text_color = self.__theme_service.primary_color
        self.label_value.font_style = "H6"
        self.label_value.font_size = "25sp"
        self.label_value.halign = "right"

    def build_label(self, text: str):
        self.label.text = text
        self.label.font_style = "Overline"
        self.label.font_size = "15sp"
        self.label.theme_text_color = "Primary"


class Action(Enum):
    NONE = 0
    PLC_START = 10
    PLC_STOP = 20
    CAMERA_START = 30
    CAMERA_STOP = 40
    REFERENCE = 50
    DETECT = 60
    VALIDATE = 70


class IconListItem(OneLineIconListItem):
    text = StringProperty()
    icon = StringProperty()
    text_color = ListProperty((0, 0, 0, 1))


class ActionListItem(OneLineIconListItem):
    text = StringProperty()
    icon = StringProperty()
    action = StringProperty(Action.NONE.name)
    text_color = ListProperty((0, 0, 0, 1))


class MainApp(MDApp):
    def __init__(
        self,
        config_options,
        plc_func,
        camera_func,
        settings_func,
        inc_ref,
        detect,
        validate,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.theme_service = ThemeService()

        self.menu = MDDropdownMenu()

        self.__options = []
        for option in config_options:
            self.__options.append(
                IconListItem(
                    text=option, icon="cog", text_color=self.theme_service.white_rgba
                )
            )

        self.__selected = config_options[0]

        self.__validate = validate
        self.__detect = detect
        self.__inc_reference = inc_ref
        self.__set_plc_func = plc_func
        self.__set_camera_func = camera_func
        self.__set_settings_func = settings_func

        self.__action_options = self.get_action_item_list()

        self.__settings_grid = SettingsSliderGrid()
        self.__advanced_settings_grid = SettingsSliderGrid()
        self.__processing_settings_grid = SettingsSliderGrid()

        self.__settings = settings_helper.DEFAULT_DICT

    def build(self):
        Window.size = (1200, 750)
        self.theme_cls = self.theme_service.set_theme(dark=True)
        return Builder.load_string(KV)

    def on_start(self):
        self.load_nav()
        self.load_dropdown()
        self.load_actions_dropdown()
        self.load_settings()
        self.load_settings_grids()

    def get_action_item_list(self) -> List[ActionListItem]:
        return [
            ActionListItem(
                text="KAMERA",
                icon="play",
                action=Action.CAMERA_START.name,
                text_color=self.theme_service.success_color,
            ),
            ActionListItem(
                text="KAMERA",
                icon="stop",
                action=Action.CAMERA_STOP.name,
                text_color=self.theme_service.error_color,
            ),
            ActionListItem(
                text="PLC",
                icon="play",
                action=Action.PLC_START.name,
                text_color=self.theme_service.success_color,
            ),
            ActionListItem(
                text="PLC",
                icon="stop",
                action=Action.PLC_STOP.name,
                text_color=self.theme_service.error_color,
            ),
            ActionListItem(
                text="ETALONAS-RANKINIS",
                icon="card-search",
                action=Action.REFERENCE.name,
                text_color=self.theme_service.success_color,
            ),
            ActionListItem(
                text="APTIKIMAS-RANKINIS",
                icon="card-search",
                action=Action.DETECT.name,
                text_color=self.theme_service.success_color,
            ),
            ActionListItem(
                text="VALIDACIJA-RANKINIS",
                icon="card-search",
                action=Action.VALIDATE.name,
                text_color=self.theme_service.success_color,
            ),
        ]
    def save_settings(self):
        logger.info("[APP]: Saving settings for " + str(self.__selected))
        settings_reader.save_settings_to_file(self.__settings, self.__selected)
        self.__set_settings_func(self.__selected)

    def set_plc(self, on: bool = False):
        self.__set_plc_func(on)

    def set_camera(self, on: bool = False):
        self.__set_camera_func(on)

    def inc_references(self):
        self.__inc_reference()

    def load_settings_grids(self):
        self.root.ids.screen_manager.get_screen("settings_scr").add_widget(
            self.__settings_grid
        )

        self.root.ids.screen_manager.get_screen("advanced_settings_scr").add_widget(
            self.__advanced_settings_grid
        )

        self.root.ids.screen_manager.get_screen("processing_settings_scr").add_widget(
            self.__processing_settings_grid
        )

    def load_dropdown(self):
        menu_items = [
            {
                "text": f"{option.text}",
                "icon": f"{option.icon}",
                "text_color": option.text_color,
                "viewclass": "IconListItem",
                "height": 56,
                "on_release": lambda x=option.text: self.dropdown_callback(x),
            }
            for option in self.__options
        ]

        self.menu = MDDropdownMenu(
            items=menu_items,
            width_mult=4,
        )

    def load_actions_dropdown(self):
        action_items = [
            {
                "text": f"{option.text}",
                "icon": f"{option.icon}",
                "text_color": option.text_color,
                "viewclass": "ActionListItem",
                "height": 56,
                "on_press": lambda x=option.action: self.action_callback(x),
            }
            for option in self.__action_options
        ]

        self.actions_menu = MDDropdownMenu(items=action_items, width_mult=4)

    def open_settings_dropdown(self, button):
        self.menu.caller = button
        self.menu.open()

    def open_actions_dropdown(self, button):
        self.actions_menu.caller = button
        self.actions_menu.open()

    def action_callback(self, selected):
        if Action[selected] is Action.CAMERA_START:
            self.__set_camera_func(True)
        elif Action[selected] is Action.CAMERA_STOP:
            self.__set_camera_func(False)
        elif Action[selected] is Action.PLC_START:
            self.__set_plc_func(True)
        elif Action[selected] is Action.PLC_STOP:
            self.__set_plc_func(False)
        elif Action[selected] is Action.REFERENCE:
            self.__inc_reference()
        elif Action[selected] is Action.DETECT:
            self.__detect()
        elif Action[selected] is Action.VALIDATE:
            self.__validate()

        self.actions_menu.dismiss()

    def dropdown_callback(self, selected):
        self.menu.dismiss()

        self.__selected = selected
        self.__settings.update(settings_reader.read_settings(selected))
        self.__settings_grid.update(self.__settings)
        self.__advanced_settings_grid.update(self.__settings)
        self.__processing_settings_grid.update(self.__settings)

        Snackbar(text=selected).open()

    def load_settings(self):
        settings_vm = settings_helper.default_settings()
        self.__settings.update(settings_reader.read_settings(self.__selected))
        settings_helper.update_settings_from_dict(settings_vm, self.__settings)

        for setting in settings_vm[0]["settings"]:
            slider_card = SettingsSliderCard(
                        setting["label"],
                        setting["value"],
                        setting["metric"],
                        setting["val_mult"],
                        setting["min_val"],
                        setting["max_val"],
                        setting["step"],
                        self.theme_service,
                        self.__settings,
                        setting["name"],
            )
            if setting["type"] is settings_helper.SettingType.ADVANCED.value:
                self.__advanced_settings_grid.add_widget(slider_card)
            elif setting["type"] is settings_helper.SettingType.PROCESSING.value:
                self.__processing_settings_grid.add_widget(slider_card)
            else:
                self.__settings_grid.add_widget(slider_card)

    def load_nav(self):
        icons_item = {
            "cog": ["Nustatymai", "settings_scr"],
            "account-cog": ["Išplėstiniai nustatymai", "advanced_settings_scr"],
            "database-cog": ["Apdorojimo nustatymai", "processing_settings_scr"],
        }
        
        for icon_name in icons_item.keys():
            item_drawer = ItemDrawer(
                    icon=icon_name,
                    text=icons_item[icon_name][0],
                    to_screen=icons_item[icon_name][1],
                    text_color=self.theme_service.text_color,
            )
            item_drawer.load_functions = []
            self.root.ids.content_drawer.ids.nav_list.add_widget(item_drawer)
