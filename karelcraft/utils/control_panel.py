from ursina import *
from karelcraft.entities.cog_menu import CogMenu
from karelcraft.entities.radial_menu import RadialMenu, RadialMenuButton
from karelcraft.entities.dropdown_menu import DropdownMenu, DropdownMenuButton

TITLE = 'KarelCraft'


class ControlPanel:
    def __init__(self) -> None:
        self.set_main_buttons()
        self.set_view_button()

    def set_main_buttons(self) -> None:
        # Run button:
        self.run_button = Button(
            model='circle',
            position=(-0.75, 0.36),
            text='Run',
            color=color.gray,
            pressed_color=color.green,
            parent=camera.ui,
            eternal=True,
            scale=0.064,
        )
        self.run_button.text_entity.scale = 0.7
        self.run_button.tooltip = Tooltip('Run Student Code')

        # Stop button:
        self.stop_button = Button(
            model='circle',
            position=(-0.75, 0.28),
            text='Stop',
            color=color.gray,
            pressed_color=color.red,
            parent=camera.ui,
            eternal=True,
            scale=0.064,
        )
        self.stop_button.text_entity.scale = 0.7
        self.stop_button.tooltip = Tooltip('Stop Student Code')

        # Reset button:
        self.reset_button = Button(
            model='circle',
            position=(-0.75, 0.20),
            text='Reset',
            color=color.gray,
            pressed_color=color.yellow,
            parent=camera.ui,
            eternal=True,
            scale=0.064,
        )
        self.reset_button.text_entity.scale = 0.7
        self.reset_button.tooltip = Tooltip('Reset the world')

    def setup_menu(self, func_dict) -> None:
        self.menu = CogMenu(func_dict)
        self.menu.on_click = Func(setattr, self.menu, 'enabled', False)
        self.menu.eternal = True

    def set_view_button(self) -> None:
        # Camera button:
        self.view_button = ButtonGroup(('2D', '3D'),
                                       min_selection=1,
                                       x=-0.8, y=0.13,
                                       default='3D',
                                       selected_color=color.green,
                                       parent=camera.ui,
                                       eternal=True,
                                       )
        self.view_button.scale *= 0.85

    def set_speed_control(self, world_speed) -> None:
        # Slider
        self.speed_slider = ThinSlider(0.0, 1.0,
                                       default=world_speed,
                                       step=0.02,
                                       text='Speed',
                                       dynamic=True,
                                       position=(-0.75, -0.4),
                                       vertical=True,
                                       parent=camera.ui,
                                       eternal=True,
                                       )
        self.speed_slider.scale *= 0.85
        self.speed_slider.bg.color = color.white66
        self.speed_slider.knob.color = color.green

    def world_selector(self, world_list, load_world) -> None:
        # world selector:
        button_list = []
        for w in world_list:
            drop_button = DropdownMenuButton(w)
            drop_button.on_click = lambda w=w: load_world(w)
            button_list.append(drop_button)
        # world selector
        DropdownMenu('Load World',
                     buttons=button_list,
                     position=(0.52, 0.48),
                     eternal=True,
                     )

    def set_color_chooser(self, color_list, change_color) -> None:
        radial_list = []
        for k in color_list:
            color_button = RadialMenuButton(scale=.4, color=color.colors[k])
            color_button.on_click = lambda k=k: change_color(k)
            radial_list.append(color_button)
        self.color_selector = RadialMenu(
            buttons=(radial_list),
            enabled=False,
            eternal=True,
        )

    def enable_color_menu(self) -> None:
        self.color_selector.enabled = True

    def init_prompt(self, center, agent_position, direction_name) -> None:
        Text(TITLE,
             position=center + Vec2(-0.14, 0.48),
             scale=2,
             parent=camera.ui,
             eternal=True,
             )
        msg = f'Position : {agent_position}; Direction: {direction_name}'
        self.prompt = Text(msg,
                           position=center + Vec2(-0.36, -0.43),
                           scale=1,
                           parent=camera.ui
                           )

    def update_prompt(self, agent_pos, direction_name, agent_action, error_message=None) -> None:
        msg = f'''           \t {agent_action}
        \t Position @ {(agent_pos[:2])+(abs(agent_pos[-1]),)} ==> {direction_name}
        '''
        self.prompt.color = color.white
        if error_message:
            msg = error_message + '\n' + '\t' + msg.split('\n')[1]
            self.prompt.color = color.red
        self.prompt.text = msg
