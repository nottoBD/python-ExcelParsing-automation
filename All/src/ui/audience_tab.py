import tkinter as tk
from datetime import datetime
from tkinter import filedialog
from tkinter import ttk

import pandas as pd

from All.src.ui.audience_parser import get_column_names, save_dataframe, duplicate_data, adjust_viewing_columns, \
    load_excel_data
from All.src.utils import utils


class AudienceTab(ttk.Frame):
    def __init__(self, parent, config_data, config_ui_callback=None):
        super().__init__(parent)
        self.df = None
        self.config_ui_callback = config_ui_callback
        self.config_data = config_data
        self.setup_ui()

    def process_widgets_setup(self):
        """Sets up the processing button widget."""
        container = ttk.Frame(self)
        container.pack(side='top', fill='x', expand=False, padx=20, pady=10)
        ttk.Label(container, text="PROCESS", style='Title.TLabel').pack(side='top', padx=10, pady=(10, 5))

        # Directly use start_processing method of the class
        self.process_button = ttk.Button(container, text="Start Processing", )
        self.process_button.pack(side='top', fill='x', padx=10, pady=(5, 5))

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
            self.df = self.load_excel(src_audience_path)
            self.load_excel(src_audience_path)


    def button_select_sources(self, parent, context):
        if context == 'REFERENCES':
            ttk.Button(parent, text="⇓", command=self.prompt_excel_load, style='AudienceTab.TButton').pack(side='left', padx=10)
        if context == 'TARGET':
            ttk.Button(parent, text="◎", command=self.set_output_folder, style='AudienceTab.TButton').pack(side='left', padx=10)

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
    def references_file_details(self, parent):
        """Configure and place the file details label within the given container."""
        self.file_details_label = ttk.Label(parent, text="No file loaded", anchor='w')
        self.file_details_label.pack(side='top', fill='x', expand=False, padx=10, pady=(5, 10))




    def prompt_excel_load(self):
        # filetypes = [("Excel files", "*.xlsx *.xls")]
        # utils.select_file(self.load_excel, filetypes)
        filetypes = [("Excel files", "*.xlsx *.xls")]
        filepath = filedialog.askopenfilename(filetypes=filetypes)
        if filepath:
            self.load_excel(filepath)

    def load_excel(self, file_path):
        try:
            data_frame = pd.read_excel(file_path)
            self.update_file_details_label(file_path)
            return data_frame
        except Exception as e:
            utils.show_message("Error", f"Failed to load the file:\n{str(e)}", type='error', master=self, custom=True)
            return pd.DataFrame()


    def update_file_details_label(self, file_path):
        if self.df is not None and not self.df.empty:
            rows, cols = self.df.shape
            relative_path = '/'.join(file_path.split('/')[-3:])
            self.file_details_label.config(text=f".../{relative_path} | rows: {rows} ~ columns: {cols}")
            utils.show_message("Success", "Excel file loaded successfully!", type="info", master=self, custom=True)
        else:
            self.file_details_label.config(text="Failed to load file or file is empty")




    def setup_show_columns_button(self, parent, context):
        """Sets up a button to show column names from the loaded DataFrame."""
        if context == 'REFERENCES':
            self.show_columns_button = ttk.Button(parent, text="☱", command=self.show_columns, style='AudienceTab.TButton')
            self.show_columns_button.pack(side='right', padx=10)


    def show_columns(self):
        """Displays the column names from the loaded DataFrame."""
        if self.df is not None:
            columns = '\n'.join(self.df.columns)
            utils.show_message("Columns", f"Columns in the file:\n{columns}", type='info', master=self, custom=True)
        else:
            utils.show_message("Error", "Load an Excel file first.", type='info', master=self, custom=True)
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


    def validate_year(self, P):
        """Validate the year entry to ensure it meets specified conditions."""
        if P == "" or (P.isdigit() and P.startswith("2") and len(P) <= 4 and int(P) <= 2044):
            return True
        return False

    def validate_references(self):
        try:
            # Check if a file is loaded first
            if self.df is None:
                utils.show_message("Error", "Load an Excel file first.", type='error', master=self, custom=True)
                return

            month = int(self.references_month.get())
            year = int(self.references_year.get())

            # Validate the date against the current date
            if datetime(year, month, 1) > datetime.now():
                utils.show_message("Error", "The reference date cannot be in the future.", type='error', master=self,
                                   custom=True)
            else:
                self.validation_references_dates(year, month)

        except ValueError:
            utils.show_message("Error", "Invalid date. Please enter a valid month and year.", type='error', master=self,
                               custom=True)

    def validate_target(self):
        try:
            # Check if a reference file is loaded
            if self.df is None:
                utils.show_message("Error", "A reference file must be set.", type='error', master=self, custom=True)
                return

            # Check if the output path entry is populated
            if not self.output_path.get():
                utils.show_message("Error", "Select an output folder first.", type='error', master=self, custom=True)
                return

            # Check if a reference date is set
            if not self.references_year.get() or not self.references_month.get():
                utils.show_message("Error", "A reference date must be set.", type='error', master=self, custom=True)
                return

            reference_year = int(self.references_year.get())
            reference_month = int(self.references_month.get())
            start_year = int(self.target_start_year.get())
            end_year = int(self.target_end_year.get())

            # Validate years based on the new rules
            if reference_month != 12:
                if start_year < reference_year or end_year < reference_year:
                    utils.show_message("Error",
                                       "Target years must be after or equal to the reference year when the reference month is not December.",
                                       type='error', master=self, custom=True)
            else:
                if start_year <= reference_year or end_year <= reference_year:
                    utils.show_message("Error",
                                       "Target years must be strictly after the reference year when the reference month is December.",
                                       type='error', master=self, custom=True)

            if start_year > reference_year + 1:
                utils.show_message("Error", "Target start year cannot be more than 1 year after the reference year.",
                                   type='error', master=self, custom=True)
            elif abs(start_year - end_year) > 5:
                utils.show_message("Error", "The difference between start and end year cannot exceed 5 years.",
                                   type='error', master=self, custom=True)
            else:
                utils.show_message("Validation", "Target years are valid.", type='info', master=self, custom=True)
        except ValueError:
            utils.show_message("Error", "Invalid year. Please enter a valid year.", type='error', master=self,
                               custom=True)

    def validation_references_dates(self, year, month):
        """Checks if the date exists in the loaded data and updates the user."""
        mask = (self.df['PERIOD_YEAR'] == year) & (self.df['PERIOD_MONTH'] == month)
        if mask.any():
            utils.show_message("Validation", "Date is valid and found in the file.", type='info', master=self, custom=True)
        else:
            specific_data = self.df[(self.df['PERIOD_YEAR'] == year)]
            utils.show_message("Validation", f"Date not found in the file. Debug: Year({year}), Month({month})\nSample rows where year matches:\n{specific_data.head()}", type='error', master=self, custom=True)
    def validate_month(self, P):
        """Validate the month entry to ensure it's empty or a valid month number."""
        return P == "" or (P.isdigit() and 1 <= int(P) <= 12)

