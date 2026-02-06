from kivy.app import App
from kivy.uix.gridlayout import GridLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle, RoundedRectangle
from kivy.clock import Clock
from kivy.animation import Animation
from kivy.properties import StringProperty, BooleanProperty, NumericProperty
import math
from typing import Optional, Callable, Dict, List, Tuple
from enum import Enum

class AngleMode(Enum):
    DEGREES = 'deg'
    RADIANS = 'rad'

class Theme(Enum):
    DARK = 'dark'
    LIGHT = 'light'
    BLUE = 'blue'

COLORS = {
    'slate_blue': (0.239, 0.353, 0.502, 1),
    'space_cadet': (0.161, 0.196, 0.255, 1),
    'burnt_orange': (0.933, 0.424, 0.302, 1),
    'eerie_black': (0.102, 0.102, 0.102, 1),
    'label_color': (0.878, 0.984, 0.988, 1),
    'hover': (0.306, 0.431, 0.588, 1),
    'dark_bg': (0.08, 0.08, 0.08, 1),
    'active': (0.4, 0.6, 0.8, 1),
    'error': (0.933, 0.424, 0.302, 1),
    'success': (0.2, 0.8, 0.4, 1),
    'memory': (0.6, 0.4, 0.8, 1)
}

THEMES = {
    Theme.DARK: {
        'bg': (0.08, 0.08, 0.08, 1),
        'display': (0.102, 0.102, 0.102, 1),
        'num': (0.161, 0.196, 0.255, 1),
        'op': (0.239, 0.353, 0.502, 1),
        'special': (0.933, 0.424, 0.302, 1),
        'text': (0.878, 0.984, 0.988, 1)
    },
    Theme.LIGHT: {
        'bg': (0.95, 0.95, 0.95, 1),
        'display': (1, 1, 1, 1),
        'num': (0.9, 0.9, 0.92, 1),
        'op': (0.7, 0.8, 0.9, 1),
        'special': (0.933, 0.624, 0.502, 1),
        'text': (0.1, 0.1, 0.1, 1)
    },
    Theme.BLUE: {
        'bg': (0.05, 0.1, 0.2, 1),
        'display': (0.08, 0.15, 0.25, 1),
        'num': (0.15, 0.25, 0.4, 1),
        'op': (0.2, 0.4, 0.6, 1),
        'special': (0.8, 0.3, 0.5, 1),
        'text': (0.9, 0.95, 1, 1)
    }
}

class CalculatorButton(Button):
    def __init__(self, **kwargs):
        kwargs.setdefault('markup', True)
        kwargs.setdefault('bold', True)
        super().__init__(**kwargs)
        
        self.original_color = kwargs.get('background_color', (1, 1, 1, 1))
        self.background_normal = ''
        
    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            Animation(background_color=COLORS['hover'], duration=0.1).start(self)
        return super().on_touch_down(touch)
    
    def on_touch_up(self, touch):
        if self.collide_point(*touch.pos):
            Animation(background_color=self.original_color, duration=0.15).start(self)
        return super().on_touch_up(touch)

    def flash(self):
        original = self.background_color
        self.background_color = COLORS['active']
        Clock.schedule_once(lambda dt: setattr(self, 'background_color', original), 0.15)
    
    def update_theme(self, color: tuple):
        self.original_color = color
        self.background_color = color

