"""
This file is the main object running the KarelCraft application.

Author : Melvin Cabatuan
ThanksTo: pokepetter (Ursina)
         Nicholas Bowman, Kylie Jue, Tyler Yep (stanfordkarel module)
         clear-code-projects (Minecraft-in-Python)
         StanislavPetrovV
License: MIT
Version: 1.0.0
Date of Creation: 5/17/2021
"""
from ursina import *
from karelcraft.entities.karel import Karel
from karelcraft.entities.file_browser_save import FileBrowserSave
from karelcraft.entities.video_recorder import VideoRecorder
from karelcraft.utils.helpers import vec2tup, vec2key, KarelException
from karelcraft.utils.student_code import StudentCode
from karelcraft.utils.world_loader import COLOR_LIST, TEXTURE_LIST
from karelcraft.utils.control_panel import ControlPanel


import sys
import webbrowser
import random
from pathlib import Path
from time import sleep
from typing import Callable

BLOCKS_PATH = 'assets/blocks/'
REPO_PATH = 'https://github.com/melvincabatuan/KarelCraft'


class App(Ursina):

    def __init__(self, code_file: Path, world_file: str, development_mode=False) -> None:
        super().__init__()
        self._setup_texture()
        self.karel = Karel(world_file, self.textures)
        self.world = self.karel.world
        self.code_file = code_file
        self.create_mode = ''  # default: None
        self.color_name = random.choice(COLOR_LIST)
        self._setup_code()
        self._setup_controls()
        self._setup_menu()
        self._setup_sound_lights_cam()
        self._setup_window()

    def _setup_window(self) -> None:
        window.color = color.black
        window.borderless = False
        window.exit_button.visible = False
        window.fps_counter.enabled = False
        window.cog_menu.enabled = False

    def _setup_texture(self):
        default_texture_path = Path(__file__).absolute().parent.parent / BLOCKS_PATH
        self.textures = {
            texture_path.stem.split('_')[0]: load_texture(BLOCKS_PATH + texture_path.stem + '.png')
            for texture_path in default_texture_path.glob("*.png")
        }
        self.texture_names = list(self.textures.keys())
        self.texture_name = random.choice(self.texture_names)
        self.block_texture = self.textures.get(self.texture_name, 'grass')

    def _setup_code(self) -> None:
        self.student_code = StudentCode(self.code_file)
        self.student_code.inject_namespace(self.karel)
        self.inject_decorator_namespace()
        self.run_code = False

    def _setup_sound_lights_cam(self):
        self.move_sound = Audio('assets/sounds/move.mp3', autoplay=False)  # loop = True,
        self.destroy_sound = Audio('assets/sounds/destroy.wav', autoplay=False)
        self.mute = False
        Light(type='ambient', color=(0.6, 0.6, 0.6, 1))
        Light(type='directional', color=(0.6, 0.6, 0.6, 1), direction=(1, 1, 1))
        EditorCamera(rotation_speed=25)  # lessen angle adjustment
        self.set_3d()
        # Video Recorder
        self.vr = VideoRecorder(name=self.student_code.module_name, duration=10)

    def _setup_controls(self) -> None:
        self.ui = ControlPanel()
        # run, top, and reset
        self.ui.run_button.on_click = self.set_run_code
        self.ui.stop_button.on_click = self.stop_code
        self.ui.reset_button.on_click = self.reset

        # camera view: 2d vs 3d
        def handle_view() -> None:
            if self.ui.view_button.value[0] == '3D':
                self.set_3d()
            else:
                self.set_2d()
        self.ui.view_button.on_value_changed = handle_view

        # speed slider
        self.ui.set_speed_control(self.world.speed)

        def handle_speed() -> None:
            self.world.speed = self.ui.speed_slider.value
        self.ui.speed_slider.on_value_changed = handle_speed

        # world selector
        self.ui.world_selector(self.world.world_list, self.load_world)

        # prompt text
        self.ui.init_prompt(window.center, vec2tup(self.karel.position), self.karel.direction.name)

    def _setup_menu(self) -> None:
        # color selector
        def change_color(color_name):
            self.color_name = color_name
            self.ui.color_selector.enabled = False
        self.ui.set_color_chooser(COLOR_LIST, change_color)

        # cog menu
        func_dict = {
            'Save World State <gray>[ctrl+s]<default>': self.save_world,
            'Change Texture <gray>[0 to 9]<default>': self.set_texture,
            'Change Render Mode <gray>[F10]<default>': window.next_render_mode,
            'Camera 3D View <gray>[P/Page Up]<default>': self.set_3d,
            'Camera 2D View <gray>[P/Page Down]<default>': self.set_2d,
            'Select color': self.ui.enable_color_menu,
            'Karelcraft Repo': Func(webbrowser.open, REPO_PATH),
        }
        self.ui.setup_menu(func_dict)

    def clear_objects(self) -> None:
        to_destroy = [e for e in scene.entities
                      if e.name == 'voxel' or e.name == 'paint'
                      or e.name == 'beeper' or e.name == 'wall']
        # to_destroy.append(self.karel.agent_txt)
        for d in to_destroy:
            try:
                destroy(d)
            except Exception as e:
                print('failed to destroy entity', e)

    def reset(self) -> None:
        '''
        Resets the environment to an initial state and
        returns an initial observation.
        '''
        self.clear_objects()
        self.karel.reset()

    def set_3d(self) -> None:
        span = self.world.get_maxside()
        x_center, y_center = self.world.get_center()
        y_pos = min(-1.6 * span, -12.7)
        z_pos = min(-1.4 * span, -12)
        camera.position = (x_center, y_pos, z_pos)
        camera.rotation_x = -55
        self.ui.view_button.select(self.ui.view_button.buttons[1])

    def set_2d(self) -> None:
        camera.rotation_x = 0
        span = self.world.get_maxside()
        z_pos = min(-3 * span, -10)
        x_center, y_center = self.world.get_center()
        camera.position = (x_center, y_center, z_pos)
        self.ui.view_button.select(self.ui.view_button.buttons[0])

    def set_texture(self, key=None) -> None:
        if key is None:
            self.texture_name = random.choice(self.texture_names)
        else:
            self.texture_name = self.texture_names[int(key) - 1]
        # self.block_texture = self.textures[self.texture_name]

    def set_run_code(self) -> None:
        self.run_code = True
        self.ui.run_button.disabled = True

    def stop_code(self) -> None:
        self.run_code = False
        self.ui.stop_button.disabled = True

    def load_world(self, world_file: str) -> None:
        '''
        Loads a world, i.e. world_file, from ./karelcraft/worlds/ directory
        Destroy existing entities except UI, then, recreate them
        '''
        to_destroy = [e for e in scene.entities
                      if e.name == 'voxel' or e.name == 'paint' or
                      e.name == 'beeper' or e.name == 'wall' or
                      e.name == 'karel' or e.name == 'world']
        for d in to_destroy:
            try:
                destroy(d)
            except Exception as e:
                print('failed to destroy entity', e)
        del self.karel
        self.karel = Karel(world_file, self.textures)
        self.world = self.karel.world
        self._setup_code()
        self.world.speed = self.ui.speed_slider.value
        self.set_3d()
        msg = f'Position : {vec2tup(self.karel.position)}; Direction: {self.karel.direction.name}'
        self.ui.update_prompt(vec2tup(self.karel.position),
                              self.karel.direction.name,
                              msg)

    def save_world(self) -> None:
        wp = FileBrowserSave(file_type='.w')
        try:
            wp.path = Path('./karelcraft/worlds/')
            wp.data = self.get_world_state()
        except Exception:  # use current dir instead
            print(f"Can't find the directory {wp.path}. Using current directory...")
            wp.data = self.get_world_state()

    def get_world_state(self) -> str:
        world_state = f"Karel: {vec2key(self.karel.position)}; "
        world_state += f"{self.karel.direction.name.title()}\n"
        world_state += f"Dimension: ({self.world.size.col}, {self.world.size.row})\n"
        beeper_output = (
            self.karel.num_beepers
            if self.karel.start_beeper_count >= 0
            else "INFINITY"
        )
        world_state += f"BeeperBag: {beeper_output}\n"

        for key in sorted(self.world.stacks.keys()):
            if self.world.all_beepers(key):
                world_state += f"Beeper: ({key[0]}, {key[1]}); {self.world.count_beepers(key)}\n"
            elif self.world.all_same_blocks(key):
                texture_name = self.world.top_in_stack(key).texture_name
                world_state += f"Block: ({key[0]}, {key[1]}); {texture_name}; "
                world_state += f"{self.world.count_blocks(key)}\n"
            elif self.world.all_colors(key):
                color_name = self.world.corner_color((key[0], key[1], 0))
                world_state += f"Color: ({key[0]}, {key[1]}); {color_name}\n"
            elif self.world.stacks.get(key, []):
                world_state += f"Stack: ({key[0]}, {key[1]}); {self.world.stack_string(key)}\n"

        for wall in sorted(self.world.walls):
            world_state += f"Wall: ({wall.col}, {wall.row}); {wall.direction.name.title()}\n"

        return world_state

    def destroy_item(self) -> None:
        '''
        Destroys the item - voxel, beeper, paint - hovered by the mouse
        Logic: You can only destroy the top of the stack
        '''
        if to_destroy := mouse.hovered_entity:
            pos_to_destroy = to_destroy.position
            if not self.mute:
                self.destroy_sound.play()
            if to_destroy == self.world.top_in_stack(pos_to_destroy):
                if to_destroy.name == 'voxel':
                    self.world.remove_voxel(pos_to_destroy)
                elif to_destroy.name == 'beeper':
                    self.world.remove_beeper(pos_to_destroy)
                elif to_destroy.name == 'paint':
                    self.world.remove_color(pos_to_destroy)
                if vec2key(pos_to_destroy) == vec2key(self.karel.position):
                    self.karel.update_z()

    def create_item(self) -> None:
        '''
        Create an item in agent's position
        '''
        if self.create_mode == 'voxel':
            self.karel.put_block(self.texture_name)
            agent_action = 'put_block() => ' + self.texture_name
        elif self.create_mode == 'paint_color':
            self.karel.paint_corner(self.color_name)
            agent_action = 'paint_corner() => ' + self.color_name
        elif self.create_mode == 'beeper':
            num = self.world.add_beeper(self.karel.position)
            agent_action = f'add_beeper() => {num}'
        else:  # create nothing
            return
        self.karel.update_z()
        self.ui.update_prompt(vec2tup(self.karel.position),
                              self.karel.direction.name,
                              agent_action)

    def input(self, key) -> None:
        '''
        Handles user input:
            - Agent movement: wasd or arrows keys
            - Increase / Decrease speed: = / -
            - Choose texture: 1 to 9
            - Change camera: Page Up/ Page Down
            - Run code: r
            - Clear objects: c
            - Emergency stop: escape
            - Save world state: ctrl + s
            - Destroy objects: left mouse or mouse1
        '''
        if key == 'w' or key == 'a' or key == 's' or key == 'd' \
                or key == 'arrow_up' or key == 'arrow_down' \
                or key == 'arrow_left' or key == 'arrow_right':
            # Manual Movement
            action, is_valid = self.karel.user_action(key)
            msg = '\tturn_left()'
            error_msg = ''
            if action == 'move()':
                msg = '\tmove()'
            if not is_valid:
                error_msg = '\t\t  ERROR: Invalid move()!'
            self.ui.update_prompt(vec2tup(self.karel.position),
                                  self.karel.direction.name,
                                  msg,
                                  error_msg)
            if not self.mute:
                self.move_sound.play()
        elif key == '=':
            print("Make faster...")
            self.world.speed = min(self.world.speed + 0.05, 1.0)
        elif key == '-':
            print("Make slower...")
            self.world.speed = max(self.world.speed - 0.05, 0.0)
        elif key.isdigit() and '1' <= key <= '9':
            self.set_texture(key)
        elif key == 'page_down':
            self.set_3d()
        elif key == 'page_up':
            self.set_2d()
        elif key == 'b':  # beeper
            self.create_mode = 'beeper'
        elif key == 'backspace':  # clear
            self.clear_objects()
        elif key == 'c':  # paint color
            self.create_mode = 'paint_color'
        elif key == 'r':  # run student code
            self.set_run_code()
        elif key == 'v':  # paint
            self.create_mode = 'voxel'
        elif key == 'escape':
            print("Manual mode: press wasd or arrow keys to move")
            sys.exit()  # Manual mode
        elif key == 'control-s':
            self.save_world()
        elif key == 'mouse1':  # left click
            self.destroy_item()
        elif key == 'mouse3':  # right click
            self.create_item()
        elif key == 'm':  # mute
            self.mute = True
        elif key == 'space':
            self.vr.recording = True
            self.vr.convert_to_gif()

        super().input(key)

    def end_frame(self, msg) -> None:
        self.ui.update_prompt(vec2tup(self.karel.position),
                              self.karel.direction.name,
                              msg)
        if not self.mute:
            self.move_sound.play()
        if not self.run_code:
            sys.exit()
        taskMgr.step()  # manual step Panda3D loop
        sleep(1 - self.world.speed)  # delay by specified amount

    def karel_action_decorator(
        self, karel_fn: Callable[..., None]
    ) -> Callable[..., None]:
        def wrapper() -> None:
            karel_fn()  # execute Karel function
            self.end_frame('\t' + karel_fn.__name__ + '()')
        return wrapper

    def corner_action_decorator(
        self, karel_fn: Callable[..., None]
    ) -> Callable[..., None]:
        def wrapper(color: str = color.random_color()) -> None:
            karel_fn(color)
            self.end_frame(karel_fn.__name__ + f'("{color}")')
        return wrapper

    def beeper_action_decorator(
        self, karel_fn: Callable[..., None]
    ) -> Callable[..., None]:
        def wrapper() -> None:
            num_beepers = karel_fn()
            self.end_frame(karel_fn.__name__ + '() => ' + str(num_beepers))
        return wrapper

    def block_action_decorator(
        self, karel_fn: Callable[..., None]
    ) -> Callable[..., None]:
        def wrapper(block_texture: str = TEXTURE_LIST[0]) -> None:
            karel_fn(block_texture)
            self.end_frame(f'{karel_fn.__name__}() => {block_texture}')
        return wrapper

    def karel_reset_decorator(
        self, karel_fn: Callable[..., None]
    ) -> Callable[..., None]:
        def wrapper(new_position: tuple = None) -> None:
            self.clear_objects()
            new_position = karel_fn(new_position)  # execute Karel function
            self.end_frame('\treset()')
            return new_position
        return wrapper

    def karel_prompt_decorator(
        self, karel_fn: Callable[..., None]
    ) -> Callable[..., None]:
        def wrapper(msg: str) -> None:
            karel_fn(msg)
            taskMgr.step()  # manual step Panda3D loop
            sleep(1 - self.world.speed)
        return wrapper

    def inject_decorator_namespace(self) -> None:
        """
        This function associates the generic commands in student code
        to KarelCraft functions. (Credits: stanford.karel module)
        """
        self.student_code.mod.turn_left = self.karel_action_decorator(
            self.karel.turn_left
        )
        self.student_code.mod.turn_right = self.karel_action_decorator(
            self.karel.turn_right
        )
        self.student_code.mod.move = self.karel_action_decorator(
            self.karel.move
        )
        self.student_code.mod.put_beeper = self.beeper_action_decorator(
            self.karel.put_beeper
        )
        self.student_code.mod.pick_beeper = self.beeper_action_decorator(
            self.karel.pick_beeper
        )
        self.student_code.mod.paint_corner = self.corner_action_decorator(
            self.karel.paint_corner
        )
        self.student_code.mod.put_block = self.block_action_decorator(
            self.karel.put_block
        )
        self.student_code.mod.destroy_block = self.karel_action_decorator(
            self.karel.destroy_block
        )
        self.student_code.mod.remove_paint = self.karel_action_decorator(
            self.karel.remove_paint
        )
        self.student_code.mod.reset = self.karel_reset_decorator(
            self.karel.reset
        )
        self.student_code.mod.prompt = self.karel_prompt_decorator(
            self.karel.prompt
        )

    def run_student_code(self) -> None:
        window.title = 'Running ' + self.student_code.module_name + '.py'
        # base.win.requestProperties(window)
        self.ui.stop_button.disabled = False
        try:
            self.student_code.mod.main()
        except KarelException as e:
            self.ui.update_prompt(vec2tup(self.karel.position),
                                  self.karel.direction.name,
                                  e.action,
                                  e.message)
            self.run_code = False
            self.ui.run_button.disabled = False
        except Exception as e:
            print(e)
        except SystemExit:  # ignore traceback on exit
            pass
        self.ui.run_button.disabled = False

    def run_program(self) -> None:
        try:
            # Update the title
            window.title = self.student_code.module_name + \
                ' : Manual mode - Use WASD or Arrow keys to control agent'
            window.center_on_screen()
            base.win.requestProperties(window)

            while True:
                taskMgr.step()
                if self.run_code:
                    self.run_student_code()
                    self.run_code = False
        except SystemExit:  # ignore traceback on exit
            pass
        except Exception as e:
            print(e)

    def finalizeExit(self) -> None:
        """
        Called by `userExit()` to quit the application.
        """
        base.graphicsEngine.removeAllWindows()
        if self.win is not None:
            print("Exiting KarelCraft app, bye!")
            self.closeWindow(self.win)
            self.win = None
        self.destroy()
        sys.exit()
