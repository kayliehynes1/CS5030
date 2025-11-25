import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from auth_manager import AuthManager
from dashboard import Dashboard
from api_client import APIClient

class RoomBookingClient:
    def __init__(self, root):
        self.root = root
        self.root.title("University Room Booking System")
        self.root.geometry("1000x700")

        style=ttk.Style(theme='superhero')
        
        
        self.api_client = APIClient(base_url="http://localhost:8000")
        self.auth_manager = AuthManager(self)
        self.dashboard = Dashboard(self)
        
        self.current_user = None
        self.token = None
        
        self.show_login()
    
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
        """Clear all widgets from root"""
        for widget in self.root.winfo_children():
            widget.destroy()

def main():
    root = tk.Tk()
    app = RoomBookingClient(root)
    root.mainloop()

if __name__ == "__main__":
    main()