class Calculator(BoxLayout):
    display_text = StringProperty("0")
    history_text = StringProperty("")
    error_state = BooleanProperty(False)
    
    MAX_DIGITS = 15
    MAX_HISTORY = 100
    OPERATIONS = {"/": "÷", "*": "×", "-": "−", "+": "+", "**": "^"}
    
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', **kwargs)
        
        self.total_expression = ""
        self.current_expression = ""
        self.last_result: Optional[float] = None
        self.calculation_history: List[str] = []
        
        self.memory_value = 0.0
        self.has_memory = False
        
        self.scientific_mode = False
        self.angle_mode = AngleMode.DEGREES
        self.pending_function: Optional[str] = None
        self.custom_root_mode = False
        self.root_power_value: Optional[float] = None
        
        self.current_theme = Theme.DARK
        self.btns_dict: Dict[str, CalculatorButton] = {}
        
        self._setup_canvas()
        self._create_ui()
        self._setup_keyboard()
        
    def _setup_canvas(self):
        with self.canvas.before:
            Color(*THEMES[self.current_theme]['bg'])
            self.bg_rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._update_bg, size=self._update_bg)
    
    def _update_bg(self, *args):
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size
    
    def _create_ui(self):
        self._create_top_menu()
        self._create_display()
        self._create_buttons()
        self._create_help_label()
    
    def _setup_keyboard(self):
        Window.bind(on_key_down=self._on_keyboard_down)
        self._keyboard = Window.request_keyboard(lambda: None, self)
    
    def _create_top_menu(self):
        menu_layout = BoxLayout(size_hint=(1, 0.06), spacing=5, padding=[10, 5, 10, 0])
        
        theme_colors = THEMES[self.current_theme]
        
        self.history_btn = CalculatorButton(
            text="History",
            font_size='14sp',
            background_color=theme_colors['op'],
            color=theme_colors['text']
        )
        self.history_btn.bind(on_press=lambda x: self.show_history())
        
        self.theme_btn = CalculatorButton(
            text="Theme",
            font_size='14sp',
            background_color=theme_colors['op'],
            color=theme_colors['text']
        )
        self.theme_btn.bind(on_press=lambda x: self.cycle_theme())
        
        self.mode_btn = CalculatorButton(
            text="Scientific",
            font_size='14sp',
            background_color=theme_colors['op'],
            color=theme_colors['text']
        )
        self.mode_btn.bind(on_press=lambda x: self.toggle_scientific_mode())
        
        menu_layout.add_widget(self.history_btn)
        menu_layout.add_widget(self.theme_btn)
        menu_layout.add_widget(self.mode_btn)
        
        self.add_widget(menu_layout)
    
    def _create_display(self):
        display_layout = GridLayout(cols=1, rows=3, size_hint=(1, 0.24), 
                                    spacing=3, padding=[10, 5, 10, 5])
        
        theme_colors = THEMES[self.current_theme]
        
        self.memory_label = Label(
            text="",
            font_size='12sp',
            halign='left',
            valign='middle',
            color=COLORS['memory'],
            opacity=0.8
        )
        self.memory_label.bind(size=self.memory_label.setter('text_size'))
        
        self.total_label = Label(
            text="", 
            font_size='16sp', 
            halign='right', 
            valign='middle', 
            color=theme_colors['text'],
            opacity=0.7,
            markup=True
        )
        
        self.label = Label(
            text="0", 
            font_size='42sp', 
            bold=True, 
            halign='right', 
            valign='middle', 
            color=theme_colors['text']
        )
        
        for lbl in [self.memory_label, self.total_label, self.label]:
            lbl.bind(size=lbl.setter('text_size'))
            with lbl.canvas.before:
                Color(*theme_colors['display'])
                lbl.bg_rect = RoundedRectangle(pos=lbl.pos, size=lbl.size, radius=[10])
            lbl.bind(pos=self._update_label_rect, size=self._update_label_rect)
            display_layout.add_widget(lbl)
        
        self.add_widget(display_layout)

    def _update_label_rect(self, instance, value):
        instance.bg_rect.pos = instance.pos
        instance.bg_rect.size = instance.size
    
    def _create_help_label(self):
        help_layout = BoxLayout(size_hint=(1, 0.035), padding=[10, 0, 10, 5])
        self.help_label = Label(
            text="Keyboard: 0-9, +−×÷*/, Enter, Backspace, Esc, %, C | Memory: M+, M-, MR, MC",
            font_size='10sp',
            halign='center',
            valign='middle',
            color=(0.5, 0.5, 0.5, 1),
            opacity=0.7
        )
        self.help_label.bind(size=self.help_label.setter('text_size'))
        help_layout.add_widget(self.help_label)
        self.add_widget(help_layout)
    
    def _create_buttons(self):
        btns_container = BoxLayout(
            orientation='vertical', 
            size_hint=(1, 0.645), 
            spacing=2, 
            padding=[10, 5, 10, 10]
        )
        
        if self.scientific_mode:
            self._create_scientific_buttons(btns_container)
        else:
            self._create_standard_buttons(btns_container)
        
        self.add_widget(btns_container)
        self.btns_container = btns_container
    
    def _create_standard_buttons(self, container: BoxLayout):
        theme_colors = THEMES[self.current_theme]
        
        memory_row = BoxLayout(orientation='horizontal', spacing=2, size_hint=(1, 0.15))
        memory_btns = [
            ('MC', theme_colors['op'], self.memory_clear),
            ('MR', theme_colors['op'], self.memory_recall),
            ('M+', theme_colors['op'], self.memory_add),
            ('M-', theme_colors['op'], self.memory_subtract)
        ]
        
        for txt, clr, func in memory_btns:
            btn = self._create_button(txt, clr, func, font_size='16sp')
            btn.size_hint_x = 0.25
            memory_row.add_widget(btn)
            self.btns_dict[txt] = btn
        
        container.add_widget(memory_row)
        
        top_grid = GridLayout(cols=4, spacing=2, size_hint=(1, 0.7))
        
        main_btns = [
            ('C', theme_colors['op'], self.clear), 
            ('DEL', theme_colors['op'], self.backspace), 
            ('%', theme_colors['op'], self.percentage), 
            ('÷', theme_colors['op'], lambda: self.append_operator("/")),
            ('7', theme_colors['num'], lambda: self.add_to_expression('7')), 
            ('8', theme_colors['num'], lambda: self.add_to_expression('8')), 
            ('9', theme_colors['num'], lambda: self.add_to_expression('9')), 
            ('×', theme_colors['op'], lambda: self.append_operator("*")),
            ('4', theme_colors['num'], lambda: self.add_to_expression('4')), 
            ('5', theme_colors['num'], lambda: self.add_to_expression('5')), 
            ('6', theme_colors['num'], lambda: self.add_to_expression('6')), 
            ('−', theme_colors['op'], lambda: self.append_operator("-")),
            ('1', theme_colors['num'], lambda: self.add_to_expression('1')), 
            ('2', theme_colors['num'], lambda: self.add_to_expression('2')), 
            ('3', theme_colors['num'], lambda: self.add_to_expression('3')), 
            ('+', theme_colors['op'], lambda: self.append_operator("+"))
        ]
        
        for txt, clr, func in main_btns:
            btn = self._create_button(txt, clr, func)
            top_grid.add_widget(btn)
            self.btns_dict[txt] = btn
        
        container.add_widget(top_grid)
        
        bottom_row = BoxLayout(orientation='horizontal', spacing=2, size_hint=(1, 0.15))
        
        buttons = [
            ('±', theme_colors['op'], self.toggle_sign),
            ('0', theme_colors['num'], lambda: self.add_to_expression('0')),
            ('.', theme_colors['num'], lambda: self.add_to_expression(".")),
            ('=', theme_colors['special'], self.evaluate)
        ]
        
        for txt, clr, func in buttons:
            btn = self._create_button(txt, clr, func)
            btn.size_hint_x = 0.25
            bottom_row.add_widget(btn)
            self.btns_dict[txt] = btn
        
        self.btns_dict['/'] = self.btns_dict['÷']
        self.btns_dict['*'] = self.btns_dict['×']
        self.btns_dict['-'] = self.btns_dict['−']
        
        container.add_widget(bottom_row)
    
    def _create_scientific_buttons(self, container: BoxLayout):
        theme_colors = THEMES[self.current_theme]
        
        memory_row = BoxLayout(orientation='horizontal', spacing=2, size_hint=(1, 0.1))
        memory_btns = [
            ('MC', theme_colors['op'], self.memory_clear),
            ('MR', theme_colors['op'], self.memory_recall),
            ('M+', theme_colors['op'], self.memory_add),
            ('M-', theme_colors['op'], self.memory_subtract)
        ]
        
        for txt, clr, func in memory_btns:
            btn = self._create_button(txt, clr, func, font_size='13sp')
            btn.size_hint_x = 0.25
            memory_row.add_widget(btn)
            self.btns_dict[txt] = btn
        
        container.add_widget(memory_row)
        
        sci_rows = [
            [
                ('sin', theme_colors['op'], lambda: self.scientific_function('sin')),
                ('cos', theme_colors['op'], lambda: self.scientific_function('cos')),
                ('tan', theme_colors['op'], lambda: self.scientific_function('tan')),
                ('√', theme_colors['op'], lambda: self.scientific_function('sqrt'))
            ],
            [
                ('sin[sup]-1[/sup]', theme_colors['op'], lambda: self.scientific_function('asin')),
                ('cos[sup]-1[/sup]', theme_colors['op'], lambda: self.scientific_function('acos')),
                ('tan[sup]-1[/sup]', theme_colors['op'], lambda: self.scientific_function('atan')),
                ('[sup]n[/sup]√', theme_colors['op'], self.custom_root)
            ],
            [
                ('csc', theme_colors['op'], lambda: self.scientific_function('csc')),
                ('sec', theme_colors['op'], lambda: self.scientific_function('sec')),
                ('cot', theme_colors['op'], lambda: self.scientific_function('cot')),
                ('π', theme_colors['op'], lambda: self.add_constant('pi'))
            ],
            [
                ('x[sup]2[/sup]', theme_colors['op'], lambda: self.scientific_function('square')),
                ('x[sup]y[/sup]', theme_colors['op'], lambda: self.append_operator('**')),
                ('ln', theme_colors['op'], lambda: self.scientific_function('ln')),
                ('log', theme_colors['op'], lambda: self.scientific_function('log'))
            ]
        ]
        
        for row_btns in sci_rows:
            row = BoxLayout(orientation='horizontal', spacing=2, size_hint=(1, 0.1))
            for txt, clr, func in row_btns:
                btn = self._create_button(txt, clr, func, font_size='13sp')
                btn.size_hint_x = 0.25
                row.add_widget(btn)
                self.btns_dict[txt] = btn
            container.add_widget(row)
        
        main_grid = GridLayout(cols=4, spacing=2, size_hint=(1, 0.4))
        
        main_btns = [
            ('C', theme_colors['op'], self.clear), 
            ('DEL', theme_colors['op'], self.backspace), 
            ('%', theme_colors['op'], self.percentage), 
            ('÷', theme_colors['op'], lambda: self.append_operator("/")),
            ('7', theme_colors['num'], lambda: self.add_to_expression('7')), 
            ('8', theme_colors['num'], lambda: self.add_to_expression('8')), 
            ('9', theme_colors['num'], lambda: self.add_to_expression('9')), 
            ('×', theme_colors['op'], lambda: self.append_operator("*")),
            ('4', theme_colors['num'], lambda: self.add_to_expression('4')), 
            ('5', theme_colors['num'], lambda: self.add_to_expression('5')), 
            ('6', theme_colors['num'], lambda: self.add_to_expression('6')), 
            ('−', theme_colors['op'], lambda: self.append_operator("-")),
            ('1', theme_colors['num'], lambda: self.add_to_expression('1')), 
            ('2', theme_colors['num'], lambda: self.add_to_expression('2')), 
            ('3', theme_colors['num'], lambda: self.add_to_expression('3')), 
            ('+', theme_colors['op'], lambda: self.append_operator("+"))
        ]
        
        for txt, clr, func in main_btns:
            btn = self._create_button(txt, clr, func, font_size='18sp')
            main_grid.add_widget(btn)
            self.btns_dict[txt] = btn
        
        container.add_widget(main_grid)
        
        bottom_row = BoxLayout(orientation='horizontal', spacing=2, size_hint=(1, 0.1))
        
        buttons = [
            ('±', theme_colors['op'], self.toggle_sign),
            ('0', theme_colors['num'], lambda: self.add_to_expression('0')),
            ('.', theme_colors['num'], lambda: self.add_to_expression(".")),
            ('=', theme_colors['special'], self.evaluate)
        ]
        
        for txt, clr, func in buttons:
            btn = self._create_button(txt, clr, func, font_size='18sp')
            btn.size_hint_x = 0.25
            bottom_row.add_widget(btn)
            self.btns_dict[txt] = btn
        
        self.btns_dict['/'] = self.btns_dict['÷']
        self.btns_dict['*'] = self.btns_dict['×']
        self.btns_dict['-'] = self.btns_dict['−']
        
        container.add_widget(bottom_row)

    def _create_button(self, text: str, color: tuple, callback: Callable, 
                       font_size: str = '24sp') -> CalculatorButton:
        theme_colors = THEMES[self.current_theme]
        btn = CalculatorButton(
            text=text, 
            font_size=font_size, 
            background_color=color, 
            color=theme_colors['text']
        )
        btn.bind(on_press=lambda x: callback())
        return btn
    
    def add_to_expression(self, value: str):
        if self.error_state:
            self.clear()
        
        if value == "0" and self.current_expression == "0":
            return
        
        if value == ".":
            if not self.current_expression:
                self.current_expression = "0."
                self._update_label()
                return
            if "." in self.current_expression:
                return
        
        if (self.last_result is not None and not self.total_expression and 
            self.pending_function is None):
            self.current_expression = ""
            self.last_result = None
        
        if self.current_expression == "0" and value != ".":
            self.current_expression = value
        else:
            if len(self.current_expression) < self.MAX_DIGITS:
                self.current_expression += value
        
        self._update_label()

    def append_operator(self, operator: str):
        if self.error_state:
            self.clear()
            return
        
        if self.current_expression:
            self.total_expression += self.current_expression + operator
            self.current_expression = ""
            self.last_result = None
            self._update_total_label()
            self._update_label()
        elif self.total_expression and self.total_expression[-1] in ['+', '-', '*', '/', '**']:
            self.total_expression = self.total_expression[:-1] + operator
            if operator == '**':
                self.total_expression = self.total_expression[:-1] + operator
            self._update_total_label()
        elif self.last_result is not None:
            self.total_expression = str(self.last_result) + operator
            self.current_expression = ""
            self.last_result = None
            self._update_total_label()

    def evaluate(self):
        if self.error_state:
            self.clear()
            return
        
        if self.pending_function is not None:
            self._execute_pending_function()
            return
        
        try:
            full_expr = self.total_expression + self.current_expression
            if not full_expr or (full_expr and full_expr[-1] in ['+', '-', '*', '/', '**']):
                return
            
            display_expr = self._format_expression_for_display(full_expr)
            
            result = eval(full_expr)
            
            if not isinstance(result, (int, float)):
                raise ValueError("Invalid result type")
            
            if abs(result) > 1e15:
                raise OverflowError("Number too large")
            
            result_str = self._format_number(result)
            
            self.calculation_history.append(f"{display_expr} = {result_str}")
            if len(self.calculation_history) > self.MAX_HISTORY:
                self.calculation_history.pop(0)
            
            self.current_expression = result_str
            self.last_result = float(result_str)
            self.total_expression = ""
            
        except ZeroDivisionError:
            self._show_error("Cannot divide by zero")
        except OverflowError:
            self._show_error("Number too large")
        except Exception as e:
            self._show_error("Error")
        
        self._update_total_label()
        self._update_label()
    
    def _execute_pending_function(self):
        if not self.current_expression or self.current_expression == "0":
            return
        
        try:
            value = float(self.current_expression)
            func_name = self.pending_function
            
            if func_name == 'custom_root':
                if not self.custom_root_mode:
                    return
                
                if self.root_power_value is None:
                    self.root_power_value = value
                    self.current_expression = ""
                    self.total_label.text = f"[sup]n[/sup]√( root power: {int(value)} ) value: "
                    return
                else:
                    root_power = self.root_power_value
                    if root_power == 0:
                        raise ValueError("Root power cannot be zero")
                    if value < 0 and root_power % 2 == 0:
                        raise ValueError("Cannot calculate even root of negative number")
                    result = value ** (1 / root_power)
                    display_text = f"{int(root_power)}√({value})"
                    self.root_power_value = None
                    self.custom_root_mode = False
            else:
                result = self._apply_scientific_function(func_name, value)
                display_text = self._get_function_display_text(func_name, value)
            
            if abs(result) > 1e15:
                raise OverflowError("Number too large")
            
            result_str = self._format_number(result)
            
            self.calculation_history.append(f"{display_text} = {result_str}")
            if len(self.calculation_history) > self.MAX_HISTORY:
                self.calculation_history.pop(0)
            
            self.current_expression = result_str
            self.pending_function = None
            self.total_label.text = ""
            self._update_label()
            
        except ValueError as e:
            self._show_error(str(e))
            self._reset_pending_function()
        except Exception:
            self._show_error("Math Error")
            self._reset_pending_function()
    
    def _reset_pending_function(self):
        self.pending_function = None
        self.custom_root_mode = False
        self.root_power_value = None
        self.total_label.text = ""
    
    def scientific_function(self, func_name: str):
        if self.error_state:
            self.clear()
            return
        
        if self.current_expression and self.current_expression != "0":
            try:
                value = float(self.current_expression)
                result = self._apply_scientific_function(func_name, value)
                
                if abs(result) > 1e15:
                    raise OverflowError("Number too large")
                
                self.current_expression = self._format_number(result)
                self._update_label()
                
            except ValueError as e:
                self._show_error(str(e))
            except Exception:
                self._show_error("Math Error")
        else:
            self.pending_function = func_name
            self.current_expression = ""
            self.total_label.text = self._get_function_prompt(func_name)
    
    def _apply_scientific_function(self, func_name: str, value: float) -> float:
        angle_rad = math.radians(value) if self.angle_mode == AngleMode.DEGREES else value
        
        function_map = {
            'sin': lambda v: math.sin(angle_rad),
            'cos': lambda v: math.cos(angle_rad),
            'tan': lambda v: math.tan(angle_rad),
            'asin': lambda v: self._asin_safe(v),
            'acos': lambda v: self._acos_safe(v),
            'atan': lambda v: self._atan_safe(v),
            'csc': lambda v: self._csc_safe(angle_rad),
            'sec': lambda v: self._sec_safe(angle_rad),
            'cot': lambda v: self._cot_safe(angle_rad),
            'sqrt': lambda v: self._sqrt_safe(v),
            'ln': lambda v: self._ln_safe(v),
            'log': lambda v: self._log_safe(v),
            'square': lambda v: v ** 2
        }
        
        if func_name not in function_map:
            raise ValueError(f"Unknown function: {func_name}")
        
        return function_map[func_name](value)
    
    def _asin_safe(self, value: float) -> float:
        if value < -1 or value > 1:
            raise ValueError("Domain error: arcsin requires -1 ≤ x ≤ 1")
        result = math.asin(value)
        return math.degrees(result) if self.angle_mode == AngleMode.DEGREES else result
    
    def _acos_safe(self, value: float) -> float:
        if value < -1 or value > 1:
            raise ValueError("Domain error: arccos requires -1 ≤ x ≤ 1")
        result = math.acos(value)
        return math.degrees(result) if self.angle_mode == AngleMode.DEGREES else result
    
    def _atan_safe(self, value: float) -> float:
        result = math.atan(value)
        return math.degrees(result) if self.angle_mode == AngleMode.DEGREES else result
    
    def _csc_safe(self, angle_rad: float) -> float:
        sin_val = math.sin(angle_rad)
        if abs(sin_val) < 1e-10:
            raise ValueError("Math error: csc undefined")
        return 1 / sin_val
    
    def _sec_safe(self, angle_rad: float) -> float:
        cos_val = math.cos(angle_rad)
        if abs(cos_val) < 1e-10:
            raise ValueError("Math error: sec undefined")
        return 1 / cos_val
    
    def _cot_safe(self, angle_rad: float) -> float:
        tan_val = math.tan(angle_rad)
        if abs(tan_val) < 1e-10:
            raise ValueError("Math error: cot undefined")
        return 1 / tan_val
    
    def _sqrt_safe(self, value: float) -> float:
        if value < 0:
            raise ValueError("Cannot calculate square root of negative number")
        return math.sqrt(value)
    
    def _ln_safe(self, value: float) -> float:
        if value <= 0:
            raise ValueError("Cannot calculate ln of non-positive number")
        return math.log(value)
    
    def _log_safe(self, value: float) -> float:
        if value <= 0:
            raise ValueError("Cannot calculate log of non-positive number")
        return math.log10(value)
    
    def _get_function_prompt(self, func_name: str) -> str:
        prompts = {
            'sqrt': '√(',
            'sin': 'sin(',
            'cos': 'cos(',
            'tan': 'tan(',
            'asin': 'sin[sup]-1[/sup](',
            'acos': 'cos[sup]-1[/sup](',
            'atan': 'tan[sup]-1[/sup](',
            'csc': 'csc(',
            'sec': 'sec(',
            'cot': 'cot(',
            'ln': 'ln(',
            'log': 'log('
        }
        return prompts.get(func_name, f"{func_name}(")
    
    def _get_function_display_text(self, func_name: str, value: float) -> str:
        displays = {
            'sqrt': f'√({value})',
            'sin': f'sin({value})',
            'cos': f'cos({value})',
            'tan': f'tan({value})',
            'asin': f'sin[sup]-1[/sup]({value})',
            'acos': f'cos[sup]-1[/sup]({value})',
            'atan': f'tan[sup]-1[/sup]({value})',
            'csc': f'csc({value})',
            'sec': f'sec({value})',
            'cot': f'cot({value})',
            'ln': f'ln({value})',
            'log': f'log({value})'
        }
        return displays.get(func_name, f"{func_name}({value})")
    
    def custom_root(self):
        if self.error_state:
            self.clear()
            return
        
        if not self.custom_root_mode:
            self.custom_root_mode = True
            self.pending_function = 'custom_root'
            self.current_expression = ""
            self.total_label.text = "[sup]n[/sup]√( root power: "
        else:
            self.custom_root_mode = False
            self.pending_function = None
            self.root_power_value = None
            self.total_label.text = ""
    
    def add_constant(self, constant_name: str):
        if self.error_state:
            self.clear()
        
        constants = {
            'pi': str(math.pi),
            'e': str(math.e)
        }
        
        if constant_name in constants:
            self.current_expression = constants[constant_name]
            self._update_label()
    
    def memory_clear(self):
        self.memory_value = 0.0
        self.has_memory = False
        self._update_memory_display()
    
    def memory_recall(self):
        if self.has_memory:
            self.current_expression = str(self.memory_value)
            self._update_label()
    
    def memory_add(self):
        try:
            if self._is_valid_expression():
                value = float(self.current_expression)
                self.memory_value += value
                self.has_memory = True
                self._update_memory_display()
                self._show_memory_feedback("M+")
        except Exception:
            pass
    
    def memory_subtract(self):
        try:
            if self._is_valid_expression():
                value = float(self.current_expression)
                self.memory_value -= value
                self.has_memory = True
                self._update_memory_display()
                self._show_memory_feedback("M-")
        except Exception:
            pass
    
    def _is_valid_expression(self) -> bool:
        error_messages = ["Error", "Cannot divide by zero", "Number too large", "Math Error"]
        return self.current_expression and self.current_expression not in error_messages
    
    def _update_memory_display(self):
        if self.has_memory:
            self.memory_label.text = f"  Memory: {self.memory_value}"
        else:
            self.memory_label.text = ""
    
    def _show_memory_feedback(self, operation: str):
        original_text = self.memory_label.text
        self.memory_label.text = f"  {operation}: {self.memory_value}"
        Clock.schedule_once(lambda dt: setattr(self.memory_label, 'text', original_text), 1.0)
    
    def clear(self):
        self.current_expression = ""
        self.total_expression = ""
        self.last_result = None
        self.error_state = False
        self._reset_pending_function()
        self._update_label()
        self._update_total_label()

    def backspace(self):
        if self.error_state:
            self.clear()
            return
        
        if self.pending_function is not None and not self.current_expression:
            self._reset_pending_function()
            return
        
        if self._is_valid_expression():
            self.current_expression = self.current_expression[:-1]
            self._update_label()

    def toggle_sign(self):
        if self.error_state:
            self.clear()
            return
        
        if self.current_expression and self.current_expression not in ["0"] and self._is_valid_expression():
            if self.current_expression.startswith("-"):
                self.current_expression = self.current_expression[1:]
            else:
                self.current_expression = "-" + self.current_expression
            self._update_label()

    def percentage(self):
        if self.error_state:
            self.clear()
            return
        
        try:
            if self._is_valid_expression():
                val = float(self.current_expression)
                result = val / 100
                self.current_expression = self._format_number(result)
                self._update_label()
        except Exception:
            self._show_error("Error")
    
    def _show_error(self, message: str):
        self.current_expression = message
        self.error_state = True
        original_color = self.label.color
        self.label.color = COLORS['error']
        Clock.schedule_once(lambda dt: setattr(self.label, 'color', original_color), 1.5)
    
    def _update_total_label(self):
        text = self._format_expression_for_display(self.total_expression)
        self.total_label.text = text

    def _update_label(self):
        self.label.text = self.current_expression or "0"
    
    def _format_expression_for_display(self, expr: str) -> str:
        text = expr
        for op, sym in self.OPERATIONS.items():
            text = text.replace(op, sym)
        return text
    
    def _format_number(self, number: float) -> str:
        if number == int(number):
            return str(int(number))
        else:
            result_str = str(round(number, 10))
            if '.' in result_str:
                result_str = result_str.rstrip('0').rstrip('.')
            
            if len(result_str) > self.MAX_DIGITS:
                return f"{number:.6e}"
            
            return result_str
    
    def cycle_theme(self):
        themes = [Theme.DARK, Theme.LIGHT, Theme.BLUE]
        current_index = themes.index(self.current_theme)
        next_index = (current_index + 1) % len(themes)
        self.current_theme = themes[next_index]
        self.apply_theme()
    
    def apply_theme(self):
        theme_colors = THEMES[self.current_theme]
        
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*theme_colors['bg'])
            self.bg_rect = Rectangle(pos=self.pos, size=self.size)
        
        for lbl in [self.memory_label, self.total_label, self.label]:
            lbl.canvas.before.clear()
            with lbl.canvas.before:
                Color(*theme_colors['display'])
                lbl.bg_rect = RoundedRectangle(pos=lbl.pos, size=lbl.size, radius=[10])
            lbl.color = theme_colors['text']
        
        for btn in [self.history_btn, self.theme_btn, self.mode_btn]:
            btn.update_theme(theme_colors['op'])
            btn.color = theme_colors['text']
        
        operator_keys = [
            'C', 'DEL', '%', '÷', '×', '−', '+', '±', 
            'MC', 'MR', 'M+', 'M-', 
            'sin', 'cos', 'tan', '√', 'x[sup]2[/sup]', 'x[sup]y[/sup]', 'ln', 'log', 
            'sin[sup]-1[/sup]', 'cos[sup]-1[/sup]', 'tan[sup]-1[/sup]',
            '[sup]n[/sup]√', 'csc', 'sec', 'cot', 'π'
        ]
        
        for key, btn in self.btns_dict.items():
            if key in operator_keys:
                btn.update_theme(theme_colors['op'])
            elif key == '=':
                btn.update_theme(theme_colors['special'])
            else:
                btn.update_theme(theme_colors['num'])
            btn.color = theme_colors['text']
    
    def toggle_scientific_mode(self):
        self.scientific_mode = not self.scientific_mode
        self.remove_widget(self.btns_container)
        
        btns_container = BoxLayout(
            orientation='vertical', 
            size_hint=(1, 0.645), 
            spacing=2, 
            padding=[10, 5, 10, 10]
        )
        
        if self.scientific_mode:
            self._create_scientific_buttons(btns_container)
            self.mode_btn.text = "Standard"
        else:
            self._create_standard_buttons(btns_container)
            self.mode_btn.text = "Scientific"
        
        self.add_widget(btns_container)
        self.btns_container = btns_container
    
    def show_history(self):
        content = BoxLayout(orientation='vertical', padding=10, spacing=10)
        theme_colors = THEMES[self.current_theme]
        
        scroll = ScrollView(size_hint=(1, 0.85))
        history_layout = GridLayout(cols=1, spacing=5, size_hint_y=None)
        history_layout.bind(minimum_height=history_layout.setter('height'))
        
        if not self.calculation_history:
            no_history = Label(
                text="No calculation history yet",
                size_hint_y=None,
                height=40,
                color=theme_colors['text']
            )
            history_layout.add_widget(no_history)
        else:
            for calc in reversed(self.calculation_history):
                calc_label = Label(
                    text=calc,
                    size_hint_y=None,
                    height=30,
                    color=theme_colors['text'],
                    halign='left',
                    valign='middle',
                    markup=True
                )
                calc_label.bind(size=calc_label.setter('text_size'))
                history_layout.add_widget(calc_label)
        
        scroll.add_widget(history_layout)
        content.add_widget(scroll)
        
        btn_layout = BoxLayout(size_hint=(1, 0.15), spacing=5)
        
        clear_btn = Button(
            text="Clear History",
            background_color=theme_colors['special'],
            color=theme_colors['text']
        )
        close_btn = Button(
            text="Close",
            background_color=theme_colors['op'],
            color=theme_colors['text']
        )
        
        popup = Popup(
            title="Calculation History",
            content=content,
            size_hint=(0.9, 0.8),
            background_color=theme_colors['bg']
        )
        
        clear_btn.bind(on_press=lambda x: self._clear_history(popup))
        close_btn.bind(on_press=popup.dismiss)
        
        btn_layout.add_widget(clear_btn)
        btn_layout.add_widget(close_btn)
        content.add_widget(btn_layout)
        
        popup.open()
    
    def _clear_history(self, popup: Popup):
        self.calculation_history = []
        popup.dismiss()
    
    def _on_keyboard_down(self, window, key: int, scancode: int, 
                          codepoint: str, modifiers: List[str]) -> bool:
        if (48 <= key <= 57) or (256 <= key <= 265):
            if key == 56 and 'shift' in modifiers:
                self.append_operator("*")
                if '*' in self.btns_dict:
                    self.btns_dict['*'].flash()
                return True
            
            num = chr(key) if 48 <= key <= 57 else str(key - 256)
            self.add_to_expression(num)
            if num in self.btns_dict:
                self.btns_dict[num].flash()
            return True
        
        key_map = {
            46: '.', 266: '.',
            43: '+', 270: '+',
            45: '−', 269: '−',
            42: '*', 268: '*',
            47: '/', 267: '/',
            13: '=', 271: '=',
            8: 'DEL', 127: 'DEL',
            27: 'C',
            37: '%',
            61: '+'
        }
        
        if key == 61 and 'shift' in modifiers:
            self.append_operator("+")
            if '+' in self.btns_dict:
                self.btns_dict['+'].flash()
            return True
        
        if key in key_map:
            action = key_map[key]
            
            if action == '.':
                self.add_to_expression('.')
            elif action in ['+', '−', '*', '/']:
                self.append_operator(action if action != '−' else '-')
            elif action == '=':
                self.evaluate()
            elif action == 'DEL':
                self.backspace()
            elif action == 'C':
                self.clear()
            elif action == '%':
                self.percentage()
            
            display_key = action if action != '−' else '-'
            if display_key in self.btns_dict:
                self.btns_dict[display_key].flash()
            return True
        
        if codepoint:
            if codepoint.lower() == 'c':
                self.clear()
                if 'C' in self.btns_dict:
                    self.btns_dict['C'].flash()
                return True
            elif codepoint.lower() == 'h':
                self.show_history()
                return True
        
        return False

class CalculatorApp(App):
    def build(self):
        Window.size = (420, 680)
        Window.minimum_width = 380
        Window.minimum_height = 600
        self.title = "Advanced Scientific Calculator"
        self.icon = ''
        return Calculator()

if __name__ == "__main__":
    CalculatorApp().run()