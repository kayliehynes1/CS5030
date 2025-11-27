"""
Premium UI Components for Tkinter
Modern, polished, accessible components with keyboard shortcuts
"""
import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional

# Professional color system
COLORS = {
    'primary': '#2563EB',
    'primary_hover': '#1D4ED8',
    'primary_light': '#DBEAFE',
    'success': '#059669',
    'success_light': '#D1FAE5',
    'danger': '#DC2626',
    'danger_light': '#FEE2E2',
    'warning': '#D97706',
    'background': '#F8FAFC',
    'surface': '#FFFFFF',
    'surface_hover': '#F9FAFB',
    'text': '#0F172A',
    'text_secondary': '#64748B',
    'border': '#E2E8F0',
    'border_focus': '#2563EB',
    'shadow': '#00000010',
    'accent': '#8B5CF6',
}


class ModernButton(tk.Button):
    """Premium button with hover, focus, and keyboard support"""
    
    def __init__(self, parent, text="", command=None, style="primary", width=15, **kwargs):
        colors = {
            'primary': ('#2563EB', '#1D4ED8', '#000000'),  # Blue with black text
            'success': ('#059669', '#047857', '#000000'),  # Green with black text
            'danger': ('#DC2626', '#B91C1C', '#000000'),   # Red with black text
            'secondary': ('#E2E8F0', '#CBD5E1', '#000000') # Gray with black text
        }
        
        bg, hover_bg, fg = colors.get(style, colors['primary'])
        
        super().__init__(
            parent,
            text=text,
            command=command,
            bg=bg,
            fg=fg,
            font=('SF Pro Display', 11, 'bold'),
            relief='flat',
            cursor='hand2',
            width=width,
            pady=10,
            padx=20,
            bd=0,
            highlightthickness=0,
            activebackground=hover_bg,
            activeforeground=fg,
            **kwargs
        )
        
        self.default_bg = bg
        self.hover_bg = hover_bg
        self.style = style
        
        # Hover effects
        self.bind('<Enter>', self._on_enter)
        self.bind('<Leave>', self._on_leave)
        self.bind('<Button-1>', self._on_press)
        self.bind('<ButtonRelease-1>', self._on_release)
        
        # Keyboard support
        if command:
            parent.bind_all('<Return>', lambda e: command() if self.focus_get() == self else None)
    
    def _on_enter(self, e):
        self.config(bg=self.hover_bg)
    
    def _on_leave(self, e):
        self.config(bg=self.default_bg)
    
    def _on_press(self, e):
        self.config(relief='sunken')
    
    def _on_release(self, e):
        self.config(relief='flat')


class ModernEntry(tk.Frame):
    """Premium entry with label, validation, and keyboard shortcuts"""
    
    def __init__(self, parent, label="", placeholder="", show=None, width=30, 
                 on_change: Optional[Callable] = None, **kwargs):
        super().__init__(parent, bg=COLORS['background'])
        
        # Label
        if label:
            self.label = tk.Label(
                self,
                text=label,
                font=('SF Pro Display', 10, 'bold'),
                bg=COLORS['background'],
                fg=COLORS['text'],
                anchor='w'
            )
            self.label.pack(fill=tk.X, pady=(0, 6))
        
        # Entry container with border
        self.container = tk.Frame(self, bg=COLORS['border'], padx=2, pady=2)
        self.container.pack(fill=tk.X)
        
        # Entry widget
        self.entry = tk.Entry(
            self.container,
            font=('SF Pro Text', 11),
            bg=COLORS['surface'],
            fg=COLORS['text'],
            relief='flat',
            width=width,
            show=show,
            bd=0,
            highlightthickness=0,
            insertbackground=COLORS['primary'],
            **kwargs
        )
        self.entry.pack(fill=tk.X, padx=1, pady=1)
        
        # Placeholder
        self._placeholder = placeholder
        if placeholder:
            self.entry.insert(0, placeholder)
            self.entry.config(fg=COLORS['text_secondary'])
            self.entry.bind('<FocusIn>', self._clear_placeholder)
            self.entry.bind('<FocusOut>', self._restore_placeholder)
        
        # Focus effects
        self.entry.bind('<FocusIn>', self._on_focus_in)
        self.entry.bind('<FocusOut>', self._on_focus_out)
        
        # Keyboard shortcuts
        self.entry.bind('<Control-a>', self._select_all)
        self.entry.bind('<Command-a>', self._select_all)
        self.entry.bind('<Control-Delete>', self._clear_all)
        self.entry.bind('<Command-Delete>', self._clear_all)
        
        # Auto-save on change
        if on_change:
            self.entry.bind('<KeyRelease>', lambda e: on_change(self.get()))
    
    def _on_focus_in(self, e):
        self.container.config(bg=COLORS['border_focus'])
        if hasattr(self, '_placeholder') and self.entry.get() == self._placeholder:
            self._clear_placeholder(e)
    
    def _on_focus_out(self, e):
        self.container.config(bg=COLORS['border'])
        if hasattr(self, '_placeholder'):
            self._restore_placeholder(e)
    
    def _clear_placeholder(self, e=None):
        if hasattr(self, '_placeholder') and self.entry.get() == self._placeholder:
            self.entry.delete(0, tk.END)
            self.entry.config(fg=COLORS['text'])
    
    def _restore_placeholder(self, e=None):
        if hasattr(self, '_placeholder') and not self.entry.get():
            self.entry.insert(0, self._placeholder)
            self.entry.config(fg=COLORS['text_secondary'])
    
    def _select_all(self, e):
        self.entry.select_range(0, tk.END)
        return 'break'
    
    def _clear_all(self, e):
        self.entry.delete(0, tk.END)
        return 'break'
    
    def get(self):
        value = self.entry.get()
        if hasattr(self, '_placeholder') and value == self._placeholder:
            return ""
        return value
    
    def set(self, value):
        self.entry.delete(0, tk.END)
        self.entry.insert(0, value)
        self.entry.config(fg=COLORS['text'])
    
    def focus(self):
        self.entry.focus()
    
    def clear(self):
        self.entry.delete(0, tk.END)


