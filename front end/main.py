"""
Modern Room Booking Client
Beautiful, professional Tkinter application with keyboard shortcuts
"""
import tkinter as tk
from tkinter import ttk
from auth_manager import AuthManager
from dashboard import Dashboard
from api_client import APIClient
from ui_components import COLORS


class RoomBookingClient:
    def __init__(self, root):
        self.root = root
        self.root.title("University Room Booking System")
        self.root.geometry("1200x800")
        self.root.configure(bg=COLORS['background'])
        
        # Apply a dark palette to ttk widgets so backgrounds match the app shell
        style = ttk.Style(self.root)
        style.theme_use("clam")
        style.configure(".", background=COLORS['background'], foreground=COLORS['text'])
        style.configure("TFrame", background=COLORS['background'])
        style.configure("TLabel", background=COLORS['background'], foreground=COLORS['text'])
        style.configure("TButton", background=COLORS['surface'], foreground=COLORS['text'])
        style.map("TButton", background=[("active", COLORS['surface_hover'])])
        # Form controls: force dark backgrounds but black text for readability when highlighted/active
        style.configure(
            "TEntry",
            background=COLORS['surface'],
            fieldbackground=COLORS['surface'],
            foreground=COLORS['text'],
            insertcolor=COLORS['text']
        )
        style.configure(
            "TCombobox",
            background=COLORS['surface'],
            fieldbackground=COLORS['surface'],
            foreground=COLORS['text']
        )
        style.map(
            "TCombobox",
            foreground=[("readonly", COLORS['text']), ("active", COLORS['text']), ("focus", COLORS['text'])],
            fieldbackground=[("readonly", COLORS['surface']), ("active", COLORS['surface'])],
            selectbackground=[("readonly", COLORS['surface_hover']), ("!disabled", COLORS['surface_hover'])],
            selectforeground=[("readonly", COLORS['text']), ("!disabled", COLORS['text'])],
            background=[("readonly", COLORS['surface']), ("active", COLORS['surface'])]
        )
        style.configure("TNotebook", background=COLORS['background'])
        style.configure("TNotebook.Tab", background=COLORS['surface'], foreground=COLORS['text'])
        style.map(
            "TNotebook.Tab",
            background=[("selected", COLORS['surface_hover']), ("active", COLORS['surface_hover'])],
            foreground=[("selected", COLORS['text']), ("active", COLORS['text'])]
        )
        style.configure("TLabelframe", background=COLORS['background'], foreground=COLORS['text'])
        style.configure("TLabelframe.Label", background=COLORS['background'], foreground=COLORS['text'])
        style.configure(
            "Treeview",
            background=COLORS['surface'],
            fieldbackground=COLORS['surface'],
            foreground=COLORS['text']
        )
        style.configure("Treeview.Heading", background=COLORS['surface'], foreground=COLORS['text'])
        style.map("Treeview.Heading", foreground=[("active", "#000000"), ("pressed", "#000000")])
        style.map("Treeview", background=[("selected", COLORS['primary'])], foreground=[("selected", "#ffffff")])
        
        # Center window on screen
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
        
        # Initialize components
        self.api_client = APIClient()
        self.auth_manager = AuthManager(self)
        self.dashboard = Dashboard(self)
        
        # State
        self.current_user = None
        self.token = None
        
        # Setup keyboard shortcuts
        self._setup_keyboard_shortcuts()
        
        # Show login
        self.show_login()
    
    def _setup_keyboard_shortcuts(self):
        """Setup global keyboard shortcuts"""
        # Cmd/Ctrl + Enter for form submission
        self.root.bind_all('<Control-Return>', lambda e: self._handle_submit())
        self.root.bind_all('<Command-Return>', lambda e: self._handle_submit())
        
        # Escape to cancel/go back
        self.root.bind_all('<Escape>', lambda e: self._handle_escape())
        
        # Cmd/Ctrl + Q to quit
        self.root.bind_all('<Control-q>', lambda e: self.root.quit())
        self.root.bind_all('<Command-q>', lambda e: self.root.quit())
    
    def _handle_submit(self):
        """Handle form submission shortcut"""
        # Find focused widget and trigger submit if it's a button
        focused = self.root.focus_get()
        if isinstance(focused, tk.Button) and focused.cget('command'):
            focused.invoke()
    
    def _handle_escape(self):
        """Handle escape key"""
        # Close any open dialogs or go back
        focused = self.root.focus_get()
        if isinstance(focused, tk.Toplevel):
            focused.destroy()
    
    def show_login(self):
        """Show login screen"""
        self.clear_screen()
        self.auth_manager.show_login_screen()
    
    def show_dashboard(self):
        """Show main dashboard"""
        self.clear_screen()
        self.dashboard.show_dashboard()
    
    def handle_login_success(self, user_data, token):
        """Handle successful login"""
        self.current_user = user_data
        self.token = token
        self.api_client.set_token(token)
        self.show_dashboard()
    
    def logout(self):
        """Handle logout"""
        self.current_user = None
        self.token = None
        self.api_client.set_token(None)
        self.show_login()
    
    def clear_screen(self):
        """Clear all widgets"""
        for widget in self.root.winfo_children():
            widget.destroy()


def main():
    root = tk.Tk()
    
    # Set app icon behavior for macOS
    try:
        root.lift()
        root.attributes('-topmost', True)
        root.after_idle(root.attributes, '-topmost', False)
    except:
        pass
    
    app = RoomBookingClient(root)
    root.mainloop()


if __name__ == "__main__":
    main()
