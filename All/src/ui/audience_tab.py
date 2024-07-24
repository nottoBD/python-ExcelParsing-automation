import json
import os
import subprocess
import sys
import time
import traceback
from datetime import datetime
from tkinter import filedialog
from tkinter import ttk

import pandas as pd

from utilities.utils import show_message


class AudienceTab(ttk.Frame):
    def __init__(self, parent, config_manager, config_ui_callback=None):
        super().__init__(parent)
        self.df = None
        self.config_ui_callback = config_ui_callback
        self.config_manager = config_manager
        self.config_data = config_manager.get_config()
        self.file_path = None
        self.current_date = datetime.now()
        self.current_year = self.current_date.year
        self.current_month = self.current_date.month
        self.setup_ui()

    def process_widgets_setup(self):
        """Sets up the processing button widget."""
        container = ttk.Frame(self)
        container.pack(side='top', fill='x', expand=False, padx=20, pady=10)
        ttk.Label(container, text="PROCESS", style='Title.TLabel').pack(side='top', padx=10, pady=(10, 5))

        self.process_button = ttk.Button(container, text="Start Processing", command=self.start_processing)
        self.process_button.pack(side='top', fill='x', padx=10, pady=(5, 5))

    def start_processing(self):
        if self.validate_all():
            references_month = self.references_month.get()
            references_year = self.references_year.get()
            target_start_year = self.target_start_year.get()
            target_end_year = self.target_end_year.get()
            output_path = self.output_path.get()
            file_path = self.file_path

            if self.file_path is None:
                show_message("Error", "No file selected.", type='error', master=self, custom=True)
                return

            print(f"References Month: {references_month}, Year: {references_year}")
            print(f"Target Start Year: {target_start_year}, End Year: {target_end_year}")
            print(f"Output Path: {output_path}, File Path: {file_path}")

            start_time = time.time()

            self.call_script(references_month, references_year, target_start_year, target_end_year, output_path,
                             file_path)

            end_time = time.time()
            duration = end_time - start_time
            show_message("Info", f"Parsing completed in {duration:.2f} seconds.", type='info', master=self, custom=True)
        else:
            show_message("Error", "Validation failed. Please correct the errors and try again.", type='error',
                         master=self, custom=True)

    def call_script(self, references_month, references_year, target_start_year, target_end_year, output_path, file_path):
        if getattr(sys, 'frozen', False):
            base_dir = sys._MEIPASS
            print(f"Hook: Application is frozen. _MEIPASS directory is {base_dir}")
            print(f"Hook: Contents of _MEIPASS directory: {os.listdir(base_dir)}")
        else:
            base_dir = os.path.dirname(os.path.abspath(__file__))

        script_path = os.path.join(base_dir, 'audience_parser.py')

        script_path = os.path.abspath(script_path)
        print(f"Script Path: {script_path}")
        args = {
            "references_month": references_month,
            "references_year": references_year,
            "target_start_year": target_start_year,
            "target_end_year": target_end_year,
            "output_path": output_path,
            "file_path": file_path
        }

        subprocess.run(["python", script_path, json.dumps(args)])

    def date_fields_setup(self, parent, context):
        if context == 'REFERENCES':
            ttk.Label(parent, text="Date (MM - YYYY):").pack(side='left')
            self.references_month = ttk.Entry(parent, width=3, validate='key',
                                              validatecommand=(self.register(self.validate_month), '%P'))
            self.references_month.pack(side='left', padx=(0, 2))
            self.references_year = ttk.Entry(parent, width=5, validate='key',
                                             validatecommand=(self.register(self.validate_year), '%P'))
            self.references_year.pack(side='left', padx=(2, 10))
            ttk.Button(parent, text="✓", command=self.validate_references, style='AudienceTab.TButton').pack(side='right', padx=10)
        elif context == 'TARGET':
            ttk.Label(parent, text="From (YYYY):").pack(side='left')
            self.target_start_year = ttk.Entry(parent, width=5, validate='key',
                                               validatecommand=(self.register(self.validate_year), '%P'))
            self.target_start_year.pack(side='left', padx=(0, 2))
            ttk.Label(parent, text="To (YYYY):").pack(side='left')
            self.target_end_year = ttk.Entry(parent, width=5, validate='key',
                                             validatecommand=(self.register(self.validate_year), '%P'))
            self.target_end_year.pack(side='left', padx=(2, 10))
            ttk.Button(parent, text="✓", command=self.validate_target, style='AudienceTab.TButton').pack(side='right', padx=10)

    def load_initial_excel(self):
        src_audience_path = self.config_data.get('audience_src')
        if src_audience_path:
            self.update_file_details_label(src_audience_path)


    def button_select_sources(self, parent, context):
        if context == 'REFERENCES':
            ttk.Button(parent, text="Source File", command=self.prompt_excel_load, style='AudienceTab.TButton').pack(side='left', padx=10)
        if context == 'TARGET':
            ttk.Button(parent, text="Forecast Folder", command=self.set_output_folder, style='AudienceTab.TButton').pack(side='left', padx=10)

    def setup_buttons_and_entries(self, parent, context):
        """Setup buttons and entry fields for user interaction."""
        self.button_select_sources(parent, context)
        self.date_fields_setup(parent, context)
        self.setup_show_columns_button(parent, context)

    def set_output_folder(self):
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            self.output_path.delete(0, 'end')
            self.output_path.insert(0, folder_selected)
            self.config_manager.update_config('audience_dest', folder_selected)


    def references_file_details(self, parent):
        """Configure and place the file details label within the given container."""
        self.file_details_label = ttk.Label(parent, text="No file loaded", anchor='w')
        self.file_details_label.pack(side='top', fill='x', expand=False, padx=10, pady=(5, 10))


    def prompt_excel_load(self):
        filetypes = [("Excel files", "*.xlsx *.xls")]
        filepath = filedialog.askopenfilename(filetypes=filetypes)
        if filepath:
            self.update_file_details_label(filepath)


    def update_file_details_label(self, file_path):
        self.file_path = file_path
        try:
            df = pd.read_excel(file_path)
            print("File loaded, checking content...")
            if df.empty:
                print("DataFrame is empty after loading.")
            else:
                rows, cols = df.shape
                relative_path = '/'.join(file_path.split('/')[-3:])
                self.file_details_label.config(text=f".../{relative_path} \t rows: {rows} ~ columns: {cols}")
        except Exception as e:
            print(f"Exception occurred: {str(e)}")
            print(traceback.format_exc())
            self.file_details_label.config(text="Failed to load file or file is empty")




    def setup_show_columns_button(self, parent, context):
        """Sets up a button to show column names from the loaded DataFrame."""
        if context == 'REFERENCES':
            self.show_columns_button = ttk.Button(parent, text="☱", command=self.show_columns, style='AudienceTab.TButton')
            self.show_columns_button.pack(side='right', padx=10)

    def show_columns(self):
        """Displays the column names from the loaded DataFrame."""
        if self.file_path:
            try:
                df = pd.read_excel(self.file_path)
                columns = '\n'.join(df.columns)
                show_message("Columns", f"Columns in the file:\n{columns}", type='info', master=self, custom=True)
            except Exception as e:
                show_message("Error", f"Failed to load file:\n{str(e)}", type='error', master=self, custom=True)
        else:
            show_message("Error", "Load an Excel file first.", type='info', master=self, custom=True)

    def tab_style(self):
        """Configure styles used within the tab."""
        style = ttk.Style(self)
        style.configure('TFrame', background='white')
        style.configure('Title.TLabel', font=('Arial', 12, 'underline'), background='white')
        style.configure('AudienceTab.TButton', padding=[5, 2], font=('Arial', 10))


    def setup_ui(self):
        """Sets up user interface components."""
        self.pack(fill='both', expand=True)
        self.tab_style()
        self.references_widgets_setup()
        self.target_widgets_setup()
        self.process_widgets_setup()
        self.load_initial_excel()



    def references_widgets_setup(self):
        container = ttk.Frame(self)
        container.pack(side='top', fill='x', expand=False, padx=20, pady=10)
        ttk.Label(container, text="REFERENCES", style='Title.TLabel').pack(side='top', padx=10, pady=(10, 5))
        self.references_file_details(container)
        self.setup_buttons_and_entries(container, 'REFERENCES')

    def target_widgets_setup(self):
        container = ttk.Frame(self)
        container.pack(side='top', fill='x', expand=False, padx=20, pady=10)
        ttk.Label(container, text="TARGET", style='Title.TLabel').pack(side='top', padx=10, pady=(10, 5))

        self.output_path = ttk.Entry(container)
        self.output_path.pack(side='top', fill='x', padx=10, pady=(5, 5))
        self.setup_buttons_and_entries(container, context='TARGET')

        audience_dest = self.config_data.get('audience_dest')
        if audience_dest:
            self.output_path.insert(0, audience_dest)

    def validate_all(self):
        valid_references = self.validate_references()
        valid_target = self.validate_target()
        return valid_references and valid_target

    def validate_year(self, P):
        """Validate the year entry to ensure it meets specified conditions."""
        if P == "" or (P.isdigit() and P.startswith("2") and len(P) <= 4 and int(P) <= 2064):
            return True
        return False

    def validate_references(self):
        if self.file_path:
            try:
                df = pd.read_excel(self.file_path)
                month = int(self.references_month.get())
                year = int(self.references_year.get())

                current_date = datetime.now()
                reference_date = datetime(year, month, 1)

                # Check if the reference date is in the current month or in the future
                if reference_date >= datetime(current_date.year, current_date.month, 1):
                    show_message("Error", "The reference date cannot be in the current month or the future.",
                                 type='error', master=self,
                                 custom=True)
                    return False
                else:
                    self.validation_references_dates(df, year, month)
                    return True
            except ValueError:
                show_message("Error", "Invalid date. Please enter a valid month and year.", type='error', master=self,
                             custom=True)
                return False
            except Exception as e:
                show_message("Error", f"Failed to load file:\n{str(e)}", type='error', master=self, custom=True)
                return False
        else:
            show_message("Error", "Load an Excel file first.", type='error', master=self, custom=True)
            return False

    def validate_target(self):
        if self.file_path:
            try:
                if not self.output_path.get():
                    show_message("Error", "Select an output folder first.", type='error', master=self, custom=True)
                    return False

                if not self.references_year.get() or not self.references_month.get():
                    show_message("Error", "A reference date must be set.", type='error', master=self, custom=True)
                    return False

                reference_year = int(self.references_year.get())
                reference_month = int(self.references_month.get())
                start_year = int(self.target_start_year.get())
                end_year = int(self.target_end_year.get())

                df = pd.read_excel(self.file_path)

                current_year = datetime.now().year

                if start_year == current_year:
                    show_message("Error", "Target start year cannot be the current year.", type='error', master=self,
                                 custom=True)
                    return False

                if start_year > end_year:
                    show_message("Error", "Target 'From' year cannot be after the target 'To' year.", type='error',
                                 master=self, custom=True)
                    return False

                if reference_month != 12:
                    if start_year < reference_year or end_year < reference_year:
                        show_message("Error",
                                     "Target years must be after or equal to the reference year when the reference month is not December.",
                                     type='error', master=self, custom=True)
                        return False
                else:
                    if start_year <= reference_year or end_year <= reference_year:
                        show_message("Error",
                                     "Target years must be strictly after the reference year when the reference month is December.",
                                     type='error', master=self, custom=True)
                        return False

                if start_year > reference_year + 1:
                    show_message("Error", "Target start year cannot be more than 1 year after the reference year.",
                                 type='error', master=self, custom=True)
                    return False
                elif abs(start_year - end_year) > 10:
                    show_message("Error", "The difference between start and end year cannot exceed 10 years.",
                                 type='error', master=self, custom=True)
                    return False
                else:
                    show_message("Validation", "Target years are valid.", type='info', master=self, custom=True)
                    return True
            except ValueError:
                show_message("Error", "Invalid target year. Please enter a valid year.", type='error', master=self,
                             custom=True)
                return False
            except Exception as e:
                show_message("Error", f"Failed to load file:\n{str(e)}", type='error', master=self, custom=True)
                return False
        else:
            show_message("Error", "Load an Excel file first.", type='error', master=self, custom=True)
            return False


    def validation_references_dates(self, df, year, month):
        """Checks if the date exists in the loaded data and updates the user."""
        mask = (df['PERIOD_YEAR'] == year) & (df['PERIOD_MONTH'] == month)
        if mask.any():
            show_message("Validation", "Reference file: Date is valid and found in the file.", type='info', master=self, custom=True)
        else:
            specific_data = df[(df['PERIOD_YEAR'] == year)]
            show_message("Validation",
                         f"Date not found in the file. Debug: Year({year}), Month({month})\nSample rows where year matches:\n{specific_data.head()}",
                         type='error', master=self, custom=True)
    def validate_month(self, P):
        """Validate the month entry to ensure it's empty or a valid month number."""
        return P == "" or (P.isdigit() and 1 <= int(P) <= 12)

