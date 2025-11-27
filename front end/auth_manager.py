"""
Modern Authentication Manager
Beautiful, user-friendly login and registration
"""
import tkinter as tk
from tkinter import messagebox
import re
from ui_components import ModernButton, ModernEntry, Card, ScrollableFrame, IconLabel, COLORS


class AuthManager:
    def __init__(self, app):
        self.app = app
        self.register_window = None
        self.loading = False
    
    def show_login_screen(self):
        """Display beautiful login interface"""
        # Reset loading state (important for re-login after logout)
        self.loading = False
        
        # Gradient-style background (two-tone)
        bg_frame = tk.Frame(self.app.root, bg=COLORS['background'])
        bg_frame.pack(fill=tk.BOTH, expand=True)
        
        # Center container
        center = tk.Frame(bg_frame, bg=COLORS['background'])
        center.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        
        # Logo/Title area with modern design
        header = tk.Frame(center, bg=COLORS['background'])
        header.pack(pady=(0, 45))
        
        # Modern minimalist logo
        logo_canvas = tk.Canvas(
            header,
            width=100,
            height=100,
            bg=COLORS['background'],
            highlightthickness=0
        )
        logo_canvas.pack()
        
        # Draw sophisticated logo - overlapping rounded squares
        logo_canvas.create_rectangle(15, 15, 65, 65, fill=COLORS['primary'], outline='', width=0)
        logo_canvas.create_rectangle(35, 35, 85, 85, fill=COLORS['accent'], outline='', width=0)
        logo_canvas.create_rectangle(42, 42, 58, 58, fill='#FFFFFF', outline='', width=0)
        
        # Title with gradient-like effect
        tk.Label(
            header,
            text="Room Booking",
            font=('SF Pro Display', 32, 'bold'),
            bg=COLORS['background'],
            fg=COLORS['text']
        ).pack(pady=(18, 0))

        tk.Label(
            header,
            text="SYSTEM",
            font=('SF Pro Display', 14, 'bold'),
            bg=COLORS['background'],
            fg=COLORS['primary']
        ).pack(pady=(0, 8))

        # Subtitle with better styling
        subtitle_frame = tk.Frame(header, bg=COLORS['background'])
        subtitle_frame.pack()

        tk.Label(
            subtitle_frame,
            text="University of St Andrews",
            font=('SF Pro Text', 12),
            bg=COLORS['background'],
            fg=COLORS['text_secondary']
        ).pack()
        
        # Login card
        login_card = Card(center, padding=35)
        login_card.pack()
        login_card.config(width=400)
        
        # Welcome message
        tk.Label(
            login_card.container,
            text="Welcome back",
            font=('SF Pro Display', 20, 'bold'),
            bg=COLORS['surface'],
            fg=COLORS['text']
        ).pack(anchor='w', pady=(0, 8))
        
        tk.Label(
            login_card.container,
            text="Sign in to manage your bookings",
            font=('SF Pro Text', 11),
            bg=COLORS['surface'],
            fg=COLORS['text_secondary']
        ).pack(anchor='w', pady=(0, 25))
        
        # Email field
        self.email_entry = ModernEntry(
            login_card.container,
            label="Email Address",
            placeholder="your.email@st-andrews.ac.uk",
            width=35
        )
        self.email_entry.pack(fill=tk.X, pady=(0, 15))
        
        # Password field
        self.password_entry = ModernEntry(
            login_card.container,
            label="Password",
            placeholder="Enter your password",
            show="•",
            width=35
        )
        self.password_entry.pack(fill=tk.X, pady=(0, 20))
        
        # Container to reserve space under password for error messages
        self.error_container = tk.Frame(login_card.container, bg=COLORS['surface'])
        self.error_container.pack(fill=tk.X)
        
        # Error message label (hidden by default)
        self.error_label = IconLabel(
            self.error_container,
            text="",
            font=('SF Pro Text', 10),
            bg=COLORS['surface'],
            fg=COLORS['danger'],
            wraplength=320,
            anchor='w'
        )
        # Do not pack yet; only show when an error occurs
        
        # Login button
        ModernButton(
            login_card.container,
            text="Sign In",
            command=self.login,
            style='primary',
            width=35
        ).pack(fill=tk.X, pady=(0, 15))
        
        # Divider
        divider_frame = tk.Frame(login_card.container, bg=COLORS['surface'])
        divider_frame.pack(fill=tk.X, pady=15)
        
        tk.Frame(divider_frame, bg=COLORS['border'], height=1).pack(side=tk.LEFT, fill=tk.X, expand=True)
        tk.Label(
            divider_frame,
            text="  or  ",
            bg=COLORS['surface'],
            fg=COLORS['text_secondary'],
            font=('SF Pro Text', 9)
        ).pack(side=tk.LEFT)
        tk.Frame(divider_frame, bg=COLORS['border'], height=1).pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Register button
        ModernButton(
            login_card.container,
            text="Create New Account",
            command=self.show_register_window,
            style='secondary',
            width=35
        ).pack(fill=tk.X)
        
        # Bind Enter key for login (multiple bindings for better UX)
        self.app.root.bind("<Return>", lambda e: self.login())
        self.email_entry.entry.bind("<Return>", lambda e: self.login())
        self.password_entry.entry.bind("<Return>", lambda e: self.login())
        
        # Focus first field
        self.email_entry.focus()
    
    def show_error(self, message):
        """Display error message"""
        if not self.error_label.winfo_ismapped():
            self.error_label.pack(fill=tk.X, pady=(0, 15))
        self.error_label.config(text=f"× {message}", fg=COLORS['danger'])
    
    def clear_error(self):
        """Clear error message"""
        self.error_label.config(text="")
        if self.error_label.winfo_ismapped():
            self.error_label.pack_forget()
    
    def validate_email(self, email):
        """Basic email validation"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def login(self):
        """Handle login with validation and feedback"""
        if self.loading:
            return
        
        self.clear_error()
        email = self.email_entry.get().strip()
        password = self.password_entry.get()
        
        # Validation
        if not email:
            self.show_error("Please enter your email address")
            self.email_entry.focus()
            return
        
        if not self.validate_email(email):
            self.show_error("Please enter a valid email address")
            self.email_entry.focus()
            return
        
        if not password:
            self.show_error("Please enter your password")
            self.password_entry.focus()
            return
        
        # Start loading state
        self.loading = True
        
        try:
            response = self.app.api_client.login(email, password)
            if response and "token" in response:
                # Success!
                self.app.handle_login_success(response.get("user", {}), response["token"])
            else:
                self.show_error("Login failed. Please try again.")
                self.loading = False
        except Exception as exc:
            error_msg = str(exc)
            if "401" in error_msg or "Invalid" in error_msg:
                self.show_error("Invalid email or password")
            elif "423" in error_msg or "locked" in error_msg.lower():
                self.show_error("Account locked. Please try again later.")
            elif "connect" in error_msg.lower():
                self.show_error("Cannot connect to server. Is the backend running?")
            else:
                self.show_error(f"Login error: {error_msg}")
            self.loading = False
    
    def show_register_window(self):
        """Modern registration window"""
        try:
            if self.register_window and self.register_window.winfo_exists():
                self.register_window.lift()
                return
        except:
            self.register_window = None
        
        # Create top-level window
        self.register_window = tk.Toplevel(self.app.root)
        self.register_window.title("Create Account")
        self.register_window.geometry("450x600")
        self.register_window.configure(bg=COLORS['background'])
        self.register_window.resizable(False, False)
        
        # Make modal
        self.register_window.transient(self.app.root)
        self.register_window.grab_set()
        
        # Main container
        main = tk.Frame(self.register_window, bg=COLORS['background'])
        main.pack(fill=tk.BOTH, expand=True, padx=30, pady=30)
        
        # Header
        tk.Label(
            main,
            text="Create Your Account",
            font=('SF Pro Display', 22, 'bold'),
            bg=COLORS['background'],
            fg=COLORS['text']
        ).pack(anchor='w', pady=(0, 8))
        
        tk.Label(
            main,
            text="Join the room booking system",
            font=('SF Pro Text', 11),
            bg=COLORS['background'],
            fg=COLORS['text_secondary']
        ).pack(anchor='w', pady=(0, 30))
        
        # Form fields
        self.reg_name = ModernEntry(main, label="Full Name", placeholder="John Doe", width=40)
        self.reg_name.pack(fill=tk.X, pady=(0, 15))
        
        self.reg_email = ModernEntry(main, label="Email Address", placeholder="your.email@st-andrews.ac.uk", width=40)
        self.reg_email.pack(fill=tk.X, pady=(0, 15))
        
        self.reg_password = ModernEntry(main, label="Password", placeholder="Minimum 8 characters", show="•", width=40)
        self.reg_password.pack(fill=tk.X, pady=(0, 15))
        
        # Role selection
        role_frame = tk.Frame(main, bg=COLORS['background'])
        role_frame.pack(fill=tk.X, pady=(0, 15))
        
        tk.Label(
            role_frame,
            text="I am a:",
            font=('SF Pro Display', 10, 'bold'),
            bg=COLORS['background'],
            fg=COLORS['text']
        ).pack(anchor='w', pady=(0, 8))
        
        self.role_var = tk.StringVar(value="student")
        
        role_options = tk.Frame(role_frame, bg=COLORS['background'])
        role_options.pack(fill=tk.X)
        
        for role, label in [('student', 'Student'), ('staff', 'Staff Member')]:
            rb = tk.Radiobutton(
                role_options,
                text=label,
                variable=self.role_var,
                value=role,
                font=('SF Pro Text', 11),
                bg=COLORS['background'],
                fg=COLORS['text'],
                selectcolor=COLORS['primary'],
                activebackground=COLORS['background'],
                cursor='hand2'
            )
            rb.pack(anchor='w', pady=4)
        
        # Error message
        self.reg_error_label = IconLabel(
            main,
            text="",
            font=('SF Pro Text', 10),
            bg=COLORS['background'],
            fg=COLORS['danger'],
            wraplength=350,
            anchor='w'
        )
        # Hidden until an error needs to be shown
        
        # Buttons
        btn_frame = tk.Frame(main, bg=COLORS['background'])
        btn_frame.pack(fill=tk.X, pady=(10, 0))
        
        ModernButton(
            btn_frame,
            text="Create Account",
            command=self.register_user,
            style='primary',
            width=20
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        ModernButton(
            btn_frame,
            text="Cancel",
            command=self._close_register_window,
            style='secondary',
            width=15
        ).pack(side=tk.LEFT)
    
    def register_user(self):
        """Register with comprehensive validation"""
        # Clear previous errors
        self._clear_reg_error()
        
        # Get values
        name = self.reg_name.get().strip()
        email = self.reg_email.get().strip()
        password = self.reg_password.get()
        role = self.role_var.get()
        
        # Validation
        if not name:
            self._show_reg_error("Please enter your full name")
            self.reg_name.focus()
            return
        
        if len(name) < 2:
            self._show_reg_error("Name must be at least 2 characters")
            self.reg_name.focus()
            return
        
        if not email:
            self._show_reg_error("Please enter your email address")
            self.reg_email.focus()
            return
        
        if not self.validate_email(email):
            self._show_reg_error("Please enter a valid email address")
            self.reg_email.focus()
            return
        
        if not password:
            self._show_reg_error("Please enter a password")
            self.reg_password.focus()
            return
        
        if len(password) < 8:
            self._show_reg_error("Password must be at least 8 characters")
            self.reg_password.focus()
            return
        
        # Attempt registration
        try:
            response = self.app.api_client.register(name, email, password, role)
            
            # Success!
            messagebox.showinfo(
                "Account Created",
                f"Welcome, {name}!\n\nYour account has been created successfully.\nYou can now sign in."
            )
            
            # Pre-fill login form
            self.email_entry.set(email)
            self.password_entry.set(password)
            
            self._close_register_window()
            
        except Exception as exc:
            error_msg = str(exc)
            if "409" in error_msg or "already registered" in error_msg.lower():
                self._show_reg_error("This email is already registered")
            elif "connect" in error_msg.lower():
                self._show_reg_error("Cannot connect to server")
            else:
                self._show_reg_error(error_msg)
    
    def _close_register_window(self):
        if self.register_window:
            try:
                self.register_window.destroy()
            except:
                pass
            self.register_window = None

    def _show_reg_error(self, message: str):
        """Show registration error message."""
        if not self.reg_error_label.winfo_ismapped():
            self.reg_error_label.pack(pady=(10, 15), fill=tk.X)
        self.reg_error_label.config(text=f"× {message}", fg=COLORS['danger'])

    def _clear_reg_error(self):
        """Hide registration error message."""
        self.reg_error_label.config(text="")
        if self.reg_error_label.winfo_ismapped():
            self.reg_error_label.pack_forget()
