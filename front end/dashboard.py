import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from datetime import datetime
from ui_components import ScrollableFrame, COLORS

class Dashboard:
    def __init__(self, app):
        self.app = app
        self.room_data = []  # Initialize room data
        self.current_bookings = {}  # Initialize current bookings for reference
        self.unread_notification_count = 0  # Track unread notifications
        self.notification_badge = None  # Reference to notification badge label

    def _validate_datetime_inputs(self, date: str, start_time: str, end_time: str) -> bool:
        """Shared validation for date/time fields used by create and edit flows."""
        if not date:
            messagebox.showerror("Error", "Please enter a date")
            return False
        if not start_time:
            messagebox.showerror("Error", "Please enter a start time")
            return False
        if not end_time:
            messagebox.showerror("Error", "Please enter an end time")
            return False

        try:
            datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            messagebox.showerror("Error", "Date must be in format YYYY-MM-DD (e.g., 2025-01-15)")
            return False

        try:
            datetime.strptime(start_time, "%H:%M")
            datetime.strptime(end_time, "%H:%M")
        except ValueError:
            messagebox.showerror("Error", "Time must be in format HH:MM (e.g., 09:00)")
            return False

        return True

    def _is_organiser(self) -> bool:
        """Return True if current user has organiser privileges."""
        role = (self.app.current_user or {}).get('role', '').lower()
        return role == "organiser"

    def _require_organiser(self, action_label: str) -> bool:
        """Guard organiser-only actions in the client."""
        if self._is_organiser():
            return True
        messagebox.showerror("Organiser Only", f"{action_label} requires organiser permissions.")
        return False

    def _load_available_rooms(self, date: str, start_time: str, end_time: str, listbox: tk.Listbox, store_attr: str) -> list:
        """Fetch available rooms and populate a given listbox, storing results on the instance."""
        # Show loading state
        listbox.delete(0, tk.END)
        listbox.insert(tk.END, "Checking availability...")
        listbox.update()
        
        try:
            # Backend expects: date (YYYY-MM-DD), start_time (HH:MM), end_time (HH:MM)
            # Ensure time is in HH:MM format (remove seconds if present)
            start_time_clean = start_time.split(':')[0] + ':' + start_time.split(':')[1] if ':' in start_time else start_time
            end_time_clean = end_time.split(':')[0] + ':' + end_time.split(':')[1] if ':' in end_time else end_time
            
            # Ensure date is in YYYY-MM-DD format
            date_clean = date.strip()
            
            rooms = self.app.api_client.get_available_rooms(date_clean, start_time_clean, end_time_clean)
            setattr(self, store_attr, rooms or [])
            listbox.delete(0, tk.END)

            if rooms and len(rooms) > 0:
                for room in rooms:
                    facilities = ', '.join([f.capitalize() for f in room.get('facilities', [])])
                    room_info = f"{room['name']} | {room['capacity']} people | {room.get('building', 'N/A')} | {facilities}"
                    listbox.insert(tk.END, room_info)
            else:
                listbox.insert(tk.END, "No rooms available for selected time")
                listbox.insert(tk.END, "Try a different date or time")
            return rooms
        except Exception as e:
            listbox.delete(0, tk.END)
            error_msg = str(e)
            if "connect" in error_msg.lower():
                listbox.insert(tk.END, "Error: Cannot connect to server")
                listbox.insert(tk.END, "Make sure backend is running")
            else:
                listbox.insert(tk.END, f"Error: {error_msg[:50]}")
            messagebox.showerror("Error", f"Unable to check room availability:\n\n{str(e)}")
            return []

    def _validate_booking_fields(self, title: str, date: str, selected_room) -> bool:
        """Shared form validation for create/edit flows."""
        if not title:
            messagebox.showerror("Error", "Please enter a meeting title")
            return False
        if not date:
            messagebox.showerror("Error", "Please select a date")
            return False
        if not selected_room:
            messagebox.showerror("Error", "Please select a room")
            return False
        return True
    
    def update_notification_badge(self):
        """Update the notification with current unread count"""
        try:
            result = self.app.api_client.get_unread_notification_count()
            self.unread_notification_count = result.get('count', 0)
            
            if self.notification_badge:
                if self.unread_notification_count > 0:
                    self.notification_badge.config(text=f"Notifications ({self.unread_notification_count})")
                else:
                    self.notification_badge.config(text="Notifications")
        except Exception:
            # Silently fail - not critical
            pass
    
    def show_dashboard(self):
        """Main dashboard"""
        # Header
        header_frame = ttk.Frame(self.app.root)
        header_frame.pack(fill=tk.X, padx=20, pady=10)
        
        # Welcome message with role
        user_name = self.app.current_user.get('name', 'User')
        user_role = self.app.current_user.get('role', 'user').capitalize()
        welcome_label = ttk.Label(header_frame, text=f"Welcome, {user_name} ({user_role})", 
                                 font=('Arial', 16, 'bold'))
        welcome_label.pack(side=tk.LEFT)
        
        # Logout button
        logout_btn = ttk.Button(header_frame, text="Logout", 
                               command=self.app.logout)
        logout_btn.pack(side=tk.RIGHT)
        
        # Navigation toolbar
        nav_frame = ttk.Frame(self.app.root)
        nav_frame.pack(fill=tk.X, padx=20, pady=10)
        
        # Navigation buttons (attendees cannot create bookings)
        is_organiser = self._is_organiser()
        nav_buttons = [("Dashboard", self.show_dashboard_view)]
        if is_organiser:
            nav_buttons.append(("Create Booking", self.show_create_booking))
        nav_buttons.extend([
            ("Open Meetings", self.show_open_meetings),
            ("Manage Bookings", self.show_manage_bookings),
            ("Available Rooms", self.show_room_browser),
            ("Profile", self.show_profile)
        ])
        
        for text, command in nav_buttons:
            btn = ttk.Button(nav_frame, text=text, command=command)
            btn.pack(side=tk.LEFT, padx=5)
        
        # Add Notifications button with badge
        notif_btn = ttk.Button(nav_frame, text="Notifications", command=self.show_notifications)
        notif_btn.pack(side=tk.LEFT, padx=5)
        self.notification_badge = notif_btn  # Keep reference for updates
        
        # Update notification count initially
        self.update_notification_badge()
        
        # Content area
        self.content_frame = ttk.Frame(self.app.root)
        self.content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Show default view
        self.show_dashboard_view()
    
    def clear_content(self):
        """Clearing content area"""
        if hasattr(self, 'content_frame'):
            for widget in self.content_frame.winfo_children():
                widget.destroy()
    
    def show_dashboard_view(self):
        """Show dashboard with upcoming and past bookings"""
        self.clear_content()
        
        # Update notification badge when navigating to dashboard
        self.update_notification_badge()
        
        # Create notebook for upcoming vs past
        notebook = ttk.Notebook(self.content_frame)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Upcoming bookings tab
        upcoming_frame = ttk.Frame(notebook)
        notebook.add(upcoming_frame, text="Upcoming Bookings")
        self._show_upcoming_bookings_content(upcoming_frame)
        
        # Past bookings tab
        past_frame = ttk.Frame(notebook)
        notebook.add(past_frame, text="Past Bookings")
        self._show_past_bookings_content(past_frame)
        
        # Public bookings tab for quick access
        public_frame = ttk.Frame(notebook)
        notebook.add(public_frame, text="Open Meetings")
        self._show_public_bookings_content(public_frame)

    def show_open_meetings(self):
        """Standalone view for browsing open meetings"""
        self.clear_content()
        self.update_notification_badge()
        
        main_frame = ttk.Frame(self.content_frame)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        ttk.Label(main_frame, text="Open Meetings", font=('Arial', 16, 'bold')).pack(pady=(0, 15))
        self._show_public_bookings_content(main_frame)
    
    def _show_upcoming_bookings_content(self, parent):
        """Show upcoming bookings content"""
        try:
            bookings = self.app.api_client.get_upcoming_bookings()
            
            if not bookings:
                no_bookings_frame = ttk.Frame(parent)
                no_bookings_frame.pack(expand=True)
                
                ttk.Label(no_bookings_frame, text="No upcoming bookings", 
                         font=('Arial', 14)).pack(pady=20)
                ttk.Button(no_bookings_frame, text="Create Your First Booking",
                          command=self.show_create_booking).pack(pady=10)
                return

            # Display all bookings in a single table
            self._display_bookings_table(parent, bookings, action_type='mixed')
            
        except Exception as e:
            self._show_error_in_frame(parent, "Unable to load upcoming bookings")
    
    def _show_public_bookings_content(self, parent):
        """Show public/open bookings for self-registration"""
        try:
            bookings = self.app.api_client.get_public_bookings()
            if not bookings:
                ttk.Label(parent, text="No open meetings available", font=('Arial', 14)).pack(expand=True, pady=40)
                return
            self._display_bookings_table(parent, bookings, action_type='public')
        except Exception:
            self._show_error_in_frame(parent, "Unable to load open meetings")
    
    def _show_past_bookings_content(self, parent):
        """Show past bookings content"""
        try:
            bookings = self.app.api_client.get_past_bookings()
            
            if not bookings:
                ttk.Label(parent, text="No past bookings", 
                         font=('Arial', 14)).pack(expand=True, pady=50)
                return
            
            # Display all bookings in a single table
            self._display_bookings_table(parent, bookings, action_type='past')

        except Exception as e:
            self._show_error_in_frame(parent, "Unable to load past bookings")
    
    def _display_bookings_table(self, parent, bookings, action_type='none'):
        """
        Display bookings in a table format
        action_type: 'organizer', 'pending', 'accepted', 'mixed', 'past', 'public', or 'none'
        """
        if not bookings:
            ttk.Label(parent, text="No bookings found").pack(pady=50)
            return
        
        # Create main container
        container = ttk.Frame(parent)
        container.pack(fill=tk.BOTH, expand=True)
        
        # Create treeview frame
        tree_frame = ttk.Frame(container)
        tree_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create treeview
        columns = ('Title', 'Room', 'Date', 'Time', 'Attendees', 'Status')
        tree = ttk.Treeview(tree_frame, columns=columns, show='headings', height=12)
        
        # Define headings
        column_widths = {'Title': 150, 'Room': 120, 'Date': 100, 'Time': 120, 'Attendees': 100, 'Status': 100}
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=column_widths[col])
        
        # Store bookings data for later reference
        self.current_bookings = {str(b.get('id')): b for b in bookings}
        
        # Add data
        for booking in bookings:
            tree.insert('', tk.END, values=(
                booking.get('title', ''),
                booking.get('room_name', ''),
                booking.get('date', ''),
                f"{booking.get('start_time', '')} - {booking.get('end_time', '')}",
                f"{booking.get('current_attendees', 0)}/{booking.get('capacity', 0)}",
                booking.get('status', 'Confirmed')
            ), tags=(str(booking.get('id')),))
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Add action buttons based on type
        if action_type == 'organizer':
            # Double-click to view details for organizers
            tree.bind('<Double-1>', lambda e: self._on_booking_select(tree))
            
        elif action_type == 'pending':
            # Add action buttons for pending invitations
            action_frame = ttk.Frame(container)
            action_frame.pack(fill=tk.X, pady=10, padx=10)
            
            ttk.Label(action_frame, text="Select an invitation and:", 
                     font=('Arial', 10)).pack(side=tk.LEFT, padx=5)
            
            ttk.Button(action_frame, text="View Details", 
                      command=lambda: self._view_attendee_booking(tree)).pack(side=tk.LEFT, padx=5)
            
            ttk.Button(action_frame, text="Accept", 
                      command=lambda: self._accept_invitation(tree),
).pack(side=tk.LEFT, padx=5)
            
            ttk.Button(action_frame, text="Decline", 
                      command=lambda: self._decline_booking(tree),
).pack(side=tk.LEFT, padx=5)
            
        elif action_type == 'accepted':
            # Add action buttons for accepted bookings
            action_frame = ttk.Frame(container)
            action_frame.pack(fill=tk.X, pady=10, padx=10)
            
            ttk.Label(action_frame, text="Select a booking and:", 
                     font=('Arial', 10)).pack(side=tk.LEFT, padx=5)
            
            ttk.Button(action_frame, text="View Details", 
                      command=lambda: self._view_attendee_booking(tree)).pack(side=tk.LEFT, padx=5)
            
            ttk.Button(action_frame, text="Leave Booking", 
                      command=lambda: self._decline_booking(tree),
).pack(side=tk.LEFT, padx=5)
        
        elif action_type == 'mixed' or action_type == 'past':
            # For mixed or past bookings, just allow double-click to view
            tree.bind('<Double-1>', lambda e: self._on_booking_select(tree))
            
            # Add view details button
            action_frame = ttk.Frame(container)
            action_frame.pack(fill=tk.X, pady=10, padx=10)
            
            ttk.Label(action_frame, text="Double-click a booking or:", 
                     font=('Arial', 10)).pack(side=tk.LEFT, padx=5)
            
            ttk.Button(action_frame, text="View Details", 
                      command=lambda: self._on_booking_select(tree)).pack(side=tk.LEFT, padx=5)
        elif action_type == 'public':
            action_frame = ttk.Frame(container)
            action_frame.pack(fill=tk.X, pady=10, padx=10)
            ttk.Label(action_frame, text="Select a meeting to register:", font=('Arial', 10)).pack(side=tk.LEFT, padx=5)
            ttk.Button(action_frame, text="Register", command=lambda: self._register_for_public(tree)).pack(side=tk.LEFT, padx=5)
    
    def _on_booking_select(self, tree):
        """Handle booking selection"""
        selection = tree.selection()
        if selection:
            booking_id = tree.item(selection[0], "tags")[0]
            self.show_booking_details(booking_id)
    
    def _show_reason_dialog(self, title, prompt):
        """Show a dialog to get a cancellation/decline reason"""
        dialog = tk.Toplevel(self.app.root)
        dialog.title(title)
        dialog.geometry("400x250")
        dialog.grab_set()
        
        # Center the dialog
        dialog.transient(self.app.root)
        
        result = {"reason": None, "confirmed": False}
        
        # Main frame
        main_frame = ttk.Frame(dialog, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Prompt label
        ttk.Label(main_frame, text=prompt, 
                 font=('Arial', 11), wraplength=350).pack(pady=(0, 15))
        
        # Reason entry
        ttk.Label(main_frame, text="Reason (optional):", 
                 font=('Arial', 10)).pack(anchor=tk.W)
        
        reason_text = tk.Text(main_frame, height=4, width=40, wrap=tk.WORD)
        reason_text.pack(fill=tk.BOTH, expand=True, pady=(5, 15))
        reason_text.focus()
        
        # Button frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=(10, 0))
        
        def confirm():
            result["reason"] = reason_text.get("1.0", tk.END).strip() or None
            result["confirmed"] = True
            dialog.destroy()
        
        def cancel():
            result["confirmed"] = False
            dialog.destroy()
        
        ttk.Button(button_frame, text="Confirm", 
                  command=confirm).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", 
                  command=cancel).pack(side=tk.LEFT, padx=5)
        
        # Wait for dialog to close
        dialog.wait_window()
        return result
    
    def show_booking_details(self, booking_id):
        """Show detailed booking information with management options"""
        try:
            # Fetch full booking details from API
            booking = self.app.api_client.get_booking(int(booking_id))
            
            # Create a new window for booking details
            details_window = tk.Toplevel(self.app.root)
            details_window.title(f"Booking Details - {booking.get('title', 'N/A')}")
            details_window.geometry("600x500")
            details_window.grab_set()  # Modal window
            
            # Main frame
            main_frame = ttk.Frame(details_window, padding="20")
            main_frame.pack(fill=tk.BOTH, expand=True)
            
            # Title
            ttk.Label(main_frame, text=booking.get('title', 'N/A'), 
                     font=('Arial', 16, 'bold')).pack(pady=(0, 20))
            
            # Details frame with grid layout
            details_frame = ttk.Frame(main_frame)
            details_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
            
            # Booking information
            info = [
                ("Room:", booking.get('room_name', 'N/A')),
                ("Date:", booking.get('date', 'N/A')),
                ("Start Time:", booking.get('start_time', 'N/A')),
                ("End Time:", booking.get('end_time', 'N/A')),
                ("Attendees:", f"{booking.get('current_attendees', 0)}/{booking.get('capacity', 0)}"),
                ("Status:", booking.get('status', 'Confirmed')),
            ]
            
            for i, (label, value) in enumerate(info):
                ttk.Label(details_frame, text=label, 
                         font=('Arial', 10, 'bold')).grid(row=i, column=0, sticky=tk.W, pady=5, padx=(0, 10))
                ttk.Label(details_frame, text=value, 
                         font=('Arial', 10)).grid(row=i, column=1, sticky=tk.W, pady=5)
            
            # Attendee emails section
            attendee_emails = booking.get('attendee_emails', [])
            if attendee_emails:
                row_offset = len(info)
                ttk.Label(details_frame, text="Invited:", 
                         font=('Arial', 10, 'bold')).grid(row=row_offset, column=0, sticky=tk.NW, pady=5, padx=(0, 10))
                
                # Display emails as comma-separated list with wrapping
                emails_text = ", ".join(attendee_emails)
                emails_label = ttk.Label(details_frame, text=emails_text, 
                                        font=('Arial', 10), wraplength=350)
                emails_label.grid(row=row_offset, column=1, sticky=tk.W, pady=5)
            
            # Notes section
            if booking.get('notes'):
                ttk.Label(main_frame, text="Notes:", 
                         font=('Arial', 10, 'bold')).pack(anchor=tk.W, pady=(10, 5))
                
                notes_frame = ttk.Frame(main_frame, relief='solid', borderwidth=1)
                notes_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
                
                notes_text = tk.Text(notes_frame, height=5, wrap=tk.WORD, 
                                    font=('Arial', 10), state='disabled')
                notes_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
                notes_text.config(state='normal')
                notes_text.insert('1.0', booking.get('notes', ''))
                notes_text.config(state='disabled')
            
            # Action buttons (only if organizer)
            if booking.get('is_organizer'):
                button_frame = ttk.Frame(main_frame)
                button_frame.pack(fill=tk.X, pady=(10, 0))
                
                ttk.Button(button_frame, text="Edit Booking", 
                          command=lambda: [details_window.destroy(), self.edit_booking(booking)]).pack(side=tk.LEFT, padx=5)
                
                ttk.Button(button_frame, text="Cancel Booking", 
                          command=lambda: [details_window.destroy(), self.cancel_booking(booking)],
).pack(side=tk.LEFT, padx=5)
                
                ttk.Button(button_frame, text="Close", 
                          command=details_window.destroy).pack(side=tk.RIGHT, padx=5)
            else:
                ttk.Button(main_frame, text="Close", 
                          command=details_window.destroy).pack(pady=(10, 0))
            
        except Exception as e:
            error_msg = str(e)
            if "not found" in error_msg.lower() or "404" in error_msg:
                messagebox.showinfo("Booking Not Found", 
                    "This booking no longer exists.\n\n"
                    "It may have been cancelled by the organiser.")
            else:
                messagebox.showerror("Error", f"Unable to load booking details: {error_msg}")
    
    def _view_attendee_booking(self, tree):
        """View details of a booking as attendee"""
        selection = tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a booking to view")
            return
        
        booking_id = tree.item(selection[0], "tags")[0]
        
        try:
            # Fetch full booking details from API
            booking = self.app.api_client.get_booking(int(booking_id))
            
            # Create info message with booking details
            info = f"""
Booking Details

Title: {booking.get('title', 'N/A')}
Room: {booking.get('room_name', 'N/A')}
Date: {booking.get('date', 'N/A')}
Time: {booking.get('start_time', 'N/A')} - {booking.get('end_time', 'N/A')}
Attendees: {booking.get('current_attendees', 0)}/{booking.get('capacity', 0)}
Status: {booking.get('status', 'Confirmed')}

Notes: {booking.get('notes', 'None')}
"""
            messagebox.showinfo("Booking Details", info.strip())
            
        except Exception as e:
            messagebox.showerror("Error", f"Unable to load booking details: {str(e)}")
    
    def _decline_booking(self, tree):
        """Decline/leave a booking as attendee with optional reason"""
        selection = tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a booking to leave")
            return
        
        booking_id = tree.item(selection[0], "tags")[0]
        
        # Get booking info from stored data
        booking = self.current_bookings.get(booking_id, {})
        booking_title = booking.get('title', 'this booking')
        
        # Show reason dialog
        result = self._show_reason_dialog(
            "Decline/Leave Booking",
            f"Are you sure you want to leave '{booking_title}'?\n\n"
            "You will no longer be registered for this meeting.\n\n"
            "You can optionally provide a reason:"
        )
        
        if not result["confirmed"]:
            return
        
        try:
            # Call API to decline invitation with optional reason
            response = self.app.api_client.decline_invitation(int(booking_id), result["reason"])
            
            if response:
                messagebox.showinfo("Success", 
                                  f"You have successfully left '{booking_title}'")
                # Update notification badge
                self.update_notification_badge()
                # Refresh the bookings view
                self.show_dashboard_view()
            else:
                messagebox.showerror("Error", "Failed to leave booking")
                
        except Exception as e:
            messagebox.showerror("Error", f"Unable to leave booking: {str(e)}")
    
    def _accept_invitation(self, tree):
        """Accept a pending invitation"""
        selection = tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select an invitation to accept")
            return
        
        booking_id = tree.item(selection[0], "tags")[0]
        
        # Get booking info from stored data
        booking = self.current_bookings.get(booking_id, {})
        booking_title = booking.get('title', 'this booking')
        
        try:
            # Call API to accept invitation
            response = self.app.api_client.accept_invitation(int(booking_id))
            
            if response:
                messagebox.showinfo("Success", 
                                  f"You have accepted the invitation to '{booking_title}'")
                # Update notification badge
                self.update_notification_badge()
                # Refresh the bookings view
                self.show_dashboard_view()
            else:
                messagebox.showerror("Error", "Failed to accept invitation")
                
        except Exception as e:
            messagebox.showerror("Error", f"Unable to accept invitation: {str(e)}")
    
    def _register_for_public(self, tree):
        """Register for a public meeting"""
        selection = tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a meeting to register")
            return
        
        booking_id = tree.item(selection[0], "tags")[0]
        booking = self.current_bookings.get(booking_id, {})
        title = booking.get('title', 'this meeting')
        
        if not messagebox.askyesno("Confirm Registration", f"Join '{title}'?"):
            return
        
        try:
            self.app.api_client.register_for_booking(int(booking_id))
            messagebox.showinfo("Registered", f"You are now registered for '{title}'")
            self.show_open_meetings()
        except Exception as e:
            messagebox.showerror("Error", f"Unable to register: {str(e)}")
    
    def show_notifications(self):
        """Show notifications view"""
        self.clear_content()
        
        main_frame = ttk.Frame(self.content_frame)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Header
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 20))
        
        ttk.Label(header_frame, text="Notifications", 
                 font=('Arial', 16, 'bold')).pack(side=tk.LEFT)
        
        ttk.Button(header_frame, text="Refresh", 
                  command=self.show_notifications).pack(side=tk.RIGHT, padx=5)
        
        ttk.Button(header_frame, text="Mark All as Read", 
                  command=self._mark_all_notifications_read).pack(side=tk.RIGHT, padx=5)
        
        try:
            notifications = self.app.api_client.get_notifications()
            
            if not notifications:
                no_notif_frame = ttk.Frame(main_frame)
                no_notif_frame.pack(expand=True)
                
                ttk.Label(no_notif_frame, text="No notifications", 
                         font=('Arial', 14)).pack(pady=20)
                return
            
            # Create scrollable frame for notifications
            canvas = tk.Canvas(main_frame)
            scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
            scrollable_frame = ttk.Frame(canvas)
            
            scrollable_frame.bind(
                "<Configure>",
                lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
            )
            
            canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
            canvas.configure(yscrollcommand=scrollbar.set)
            
            # Pack canvas and scrollbar
            canvas.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")
            
            # Create notification cards
            for notif in notifications:
                self._create_notification_card(scrollable_frame, notif)
            
            # Update badge after showing notifications
            self.update_notification_badge()
            
        except Exception as e:
            self._show_error_in_frame(main_frame, "Unable to load notifications")
    
    def _create_notification_card(self, parent, notification):
        """Create a notification card"""
        # Determine card style based on read status
        if notification['is_read']:
            relief_style = 'flat'
            bg_color = None
        else:
            relief_style = 'raised'
            bg_color = None
        
        card_frame = ttk.LabelFrame(parent, text=notification['title'], padding="10", relief=relief_style)
        card_frame.pack(fill=tk.X, pady=5, padx=10)
        
        # Notification type icon (clean Unicode symbols)
        type_icons = {
            'booking_cancelled': '×',
            'invitation_declined': '○',
            'booking_reminder': '●',
            'invitation_received': '▸',
            'booking_updated': '◆',
            'invitation_accepted': '✓'
        }
        icon = type_icons.get(notification['type'], '•')
        
        # Header with icon and time
        header_frame = ttk.Frame(card_frame)
        header_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(header_frame, text=f"{icon} {notification['type'].replace('_', ' ').title()}", 
                 font=('Arial', 10, 'bold')).pack(side=tk.LEFT)
        
        ttk.Label(header_frame, text=notification['created_at'], 
                 font=('Arial', 8), foreground='gray').pack(side=tk.RIGHT)
        
        # Message
        message_label = ttk.Label(card_frame, text=notification['message'], 
                                 font=('Arial', 10), wraplength=700)
        message_label.pack(fill=tk.X, pady=(0, 10))
        
        # Action buttons
        button_frame = ttk.Frame(card_frame)
        button_frame.pack(fill=tk.X)
        
        if notification['booking_id']:
            ttk.Button(button_frame, text="View Booking", 
                      command=lambda: self.show_booking_details(notification['booking_id'])).pack(side=tk.LEFT, padx=2)
        
        if not notification['is_read']:
            ttk.Button(button_frame, text="Mark as Read", 
                      command=lambda n_id=notification['id']: self._mark_notification_read(n_id),
).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(button_frame, text="Delete", 
                  command=lambda n_id=notification['id']: self._delete_notification(n_id),
).pack(side=tk.RIGHT, padx=2)
    
    def _mark_notification_read(self, notification_id):
        """Mark a single notification as read"""
        try:
            self.app.api_client.mark_notification_read(notification_id)
            self.show_notifications()  # Refresh view
        except Exception as e:
            messagebox.showerror("Error", f"Unable to mark notification as read: {str(e)}")
    
    def _mark_all_notifications_read(self):
        """Mark all notifications as read"""
        try:
            notifications = self.app.api_client.get_notifications()
            for notif in notifications:
                if not notif['is_read']:
                    self.app.api_client.mark_notification_read(notif['id'])
            self.show_notifications()  # Refresh view
            messagebox.showinfo("Success", "All notifications marked as read")
        except Exception as e:
            messagebox.showerror("Error", f"Unable to mark notifications as read: {str(e)}")
    
    def _delete_notification(self, notification_id):
        """Delete a notification"""
        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this notification?"):
            try:
                self.app.api_client.delete_notification(notification_id)
                self.show_notifications()  # Refresh view
            except Exception as e:
                messagebox.showerror("Error", f"Unable to delete notification: {str(e)}")
    
    def show_create_booking(self, preselected_room=None):
        """Show booking creation form with optional pre-selected room"""
        if not self._require_organiser("Creating bookings"):
            return
        self.clear_content()
        
        # Update notification badge
        self.update_notification_badge()
        
        form_frame = ttk.Frame(self.content_frame)
        form_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Title
        if preselected_room:
            title_text = f"Create New Booking - {preselected_room['name']}"
        else:
            title_text = "Create New Booking"
        
        ttk.Label(form_frame, text=title_text, 
                 font=('Arial', 16, 'bold')).grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # Form fields
        fields = [
            ("Meeting Title *", "title", "entry"),
            ("Date * (YYYY-MM-DD)", "date", "entry"),
            ("Start Time (HH:MM)", "start_time", "entry"), 
            ("End Time (HH:MM)", "end_time", "entry"),
            ("Additional Notes", "notes", "text")
        ]
        
        self.form_widgets = {}
        
        for i, (label, field, widget_type) in enumerate(fields):
            ttk.Label(form_frame, text=label).grid(row=i+1, column=0, sticky=tk.W, pady=8)
            
            if widget_type == "entry":
                widget = ttk.Entry(form_frame, width=40)
                widget.grid(row=i+1, column=1, sticky=(tk.W, tk.E), pady=8, padx=(10, 0))
                
                # Set default values
                if field == "date":
                    widget.insert(0, datetime.now().strftime("%Y-%m-%d"))
                elif field == "start_time":
                    widget.insert(0, "09:00")
                elif field == "end_time":
                    widget.insert(0, "10:00")
                    
            elif widget_type == "text":
                widget = tk.Text(form_frame, width=40, height=4)
                widget.grid(row=i+1, column=1, sticky=(tk.W, tk.E), pady=8, padx=(10, 0))
            
            self.form_widgets[field] = widget
        
        # Room selection with modern styling
        ttk.Label(form_frame, text="Select Room:", font=('SF Pro Display', 10, 'bold')).grid(row=len(fields)+1, column=0, sticky=tk.W, pady=8)
        
        room_frame = tk.Frame(form_frame, bg=COLORS['background'])
        room_frame.grid(row=len(fields)+1, column=1, sticky=(tk.W, tk.E), pady=8, padx=(10, 0))
        
        # Modern styled listbox
        listbox_container = tk.Frame(room_frame, bg=COLORS['border'], padx=2, pady=2)
        listbox_container.pack(fill=tk.BOTH, expand=True)
        
        self.room_listbox = tk.Listbox(
            listbox_container,
            width=50,
            height=10,
            font=('SF Pro Text', 10),
            bg=COLORS['surface'],
            fg=COLORS['text'],
            selectbackground=COLORS['primary'],
            selectforeground='white',
            relief='flat',
            bd=0,
            highlightthickness=0
        )
        room_scrollbar = ttk.Scrollbar(listbox_container, orient=tk.VERTICAL, command=self.room_listbox.yview)
        self.room_listbox.configure(yscrollcommand=room_scrollbar.set)
        
        self.room_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        room_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # If room is preselected, populate and select it
        if preselected_room:
            self.room_data = [preselected_room]
            room_info = f"{preselected_room['name']} | Cap: {preselected_room['capacity']} | Facilities: {', '.join(preselected_room.get('facilities', []))}"
            self.room_listbox.insert(tk.END, room_info)
            self.room_listbox.selection_set(0)  # Select the room
            
            # Show a label indicating the room is pre-selected
            preselect_label = ttk.Label(form_frame, 
                                       text="Room pre-selected from browser", 
                                       font=('Arial', 9), 
                                       foreground='green')
            preselect_label.grid(row=len(fields)+2, column=1, sticky=tk.W, pady=(0, 5), padx=(10, 0))
            row_offset = 1
        else:
            # Show instruction to check availability
            self.room_listbox.insert(tk.END, "Click 'Check Available Rooms' to see available rooms")
            row_offset = 0
        
        # Check availability button (modern)
        from ui_components import ModernButton
        check_btn = ModernButton(
            form_frame,
            text="Check Available Rooms",
            command=self.check_availability,
            style='primary',
            width=25
        )
        check_btn.grid(row=len(fields)+2+row_offset, column=0, columnspan=2, pady=15)
        
        # Attendees
        ttk.Label(form_frame, text="Invite Attendees (emails, comma separated):").grid(
            row=len(fields)+3+row_offset, column=0, sticky=tk.W, pady=8)
        self.attendees_entry = ttk.Entry(form_frame, width=40)
        self.attendees_entry.grid(row=len(fields)+3+row_offset, column=1, sticky=(tk.W, tk.E), pady=8, padx=(10, 0))
        
        # Submit button
        ttk.Button(form_frame, text="Create Booking", 
                  command=self.create_booking).grid(
                  row=len(fields)+4+row_offset, column=0, columnspan=2, pady=20)
        
        # Configure grid weights
        form_frame.columnconfigure(1, weight=1)
    
    def check_availability(self):
        """Check room availability based on form inputs"""
        date = self.form_widgets['date'].get().strip()
        start_time = self.form_widgets['start_time'].get().strip()
        end_time = self.form_widgets['end_time'].get().strip()
        if not self._validate_datetime_inputs(date, start_time, end_time):
            return
        self._load_available_rooms(date, start_time, end_time, self.room_listbox, "room_data")
    
    def get_selected_room(self):
        """Get selected room data"""
        selection = self.room_listbox.curselection()
        if selection and hasattr(self, 'room_data'):
            return self.room_data[selection[0]]
        return None
    
    def create_booking(self):
        """Create new booking"""
        # Get form data
        title = self.form_widgets['title'].get().strip()
        date = self.form_widgets['date'].get().strip()
        start_time = self.form_widgets['start_time'].get().strip()
        end_time = self.form_widgets['end_time'].get().strip()
        notes = self.form_widgets['notes'].get("1.0", tk.END).strip()  # Text widget always uses this
        
        selected_room = self.get_selected_room()
        attendee_emails = [email.strip() for email in self.attendees_entry.get().split(",") if email.strip()]
        
        # Validation
        if not self._validate_booking_fields(title, date, selected_room):
            return
        
        try:
            booking_data = {
                "title": title,
                "date": date,
                "start_time": start_time,
                "end_time": end_time,
                "room_id": selected_room["id"],
                "attendee_emails": attendee_emails,
                "notes": notes
            }
            
            response = self.app.api_client.create_booking(booking_data)
            
            if response:
                messagebox.showinfo("Success", "Booking created successfully!")
                self.show_dashboard_view()
            else:
                messagebox.showerror("Error", "Failed to create booking")

        except Exception as e:
            messagebox.showerror("Error", f"Unable to create booking: {str(e)}")
    
    def show_manage_bookings(self):
        """Show manage bookings view with organized and invited tabs"""
        self.clear_content()

        # Update notification badge
        self.update_notification_badge()
        
        # Create notebook for organized vs invited
        notebook = ttk.Notebook(self.content_frame)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Organized meetings tab
        organized_frame = ttk.Frame(notebook)
        notebook.add(organized_frame, text="Organized Meetings")
        self._show_organized_meetings_content(organized_frame)
        
        # Invited meetings tab
        invited_frame = ttk.Frame(notebook)
        notebook.add(invited_frame, text="Invited Meetings")
        self._show_invited_meetings_content(invited_frame)
    
    def _show_organized_meetings_content(self, parent):
        """Show organized meetings content with management options"""
        try:
            bookings = self.app.api_client.get_organized_bookings()
            
            if not bookings:
                ttk.Label(parent, text="You haven't organized any bookings", 
                         font=('Arial', 12)).pack(expand=True, pady=50)
                return

            # Display bookings as cards
            # Create a scrollable frame
            canvas = tk.Canvas(parent)
            scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
            scrollable_frame = ttk.Frame(canvas)
            
            scrollable_frame.bind(
                "<Configure>",
                lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
            )
            
            canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
            canvas.configure(yscrollcommand=scrollbar.set)
            
            # Pack canvas and scrollbar
            canvas.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")
            
            # Create booking cards
            for booking in bookings:
                self._create_booking_card(scrollable_frame, booking)
                
        except Exception as e:
            self._show_error_in_frame(parent, "Unable to load organized bookings")
    
    def _show_invited_meetings_content(self, parent):
        """Show invited meetings content (pending and accepted)"""
        try:
            # Get all upcoming bookings and filter for invited ones
            all_bookings = self.app.api_client.get_upcoming_bookings()
            
            # Filter for bookings where user is invited (not organizer)
            invited_bookings = [b for b in all_bookings if not b.get('is_organizer')]
            
            if not invited_bookings:
                ttk.Label(parent, text="You don't have any invitations", 
                         font=('Arial', 12)).pack(expand=True, pady=50)
                return
            
            # Separate pending and accepted
            pending = [b for b in invited_bookings if b.get('invitation_status') == 'pending']
            accepted = [b for b in invited_bookings if b.get('invitation_status') == 'accepted']
            
            # Create sub-notebook for pending vs accepted
            sub_notebook = ttk.Notebook(parent)
            sub_notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            
            # Pending invitations sub-tab
            pending_frame = ttk.Frame(sub_notebook)
            sub_notebook.add(pending_frame, text="Pending Invitations")
            self._display_bookings_table(pending_frame, pending, action_type='pending')
            
            # Accepted bookings sub-tab
            accepted_frame = ttk.Frame(sub_notebook)
            sub_notebook.add(accepted_frame, text="Accepted")
            self._display_bookings_table(accepted_frame, accepted, action_type='accepted')
            
        except Exception as e:
            self._show_error_in_frame(parent, "Unable to load invited meetings")
    
    def _create_booking_card(self, parent, booking):
        """Create a booking card with management options"""
        card_frame = ttk.LabelFrame(parent, text=booking['title'], padding="10")
        card_frame.pack(fill=tk.X, pady=5, padx=10)
        
        # Booking info
        info_text = f"Room: {booking['room_name']} | Date: {booking['date']} | Time: {booking['start_time']}-{booking['end_time']}"
        ttk.Label(card_frame, text=info_text).grid(row=0, column=0, sticky=tk.W)
        
        # Attendee info
        attendee_text = f"Attendees: {booking.get('current_attendees', 0)}/{booking.get('capacity', 0)}"
        ttk.Label(card_frame, text=attendee_text).grid(row=1, column=0, sticky=tk.W)
        
        # Action buttons
        btn_frame = ttk.Frame(card_frame)
        btn_frame.grid(row=0, column=1, rowspan=2, sticky=tk.E)
        
        ttk.Button(btn_frame, text="Edit", 
                  command=lambda b=booking: self.edit_booking(b)).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Cancel", 
                  command=lambda b=booking: self.cancel_booking(b)).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="View Details", 
                  command=lambda b=booking: self.show_booking_details(b['id'])).pack(side=tk.LEFT, padx=2)
        
        # Configure grid weights
        card_frame.columnconfigure(0, weight=1)
    
    def edit_booking(self, booking):
        """Edit existing booking"""
        if not self._require_organiser("Editing bookings"):
            return
        self.clear_content()
        
        form_frame = ttk.Frame(self.content_frame)
        form_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Title
        ttk.Label(form_frame, text=f"Edit Booking: {booking.get('title', '')}", 
                 font=('Arial', 16, 'bold')).grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # Form fields
        fields = [
            ("Meeting Title *", "title", "entry"),
            ("Date * (YYYY-MM-DD)", "date", "entry"),
            ("Start Time (HH:MM)", "start_time", "entry"), 
            ("End Time (HH:MM)", "end_time", "entry"),
            ("Additional Notes", "notes", "text")
        ]
        
        self.edit_form_widgets = {}
        self.editing_booking_id = booking.get('id')
        
        for i, (label, field, widget_type) in enumerate(fields):
            ttk.Label(form_frame, text=label).grid(row=i+1, column=0, sticky=tk.W, pady=8)
            
            if widget_type == "entry":
                widget = ttk.Entry(form_frame, width=40)
                widget.grid(row=i+1, column=1, sticky=(tk.W, tk.E), pady=8, padx=(10, 0))
                
                # Pre-fill with existing data
                if field == "title":
                    widget.insert(0, booking.get('title', ''))
                elif field == "date":
                    widget.insert(0, booking.get('date', ''))
                elif field == "start_time":
                    widget.insert(0, booking.get('start_time', ''))
                elif field == "end_time":
                    widget.insert(0, booking.get('end_time', ''))
                    
            elif widget_type == "text":
                widget = tk.Text(form_frame, width=40, height=4)
                widget.grid(row=i+1, column=1, sticky=(tk.W, tk.E), pady=8, padx=(10, 0))
                # Pre-fill notes
                if booking.get('notes'):
                    widget.insert('1.0', booking.get('notes'))
            
            self.edit_form_widgets[field] = widget
        
        # Room selection (read-only display of current room)
        ttk.Label(form_frame, text="Current Room:").grid(row=len(fields)+1, column=0, sticky=tk.W, pady=8)
        ttk.Label(form_frame, text=booking.get('room_name', 'N/A'),
                 font=('Arial', 10, 'bold')).grid(row=len(fields)+1, column=1, sticky=tk.W, pady=8, padx=(10, 0))
        
        # Check availability for new time slot
        ttk.Label(form_frame, text="Select New Room:").grid(row=len(fields)+2, column=0, sticky=tk.W, pady=8)
        
        room_frame = ttk.Frame(form_frame)
        room_frame.grid(row=len(fields)+2, column=1, sticky=(tk.W, tk.E), pady=8, padx=(10, 0))
        
        self.edit_room_listbox = tk.Listbox(room_frame, width=50, height=6)
        room_scrollbar = ttk.Scrollbar(room_frame, orient=tk.VERTICAL, command=self.edit_room_listbox.yview)
        self.edit_room_listbox.configure(yscrollcommand=room_scrollbar.set)
        
        self.edit_room_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        room_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Pre-select current room (will be populated after checking availability)
        self.current_room_id = booking.get('room_id')  # Store for later comparison
        
        # Check availability button (modern)
        from ui_components import ModernButton
        check_btn = ModernButton(
            form_frame,
            text="Check Available Rooms",
            command=self.check_availability_for_edit,
            style='primary',
            width=25
        )
        check_btn.grid(row=len(fields)+3, column=0, columnspan=2, pady=15)
        
        # Current attendees display
        current_attendees = booking.get('attendee_emails', [])
        if current_attendees:
            ttk.Label(form_frame, text="Current Attendees:", 
                     font=('Arial', 10, 'bold')).grid(row=len(fields)+4, column=0, sticky=tk.W, pady=8)
            attendees_text = ", ".join(current_attendees)
            ttk.Label(form_frame, text=attendees_text, 
                     font=('Arial', 9), foreground='gray', wraplength=350).grid(
                row=len(fields)+4, column=1, sticky=tk.W, pady=8, padx=(10, 0))
            row_offset = len(fields) + 5
        else:
            row_offset = len(fields) + 4
        
        # Add additional attendees field
        ttk.Label(form_frame, text="Add Attendees (emails, comma separated):").grid(
            row=row_offset, column=0, sticky=tk.W, pady=8)
        self.edit_attendees_entry = ttk.Entry(form_frame, width=40)
        self.edit_attendees_entry.grid(row=row_offset, column=1, sticky=(tk.W, tk.E), pady=8, padx=(10, 0))
        
        # Store current attendees for later
        self.current_attendee_emails = current_attendees
        
        # Action buttons
        button_frame = ttk.Frame(form_frame)
        button_frame.grid(row=row_offset+1, column=0, columnspan=2, pady=20)
        
        ttk.Button(button_frame, text="Save Changes", 
                  command=self.save_booking_edits).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(button_frame, text="Cancel", 
                  command=self.show_manage_bookings).pack(side=tk.LEFT, padx=5)
        
        # Configure grid weights
        form_frame.columnconfigure(1, weight=1)
        
        # Auto-check availability with current date/time
        self.check_availability_for_edit()
    
    def cancel_booking(self, booking):
        """Cancel a booking with optional reason"""
        if not self._require_organiser("Cancelling bookings"):
            return
        # Show reason dialog
        result = self._show_reason_dialog(
            "Cancel Booking",
            f"Are you sure you want to cancel '{booking['title']}'?\n\n"
            "All attendees will be notified.\n\n"
            "You can optionally provide a reason:"
        )
        
        if not result["confirmed"]:
            return
        
        try:
            success = self.app.api_client.cancel_booking(booking['id'], result["reason"])
            if success:
                messagebox.showinfo("Success", "Booking cancelled successfully")
                self.update_notification_badge()
                self.show_manage_bookings()
            else:
                messagebox.showerror("Error", "Failed to cancel booking")
        except Exception as e:
            messagebox.showerror("Error", f"Unable to cancel booking: {str(e)}")
    
    def check_availability_for_edit(self):
        """Check room availability for editing (similar to check_availability but for edit form)"""
        if not hasattr(self, 'edit_form_widgets'):
            return
            
        date = self.edit_form_widgets['date'].get().strip()
        start_time = self.edit_form_widgets['start_time'].get().strip()
        end_time = self.edit_form_widgets['end_time'].get().strip()
        
        if not self._validate_datetime_inputs(date, start_time, end_time):
            return

        rooms = self._load_available_rooms(date, start_time, end_time, self.edit_room_listbox, "edit_room_data")

        # Pre-select current room if it's available
        if rooms:
            for i, room in enumerate(rooms):
                if room['id'] == self.current_room_id:
                    self.edit_room_listbox.selection_set(i)
                    self.edit_room_listbox.see(i)
                    break
    
    def get_selected_room_for_edit(self):
        """Get selected room data from edit form"""
        selection = self.edit_room_listbox.curselection()
        if selection and hasattr(self, 'edit_room_data'):
            return self.edit_room_data[selection[0]]
        return None
    
    def save_booking_edits(self):
        """Save changes to existing booking"""
        if not self._require_organiser("Editing bookings"):
            return
        # Get form data
        title = self.edit_form_widgets['title'].get().strip()
        date = self.edit_form_widgets['date'].get().strip()
        start_time = self.edit_form_widgets['start_time'].get().strip()
        end_time = self.edit_form_widgets['end_time'].get().strip()
        notes = self.edit_form_widgets['notes'].get("1.0", tk.END).strip()
        
        selected_room = self.get_selected_room_for_edit()
        
        # Get additional attendees
        additional_attendees = [email.strip() for email in self.edit_attendees_entry.get().split(",") if email.strip()]
        
        # Combine existing and new attendees
        all_attendee_emails = list(self.current_attendee_emails) + additional_attendees
        
        # Validation
        if not self._validate_booking_fields(title, date, selected_room):
            return
        
        try:
            # Prepare update data with all attendees (existing + new)
            booking_data = {
                "title": title,
                "date": date,
                "start_time": start_time,
                "end_time": end_time,
                "room_id": selected_room["id"],
                "attendee_emails": all_attendee_emails,  # All attendees (existing + new)
                "notes": notes,
            }
            
            response = self.app.api_client.update_booking(self.editing_booking_id, booking_data)
            
            if response:
                messagebox.showinfo("Success", "Booking updated successfully!")
                self.show_manage_bookings()
            else:
                messagebox.showerror("Error", "Failed to update booking")
                
        except Exception as e:
            messagebox.showerror("Error", f"Unable to update booking: {str(e)}")
    
    def show_room_browser(self):
        """Show room browser"""
        self.clear_content()
        
        # Update notification badge
        self.update_notification_badge()
        
        main_frame = ttk.Frame(self.content_frame)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Header
        ttk.Label(main_frame, text="Room Browser", 
                 font=('Arial', 16, 'bold')).pack(pady=(0, 20))
        
        # Filters frame
        filter_frame = ttk.LabelFrame(main_frame, text="Filters", padding="10")
        filter_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Capacity filter
        ttk.Label(filter_frame, text="Capacity:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        self.capacity_var = tk.StringVar(value="All")
        capacity_combo = ttk.Combobox(filter_frame, textvariable=self.capacity_var,
                                     values=["All", "Small (1-5)", "Medium (6-15)", "Large (16+)"],
                                     state="readonly", width=15)
        capacity_combo.grid(row=0, column=1, padx=(0, 20))
        
        # Facilities filter
        ttk.Label(filter_frame, text="Facilities:").grid(row=0, column=2, sticky=tk.W, padx=(0, 10))
        self.facilities_var = tk.StringVar(value="Any")
        facilities_combo = ttk.Combobox(filter_frame, textvariable=self.facilities_var,
                                       values=["Any", "projector", "whiteboard", "display", "video conferencing", 
                                              "sound system", "computers", "recording", "microphone", "coffee machine"],
                                       state="readonly", width=18)
        facilities_combo.grid(row=0, column=3, padx=(0, 20))

        # Accessibility filter
        ttk.Label(filter_frame, text="Accessibility:").grid(row=0, column=4, sticky=tk.W, padx=(0, 10))
        self.accessibility_var = tk.StringVar(value="Any")
        accessibility_combo = ttk.Combobox(filter_frame, textvariable=self.accessibility_var,
                                        values=["Any", "Wheelchair Accessible", "Hearing Loop"],
                                        state="readonly", width=15)
        accessibility_combo.grid(row=0, column=5, padx=(0, 20))
        
        # Apply filters button
        ttk.Button(filter_frame, text="Apply Filters", 
                  command=self.load_rooms).grid(row=0, column=6)
        
        # Create scrollable canvas for rooms
        canvas_container = ttk.Frame(main_frame)
        canvas_container.pack(fill=tk.BOTH, expand=True)
        
        self.rooms_canvas = tk.Canvas(canvas_container, bg=COLORS['background'], highlightthickness=0)
        scrollbar = ttk.Scrollbar(canvas_container, orient="vertical", command=self.rooms_canvas.yview)
        
        self.rooms_frame = ttk.Frame(self.rooms_canvas)
        
        self.rooms_canvas.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.rooms_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.canvas_window = self.rooms_canvas.create_window((0, 0), window=self.rooms_frame, anchor="nw")
        
        # Configure scrolling
        self.rooms_frame.bind("<Configure>", lambda e: self.rooms_canvas.configure(scrollregion=self.rooms_canvas.bbox("all")))
        self.rooms_canvas.bind("<Configure>", lambda e: self.rooms_canvas.itemconfig(self.canvas_window, width=e.width))
        
        # Mousewheel scrolling
        self.rooms_canvas.bind_all("<MouseWheel>", lambda e: self.rooms_canvas.yview_scroll(int(-1*(e.delta/120)), "units"))
        
        # Load rooms initially
        self.load_rooms()
    
    def load_rooms(self):
        """Load and display rooms based on filters"""
        # Clear existing rooms
        for widget in self.rooms_frame.winfo_children():
            widget.destroy()
        
        # Show loading state
        loading_label = ttk.Label(self.rooms_frame, text="Loading rooms...", font=('Arial', 12))
        loading_label.pack(pady=50)
        self.rooms_frame.update()
        
        try:
            rooms = self.app.api_client.get_all_rooms()
            
            # Remove loading label
            loading_label.destroy()
            
            if not rooms:
                ttk.Label(self.rooms_frame, text="No rooms available", font=('Arial', 12)).pack(pady=50)
                return
            
            # Apply filters
            filtered_rooms = self._apply_filters(rooms)
            
            if not filtered_rooms:
                ttk.Label(self.rooms_frame, text="No rooms match your criteria", font=('Arial', 12)).pack(pady=50)
                return
            
            # Create room cards
            for i, room in enumerate(filtered_rooms):
                self._create_room_card(room, i)
                
        except Exception as e:
            # Show error
            for widget in self.rooms_frame.winfo_children():
                widget.destroy()
            ttk.Label(self.rooms_frame, text=f"Unable to load rooms: {str(e)}", 
                     font=('Arial', 11), foreground='red', wraplength=500).pack(pady=50)
    
    def _apply_filters(self, rooms):
        """Apply filters to room list"""
        filtered_rooms = rooms
        
        # Capacity filter
        capacity_filter = self.capacity_var.get()
        if capacity_filter != "All":
            if capacity_filter == "Small (1-5)":
                filtered_rooms = [r for r in filtered_rooms if r.get('capacity', 0) <= 5]
            elif capacity_filter == "Medium (6-15)":
                filtered_rooms = [r for r in filtered_rooms if 6 <= r.get('capacity', 0) <= 15]
            elif capacity_filter == "Large (16+)":
                filtered_rooms = [r for r in filtered_rooms if r.get('capacity', 0) >= 16]
        
        # Facilities filter 
        facilities_filter = self.facilities_var.get()
        if facilities_filter != "Any":
            filter_lower = facilities_filter.lower()
            # Check if any facility in the room contains the filter text
            filtered_rooms = [
                r for r in filtered_rooms 
                if any(filter_lower in facility.lower() for facility in r.get('facilities', []))
            ]

        # Accessibility filter
        accessibility_filter = self.accessibility_var.get()
        if accessibility_filter != "Any":
            filter_lower = accessibility_filter.lower()
            # Check if any accessibility feature in the room contains the filter text
            filtered_rooms = [
                r for r in filtered_rooms 
                if any(filter_lower in feature.lower() for feature in r.get('accessibility', []))
            ]
        
        return filtered_rooms
    
    def _create_room_card(self, room, index):
        """Create a room card display"""
        card_frame = ttk.Frame(self.rooms_frame, relief='solid', borderwidth=1, padding="10")
        card_frame.pack(fill=tk.X, pady=5, padx=10)
        
        # Room name and building
        name_label = ttk.Label(card_frame, text=room['name'], font=('Arial', 12, 'bold'))
        name_label.grid(row=0, column=0, sticky=tk.W)
        
        building_label = ttk.Label(card_frame, text=f"Building: {room.get('building', 'N/A')}", 
                                 font=('Arial', 9), foreground='gray')
        building_label.grid(row=1, column=0, sticky=tk.W)
        
        # Capacity, facilities, and accesibility
        capacity_label = ttk.Label(card_frame, text=f"Capacity: {room['capacity']} people")
        capacity_label.grid(row=2, column=0, sticky=tk.W)
        
        facilities_text = f"Facilities: {', '.join(room.get('facilities', ['None']))}"
        facilities_label = ttk.Label(card_frame, text=facilities_text, wraplength=400)
        facilities_label.grid(row=3, column=0, sticky=tk.W)

        accessibility = room.get('accessibility', [])
        if accessibility:  # Only show if there are accessibility features
            accessibility_text = f"Accessibility: {', '.join(accessibility)}"
            accessibility_label = ttk.Label(card_frame, text=accessibility_text, wraplength=400)
            accessibility_label.grid(row=4, column=0, sticky=tk.W)
        
        # Add Create Booking button
        book_button = ttk.Button(card_frame, text="Create Booking with this Room", 
                                command=lambda r=room: self.show_create_booking(preselected_room=r))
        book_button.grid(row=0, column=1, rowspan=4, padx=(10, 0), sticky=tk.E)
        

        card_frame.columnconfigure(0, weight=1)
    
    def show_profile(self):
        """Show user profile"""
        self.clear_content()
        
        # Update notification badge
        self.update_notification_badge()
        
        try:
            profile = self.app.api_client.get_user_profile() or self.app.current_user
            
            profile_frame = ttk.Frame(self.content_frame)
            profile_frame.pack(expand=True, pady=50)
            
            ttk.Label(profile_frame, text="User Profile", 
                     font=('Arial', 16, 'bold')).pack(pady=20)
            
            # Profile info
            info_frame = ttk.Frame(profile_frame)
            info_frame.pack(pady=20)
            
            ttk.Label(info_frame, text=f"Name: {profile.get('name', 'N/A')}", 
                     font=('Arial', 12)).pack(anchor=tk.W, pady=5)
            ttk.Label(info_frame, text=f"Email: {profile.get('email', 'N/A')}", 
                     font=('Arial', 12)).pack(anchor=tk.W, pady=5)
            ttk.Label(info_frame, text=f"Role: {profile.get('role', 'User')}", 
                     font=('Arial', 12)).pack(anchor=tk.W, pady=5)
            
        except Exception as e:
            self._show_error("Unable to load profile")

    def _show_error(self, message):
        """Show error message"""
        error_frame = ttk.Frame(self.content_frame)
        error_frame.pack(expand=True)
        
        ttk.Label(error_frame, text=message, 
                 font=('Arial', 12), foreground='red').pack(pady=20)
        ttk.Button(error_frame, text="Retry", 
                  command=self.show_dashboard_view).pack(pady=10)

    def _show_error_in_frame(self, parent, message):
        """Show error message in a specific frame"""
        ttk.Label(parent, text=message, 
                 font=('Arial', 12), foreground='red').pack(expand=True, pady=50)