class ScrollableFrame(tk.Frame):
    """Fully scrollable frame with native scrolling support"""
    
    def __init__(self, parent, bg=COLORS['background'], **kwargs):
        super().__init__(parent, bg=bg, **kwargs)
        
        # Create canvas and scrollbar
        self.canvas = tk.Canvas(
            self,
            bg=bg,
            highlightthickness=0,
            bd=0,
            **kwargs
        )
        
        self.scrollbar = ttk.Scrollbar(
            self,
            orient="vertical",
            command=self.canvas.yview
        )
        
        # Scrollable content frame
        self.scrollable_frame = tk.Frame(self.canvas, bg=bg)
        
        # Configure scrolling
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        # Pack
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Native scrolling support
        self._setup_scrolling()
        
        # Update canvas width when frame resizes
        self.scrollable_frame.bind('<Configure>', self._on_frame_configure)
        self.canvas.bind('<Configure>', self._on_canvas_configure)
    
    def _setup_scrolling(self):
        """Setup native scrolling for macOS and Windows"""
        # Mousewheel (Windows/Mac)
        def _on_mousewheel(event):
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        
        # Trackpad gestures (Mac)
        def _on_trackpad(event):
            if event.num == 4:
                self.canvas.yview_scroll(-1, "units")
            elif event.num == 5:
                self.canvas.yview_scroll(1, "units")
        
        self.canvas.bind_all("<MouseWheel>", _on_mousewheel)
        self.canvas.bind_all("<Button-4>", _on_trackpad)
        self.canvas.bind_all("<Button-5>", _on_trackpad)
        
        # Keyboard scrolling
        self.canvas.bind_all("<Up>", lambda e: self.canvas.yview_scroll(-1, "units") if self.canvas.focus_get() == self.canvas else None)
        self.canvas.bind_all("<Down>", lambda e: self.canvas.yview_scroll(1, "units") if self.canvas.focus_get() == self.canvas else None)
        self.canvas.bind_all("<PageUp>", lambda e: self.canvas.yview_scroll(-1, "pages") if self.canvas.focus_get() == self.canvas else None)
        self.canvas.bind_all("<PageDown>", lambda e: self.canvas.yview_scroll(1, "pages") if self.canvas.focus_get() == self.canvas else None)
    
    def _on_frame_configure(self, event):
        """Update scroll region when content changes"""
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
    
    def _on_canvas_configure(self, event):
        """Update canvas window width"""
        canvas_width = event.width
        self.canvas.itemconfig(self.canvas.find_all()[0], width=canvas_width)


class Card(tk.Frame):
    """Premium card component with subtle shadow and rounded corners"""
    
    def __init__(self, parent, title="", padding=24, bg=COLORS['surface'], **kwargs):
        super().__init__(
            parent,
            bg=bg,
            relief='flat',
            **kwargs
        )
        
        # Subtle border for elevation effect
        self.config(highlightbackground=COLORS['border'], highlightthickness=1)
        
        # Container with padding
        self.container = tk.Frame(self, bg=bg)
        self.container.pack(fill=tk.BOTH, expand=True, padx=padding, pady=padding)
        
        if title:
            tk.Label(
                self.container,
                text=title,
                font=('SF Pro Display', 18, 'bold'),
                bg=bg,
                fg=COLORS['text']
            ).pack(anchor='w', pady=(0, 16))


class IconLabel(tk.Label):
    """Label with icon (using Unicode symbols as icons)"""
    
    ICONS = {
        'user': '●',
        'room': '■',
        'calendar': '◆',
        'check': '✓',
        'cross': '×',
        'arrow_right': '→',
        'arrow_left': '←',
        'plus': '+',
        'minus': '−',
        'edit': '○',
        'delete': '×',
        'info': '○',
        'warning': '▲',
        'success': '✓',
        'error': '×',
        'notification': '●',
        'booking': '■',
        'time': '◆'
    }
    
    def __init__(self, parent, text="", icon=None, icon_color=None, **kwargs):
        display_text = text
        if icon and icon in self.ICONS:
            icon_char = self.ICONS[icon]
            display_text = f"{icon_char} {text}" if text else icon_char
        
        super().__init__(parent, text=display_text, **kwargs)
        
        if icon_color:
            self.config(fg=icon_color)

