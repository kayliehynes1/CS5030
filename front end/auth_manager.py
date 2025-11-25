import tkinter as tk
from tkinter import ttk, messagebox


class AuthManager:
    def __init__(self, app):
        self.app = app
        self.register_window = None

    def show_login_screen(self):
        """Display login interface that authenticates via the backend."""
        main_frame = ttk.Frame(self.app.root, padding="30")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        self.app.root.columnconfigure(0, weight=1)
        self.app.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)

        ttk.Label(
            main_frame,
            text="University Room Booking System",
            font=("Arial", 18, "bold"),
        ).grid(row=0, column=0, columnspan=2, pady=(0, 30))

        ttk.Label(
            main_frame,
            text="Please login with your email and password",
            font=("Arial", 12),
        ).grid(row=1, column=0, columnspan=2, pady=(0, 20))

        ttk.Label(main_frame, text="Email:", font=("Arial", 10)).grid(
            row=2, column=0, sticky=tk.W, pady=8
        )
        self.email_entry = ttk.Entry(main_frame, width=35, font=("Arial", 10))
        self.email_entry.grid(row=2, column=1, sticky=(tk.W, tk.E), pady=8, padx=(10, 0))

        ttk.Label(main_frame, text="Password:", font=("Arial", 10)).grid(
            row=3, column=0, sticky=tk.W, pady=8
        )
        self.password_entry = ttk.Entry(main_frame, width=35, show="*", font=("Arial", 10))
        self.password_entry.grid(row=3, column=1, sticky=(tk.W, tk.E), pady=8, padx=(10, 0))

        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=4, column=0, columnspan=2, pady=20)

        ttk.Button(btn_frame, text="Login", command=self.login).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Create Account", command=self.show_register_window).pack(
            side=tk.LEFT, padx=5
        )

        self.app.root.bind("<Return>", lambda event: self.login())
        self.email_entry.focus()

    def login(self):
        """Handle login process via backend /auth/login."""
        email = self.email_entry.get().strip()
        password = self.password_entry.get()

        if not email:
            messagebox.showerror("Error", "Please enter your email address")
            self.email_entry.focus()
            return

        if not password:
            messagebox.showerror("Error", "Please enter your password")
            self.password_entry.focus()
            return

        self.email_entry.config(state="disabled")
        self.password_entry.config(state="disabled")

        try:
            response = self.app.api_client.login(email, password)
            if response and "token" in response:
                self.app.handle_login_success(response.get("user", {}), response["token"])
            else:
                messagebox.showerror("Login Failed", "Invalid email or password")
        except Exception as exc:
            messagebox.showerror("Login Error", f"Unable to login: {exc}")
        finally:
            self.email_entry.config(state="normal")
            self.password_entry.config(state="normal")

    def show_register_window(self):
        """Open a separate window for account creation."""
        if self.register_window and tk.Toplevel.winfo_exists(self.register_window):
            self.register_window.lift()
            return

        self.register_window = tk.Toplevel(self.app.root)
        self.register_window.title("Create Account")
        self.register_window.grab_set()

        frame = ttk.Frame(self.register_window, padding="20")
        frame.grid(row=0, column=0, sticky=(tk.N, tk.S, tk.E, tk.W))
        self.register_window.columnconfigure(0, weight=1)
        self.register_window.rowconfigure(0, weight=1)
        frame.columnconfigure(1, weight=1)

        ttk.Label(frame, text="Name:", font=("Arial", 10)).grid(row=0, column=0, sticky=tk.W, pady=8)
        self.reg_name = ttk.Entry(frame, width=30)
        self.reg_name.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=8, padx=(10, 0))

        ttk.Label(frame, text="Email:", font=("Arial", 10)).grid(row=1, column=0, sticky=tk.W, pady=8)
        self.reg_email = ttk.Entry(frame, width=30)
        self.reg_email.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=8, padx=(10, 0))

        ttk.Label(frame, text="Password:", font=("Arial", 10)).grid(
            row=2, column=0, sticky=tk.W, pady=8
        )
        self.reg_password = ttk.Entry(frame, width=30, show="*")
        self.reg_password.grid(row=2, column=1, sticky=(tk.W, tk.E), pady=8, padx=(10, 0))

        ttk.Label(frame, text="Role:", font=("Arial", 10)).grid(row=3, column=0, sticky=tk.W, pady=8)
        self.reg_role = ttk.Combobox(
            frame, values=["organiser", "attendee"], state="readonly", width=28
        )
        self.reg_role.grid(row=3, column=1, sticky=(tk.W, tk.E), pady=8, padx=(10, 0))
        self.reg_role.set("attendee")

        btns = ttk.Frame(frame)
        btns.grid(row=4, column=0, columnspan=2, pady=15)
        ttk.Button(btns, text="Create Account", command=self.register_user).pack(side=tk.LEFT, padx=5)
        ttk.Button(btns, text="Cancel", command=self._close_register_window).pack(side=tk.LEFT, padx=5)

    def register_user(self):
        """Submit new account details to backend /auth/register."""
        name = self.reg_name.get().strip()
        email = self.reg_email.get().strip()
        password = self.reg_password.get()
        role = self.reg_role.get().strip() or "attendee"

        if not name or not email or not password:
            messagebox.showerror("Error", "Please fill in all fields")
            return

        try:
            response = self.app.api_client.register(name, email, password, role)
            messagebox.showinfo("Success", "Account created. You can now log in.")
            self.email_entry.delete(0, tk.END)
            self.email_entry.insert(0, email)
            self.password_entry.delete(0, tk.END)
            self.password_entry.insert(0, password)
            self._close_register_window()
        except Exception as exc:
            messagebox.showerror("Registration Error", f"Unable to create account: {exc}")

    def _close_register_window(self):
        if self.register_window and tk.Toplevel.winfo_exists(self.register_window):
            self.register_window.destroy()
        self.register_window = None
