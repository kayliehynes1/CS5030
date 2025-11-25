import tkinter as tk
from tkinter import ttk, messagebox

class AuthManager:
    def __init__(self, app):
        self.app = app
    
    def show_login_screen(self):
        """Display login interface"""
        # Main frame
        main_frame = ttk.Frame(self.app.root, padding="30")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.app.root.columnconfigure(0, weight=1)
        self.app.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # Title
        title_label = ttk.Label(main_frame, text="University Room Booking System", 
                               font=('Arial', 18, 'bold'))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 30))
        
        subtitle_label = ttk.Label(main_frame, text="Please login to continue",
                                  font=('Arial', 12))
        subtitle_label.grid(row=1, column=0, columnspan=2, pady=(0, 20))
        
        # Email field
        ttk.Label(main_frame, text="Email:", font=('Arial', 10)).grid(
            row=2, column=0, sticky=tk.W, pady=8)
        self.email_entry = ttk.Entry(main_frame, width=30, font=('Arial', 10))
        self.email_entry.grid(row=2, column=1, sticky=(tk.W, tk.E), pady=8, padx=(10, 0))
        
        # Password field
        ttk.Label(main_frame, text="Password:", font=('Arial', 10)).grid(
            row=3, column=0, sticky=tk.W, pady=8)
        self.password_entry = ttk.Entry(main_frame, width=30, show="*", font=('Arial', 10))
        self.password_entry.grid(row=3, column=1, sticky=(tk.W, tk.E), pady=8, padx=(10, 0))
        
        # Login button
        login_btn = ttk.Button(main_frame, text="Login", 
                              command=self.login)
        login_btn.grid(row=4, column=0, columnspan=2, pady=20)
        
        # Demo credentials hint
        demo_label = ttk.Label(main_frame, text="Demo: any email/password", 
                              font=('Arial', 9), foreground='gray')
        demo_label.grid(row=5, column=0, columnspan=2, pady=(10, 0))
        
        # Bind Enter key to login
        self.app.root.bind('<Return>', lambda event: self.login())
        
        # Set focus to email field
        self.email_entry.focus()
    
    def login(self):
        """Handle login process"""
        email = self.email_entry.get().strip()
        password = self.password_entry.get()
        
        # Validation
        if not email:
            messagebox.showerror("Error", "Please enter your email address")
            self.email_entry.focus()
            return
        
        if not password:
            messagebox.showerror("Error", "Please enter your password")
            self.password_entry.focus()
            return
        
        # Show loading state
        original_text = self.email_entry.get()
        self.email_entry.config(state='disabled')
        self.password_entry.config(state='disabled')
        
        # Attempt login
        try:
            response = self.app.api_client.login(email, password)
            
            if response and "token" in response:
                user_data = response.get("user", {"name": email, "email": email})
                self.app.handle_login_success(user_data, response["token"])
            else:
                messagebox.showerror("Login Failed", "Invalid email or password")
                
        except Exception as e:
            messagebox.showerror("Login Error", f"Unable to connect to server: {str(e)}")
        
        # Restore input fields
        finally:
            self.email_entry.config(state='normal')
            self.password_entry.config(state='normal')