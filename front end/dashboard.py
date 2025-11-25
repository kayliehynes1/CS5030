import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

class Dashboard:
    def __init__(self, app):
        self.app = app
    
    def show_dashboard(self):
        """Main dashboard"""
        # Header
        header_frame = ttk.Frame(self.app.root)
        header_frame.pack(fill=tk.X, padx=20, pady=10)
        
        # Welcome message
        user_name = self.app.current_user.get('name', 'User')
        welcome_label = ttk.Label(header_frame, text=f"Welcome, {user_name}", 
                                 font=('Arial', 16, 'bold'))
        welcome_label.pack(side=tk.LEFT)
        
        # Logout button
        logout_btn = ttk.Button(header_frame, text="Logout", 
                               command=self.app.logout)
        logout_btn.pack(side=tk.RIGHT)
        
        # Navigation toolbar
        nav_frame = ttk.Frame(self.app.root)
        nav_frame.pack(fill=tk.X, padx=20, pady=10)
        
        # Navigation buttons
        nav_buttons = [
            ("Dashboard", self.show_upcoming_bookings),
            ("Create Booking", self.show_create_booking),
            ("My Bookings", self.show_my_bookings),
            ("Available Rooms", self.show_room_browser),
            ("Profile", self.show_profile)
        ]
        
        for text, command in nav_buttons:
            btn = ttk.Button(nav_frame, text=text, command=command)
            btn.pack(side=tk.LEFT, padx=5)
        
        # Content area
        self.content_frame = ttk.Frame(self.app.root)
        self.content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Show default view
        self.show_upcoming_bookings()
    
    def clear_content(self):
        """Clearing content area"""
        if hasattr(self, 'content_frame'):
            for widget in self.content_frame.winfo_children():
                widget.destroy()
    
    def show_upcoming_bookings(self):
        """Show upcoming bookings """
        self.clear_content()
        
        try:
            bookings = self.app.api_client.get_bookings()
            rooms = {room["id"]: room for room in self.app.api_client.get_all_rooms()}
            users = {user["id"]: user for user in self.app.api_client.get_users()}
            booking_rows = [self._map_booking_to_row(b, rooms, users) for b in bookings]

            if not booking_rows:
                no_bookings_frame = ttk.Frame(self.content_frame)
                no_bookings_frame.pack(expand=True)
                
                ttk.Label(no_bookings_frame, text="No upcoming bookings", 
                         font=('Arial', 14)).pack(pady=20)
                ttk.Button(no_bookings_frame, text="Create Your First Booking",
                          command=self.show_create_booking).pack(pady=10)
                return

            notebook = ttk.Notebook(self.content_frame)
            notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

            org_frame = ttk.Frame(notebook)
            notebook.add(org_frame, text="My Organised Bookings")
            self._display_bookings_table(
                org_frame, [b for b in booking_rows if b.get("is_organizer")], show_actions=True
            )

            att_frame = ttk.Frame(notebook)
            notebook.add(att_frame, text="Bookings I'm Attending")
            self._display_bookings_table(
                att_frame, [b for b in booking_rows if not b.get("is_organizer")], show_actions=False
            )

        except Exception as e:
            self._show_error(f"Unable to load bookings: {e}")
    
    def _display_bookings_table(self, parent, bookings, show_actions=False):
        """Display bookings in a table format"""
        if not bookings:
            ttk.Label(parent, text="No bookings found").pack(pady=50)
            return
        
        columns = ('ID', 'Room', 'Date', 'Time', 'Organiser', 'Attendees')
        tree = ttk.Treeview(parent, columns=columns, show='headings', height=12)
        
        column_widths = {'ID': 60, 'Room': 150, 'Date': 110, 'Time': 160, 'Organiser': 140, 'Attendees': 110}
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=column_widths[col])
        
        # Add data
        for booking in bookings:
            tree.insert('', tk.END, values=(
                booking.get('id', ''),
                booking.get('room_name', ''),
                booking.get('date', ''),
                booking.get('time', ''),
                booking.get('organiser', ''),
                booking.get('attendees', ''),
            ), tags=(str(booking.get('id')),))
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Double-click to view details
        if show_actions:
            tree.bind('<Double-1>', lambda e: self._on_booking_select(tree))
    
    def _on_booking_select(self, tree):
        """Handle booking selection"""
        selection = tree.selection()
        if selection:
            booking_id = tree.item(selection[0], "tags")[0]
            self.show_booking_details(booking_id)
    
    def show_booking_details(self, booking_id):
        """Show booking details"""
        messagebox.showinfo("Booking Details", f"Details for booking {booking_id}\n\nThis would show full booking information with edit options.")
    
    def show_create_booking(self):
        """Show booking creation form"""
        self.clear_content()
        
        form_frame = ttk.Frame(self.content_frame)
        form_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Title
        ttk.Label(form_frame, text="Create New Booking", 
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
        
        # Room selection
        ttk.Label(form_frame, text="Select Room:").grid(row=len(fields)+1, column=0, sticky=tk.W, pady=8)
        
        room_frame = ttk.Frame(form_frame)
        room_frame.grid(row=len(fields)+1, column=1, sticky=(tk.W, tk.E), pady=8, padx=(10, 0))
        
        self.room_listbox = tk.Listbox(room_frame, width=50, height=8)
        room_scrollbar = ttk.Scrollbar(room_frame, orient=tk.VERTICAL, command=self.room_listbox.yview)
        self.room_listbox.configure(yscrollcommand=room_scrollbar.set)
        
        self.room_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        room_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Check availability button
        ttk.Button(form_frame, text="Check Available Rooms", 
                  command=self.check_availability).grid(row=len(fields)+2, column=0, columnspan=2, pady=10)
        
        # Attendees
        ttk.Label(form_frame, text="Invite Attendees (user IDs, comma separated):").grid(
            row=len(fields)+3, column=0, sticky=tk.W, pady=8)
        self.attendees_entry = ttk.Entry(form_frame, width=40)
        self.attendees_entry.grid(row=len(fields)+3, column=1, sticky=(tk.W, tk.E), pady=8, padx=(10, 0))
        
        # Submit button
        ttk.Button(form_frame, text="Create Booking", 
                  command=self.create_booking).grid(
                  row=len(fields)+4, column=0, columnspan=2, pady=20)
        
        # Configure grid weights
        form_frame.columnconfigure(1, weight=1)
    
    def check_availability(self):
        """Check room availability based on form inputs"""
        date = self.form_widgets['date'].get()
        start_time = self.form_widgets['start_time'].get()
        end_time = self.form_widgets['end_time'].get()

        start_dt, end_dt = self._build_datetime_range(date, start_time, end_time)
        if not start_dt or not end_dt:
            messagebox.showerror("Error", "Please enter a valid date and time window")
            return

        try:
            rooms = self.app.api_client.get_all_rooms()
            bookings = self.app.api_client.get_bookings()
        except Exception as e:
            messagebox.showerror("Error", f"Unable to check room availability: {e}")
            return

        available_rooms = []
        for room in rooms:
            clashes = []
            for booking in bookings:
                if booking.get("room_id") != room.get("id"):
                    continue
                existing_start = self._parse_datetime(booking.get("start_time"))
                existing_end = self._parse_datetime(booking.get("end_time"))
                if not existing_start or not existing_end:
                    continue
                if existing_start.date() != start_dt.date():
                    continue
                if self._times_overlap(start_dt, end_dt, existing_start, existing_end):
                    clashes.append(booking)
            if not clashes:
                available_rooms.append(room)

        self.room_listbox.delete(0, tk.END)
        self.room_listbox.room_data = available_rooms

        if available_rooms:
            for room in available_rooms:
                room_info = f"{room['name']} | Cap: {room['capacity']} | Facilities: {', '.join(room.get('facilities', []))}"
                self.room_listbox.insert(tk.END, room_info)
        else:
            self.room_listbox.insert(tk.END, "No rooms available for selected time")
    
    def get_selected_room(self):
        """Get selected room data"""
        selection = self.room_listbox.curselection()
        if selection and hasattr(self.room_listbox, 'room_data'):
            return self.room_listbox.room_data[selection[0]]
        return None
    
    def create_booking(self):
        """Create new booking"""
        # Get form data
        title = self.form_widgets['title'].get().strip()
        date = self.form_widgets['date'].get()
        start_time = self.form_widgets['start_time'].get()
        end_time = self.form_widgets['end_time'].get()
        notes = self.form_widgets['notes'].get("1.0", tk.END).strip() if hasattr(self.form_widgets['notes'], 'get') else self.form_widgets['notes'].get()
        current_user_id = self.app.current_user.get("id") if self.app.current_user else None
        selected_room = self.get_selected_room()
        attendee_ids = self._parse_attendee_ids(self.attendees_entry.get())
        
        # Validation
        if not title:
            messagebox.showerror("Error", "Please enter a meeting title")
            return
        
        if not date:
            messagebox.showerror("Error", "Please select a date")
            return
        
        if not selected_room:
            messagebox.showerror("Error", "Please select a room")
            return
        
        start_dt, end_dt = self._build_datetime_range(date, start_time, end_time)
        if not start_dt or not end_dt:
            messagebox.showerror("Error", "Please provide a valid start and end time")
            return

        if not current_user_id:
            messagebox.showerror("Error", "You need to log in before creating a booking")
            return
        
        try:
            existing_bookings = self.app.api_client.get_bookings()
            next_id = max([b.get("id", 0) for b in existing_bookings] + [0]) + 1
            booking_payload = {
                "id": next_id,
                "room_id": selected_room["id"],
                "organiser_id": current_user_id,
                "attendee_ids": attendee_ids,
                "start_time": start_dt.isoformat(),
                "end_time": end_dt.isoformat(),
            }

            response = self.app.api_client.create_booking(booking_payload)
            if response:
                messagebox.showinfo("Success", f"Booking #{response.get('id', next_id)} created")
                self.show_upcoming_bookings()
            else:
                messagebox.showerror("Error", "Failed to create booking")

        except Exception as e:
            messagebox.showerror("Error", f"Unable to create booking: {str(e)}")
    
    def show_my_bookings(self):
        """Show user's organized bookings for management"""
        self.clear_content()

        current_user_id = self.app.current_user.get("id") if self.app.current_user else None
        try:
            bookings = self.app.api_client.get_bookings()
            rooms = {room["id"]: room for room in self.app.api_client.get_all_rooms()}
            users = {user["id"]: user for user in self.app.api_client.get_users()}
            organised = [
                self._map_booking_to_row(b, rooms, users)
                for b in bookings
                if b.get("organiser_id") == current_user_id
            ]

            if not organised:
                ttk.Label(self.content_frame, text="You haven't organized any bookings", 
                         font=('Arial', 12)).pack(pady=50)
                return

            ttk.Label(self.content_frame, text="Manage My Bookings", 
                     font=('Arial', 16, 'bold')).pack(pady=(0, 20))

            for booking in organised:
                self._create_booking_card(booking)
                
        except Exception as e:
            self._show_error(f"Unable to load bookings: {e}")
    
    def _create_booking_card(self, booking):
        """Create a booking card with management options"""
        card_frame = ttk.LabelFrame(self.content_frame, text=f"Booking #{booking['id']}", padding="10")
        card_frame.pack(fill=tk.X, pady=5, padx=10)
        
        # Booking info
        info_text = f"Room: {booking['room_name']} | Date: {booking['date']} | Time: {booking['time']}"
        ttk.Label(card_frame, text=info_text).grid(row=0, column=0, sticky=tk.W)
        
        # Attendee info
        attendee_text = f"Attendees: {booking.get('attendees', '')}"
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
        messagebox.showinfo("Edit Booking", f"Edit booking #{booking['id']}\n\nThis would open an edit form similar to create booking.")
    
    def cancel_booking(self, booking):
        """Cancel a booking"""
        if messagebox.askyesno("Confirm Cancellation", 
                             f"Are you sure you want to cancel booking #{booking['id']}?"):
            try:
                success = self.app.api_client.cancel_booking(booking['id'])
                if success:
                    messagebox.showinfo("Success", "Booking cancelled successfully")
                    self.show_my_bookings()
                else:
                    messagebox.showerror("Error", "Failed to cancel booking")
            except Exception as e:
                messagebox.showerror("Error", f"Unable to cancel booking: {str(e)}")
    
    def show_room_browser(self):
        """Show room browser"""
        self.clear_content()
        
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
                                       values=["Any", "Projector", "Whiteboard", "TV", "Video Conference"],
                                       state="readonly", width=15)
        facilities_combo.grid(row=0, column=3, padx=(0, 20))
        
        # Apply filters button
        ttk.Button(filter_frame, text="Apply Filters", 
                  command=self.load_rooms).grid(row=0, column=4)
        
        # Rooms display area
        self.rooms_frame = ttk.Frame(main_frame)
        self.rooms_frame.pack(fill=tk.BOTH, expand=True)
        
        # Load rooms initially
        self.load_rooms()
    
    def load_rooms(self):
        """Load and display rooms based on filters"""
        # Clear existing rooms
        for widget in self.rooms_frame.winfo_children():
            widget.destroy()
        
        try:
            rooms = self.app.api_client.get_all_rooms()
            
            if not rooms:
                ttk.Label(self.rooms_frame, text="No rooms available").pack(pady=50)
                return
            
            # Apply filters
            filtered_rooms = self._apply_filters(rooms)
            
            if not filtered_rooms:
                ttk.Label(self.rooms_frame, text="No rooms match your criteria").pack(pady=50)
                return
            
            # Create room cards
            for i, room in enumerate(filtered_rooms):
                self._create_room_card(room, i)
                
        except Exception as e:
            ttk.Label(self.rooms_frame, text="Unable to load rooms", 
                     foreground='red').pack(pady=50)
    
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
            filtered_rooms = [r for r in filtered_rooms if facilities_filter in r.get('facilities', [])]
        
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
        
        # Capacity and facilities
        capacity_label = ttk.Label(card_frame, text=f"Capacity: {room['capacity']} people")
        capacity_label.grid(row=2, column=0, sticky=tk.W)
        
        facilities_text = f"Facilities: {', '.join(room.get('facilities', ['None']))}"
        facilities_label = ttk.Label(card_frame, text=facilities_text, wraplength=400)
        facilities_label.grid(row=3, column=0, sticky=tk.W)
        
        # Configure grid weights
        card_frame.columnconfigure(0, weight=1)
    
    def show_profile(self):
        """Show user profile"""
        self.clear_content()
        
        try:
            profile = self.app.current_user or {}
            if profile and profile.get("id"):
                users = self.app.api_client.get_users()
                matched = next((u for u in users if u.get("id") == profile.get("id")), None)
                if matched:
                    profile = matched
            
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
            self._show_error(f"Unable to load profile: {e}")

    def _map_booking_to_row(self, booking, rooms, users):
        """Enrich a backend booking with display-friendly fields."""
        start_dt = self._parse_datetime(booking.get("start_time"))
        end_dt = self._parse_datetime(booking.get("end_time"))
        room = rooms.get(booking.get("room_id"), {})
        organiser = users.get(booking.get("organiser_id"), {})
        current_user_id = self.app.current_user.get("id") if self.app.current_user else None

        return {
            "id": booking.get("id"),
            "room_name": room.get("name", "Unknown"),
            "date": start_dt.strftime("%Y-%m-%d") if start_dt else "",
            "time": f"{start_dt.strftime('%H:%M') if start_dt else ''} - {end_dt.strftime('%H:%M') if end_dt else ''}",
            "attendees": f"{len(booking.get('attendee_ids', []))}/{room.get('capacity', '?')}",
            "organiser": organiser.get("name", "Unknown"),
            "is_organizer": booking.get("organiser_id") == current_user_id,
        }

    def _parse_datetime(self, value):
        try:
            return datetime.fromisoformat(value) if value else None
        except Exception:
            return None

    def _build_datetime_range(self, date_str, start_str, end_str):
        try:
            start_dt = datetime.fromisoformat(f"{date_str} {start_str}")
            end_dt = datetime.fromisoformat(f"{date_str} {end_str}")
        except Exception:
            return None, None

        if end_dt <= start_dt:
            return None, None
        return start_dt, end_dt

    def _times_overlap(self, start_a, end_a, start_b, end_b):
        return start_a < end_b and end_a > start_b

    def _parse_attendee_ids(self, attendees_text):
        attendee_ids = []
        for value in attendees_text.split(","):
            value = value.strip()
            if not value:
                continue
            try:
                attendee_ids.append(int(value))
            except ValueError:
                continue
        return attendee_ids

    def _show_error(self, message):
        """Show error message"""
        error_frame = ttk.Frame(self.content_frame)
        error_frame.pack(expand=True)
        
        ttk.Label(error_frame, text=message, 
                 font=('Arial', 12), foreground='red').pack(pady=20)
        ttk.Button(error_frame, text="Retry", 
                  command=self.show_upcoming_bookings).pack(pady=10)
