# %%
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import threading
import argparse
import sys
import os

from zoning import main  

class TerritoryApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Territory Distribution System")
        
        # Input CSV
        tk.Label(root, text="CSV File:").grid(row=0, column=0, sticky="w")
        self.csv_entry = tk.Entry(root, width=50)
        self.csv_entry.grid(row=0, column=1)
        tk.Button(root, text="Browse", command=self.browse_csv).grid(row=0, column=2)

        # Latitude and Longitude
        tk.Label(root, text="Latitude Column's name:").grid(row=1, column=0, sticky="w")
        self.lat_entry = tk.Entry(root)
        self.lat_entry.insert(0, "Latitude")
        self.lat_entry.grid(row=1, column=1)

        tk.Label(root, text="Longitude Column's name:").grid(row=2, column=0, sticky="w")
        self.lon_entry = tk.Entry(root)
        self.lon_entry.insert(0, "Longitude")
        self.lon_entry.grid(row=2, column=1)

        # Number of reps
        tk.Label(root, text="Number of Representatives:").grid(row=3, column=0, sticky="w")
        self.reps_spinbox = tk.Spinbox(root, from_=1, to=100)
        self.reps_spinbox.delete(0, "end")
        self.reps_spinbox.insert(0, "15")
        self.reps_spinbox.grid(row=3, column=1)

        # Output file
        tk.Label(root, text="Output HTML:").grid(row=4, column=0, sticky="w")
        self.output_entry = tk.Entry(root)
        self.output_entry.insert(0, "territory_map.html")
        self.output_entry.grid(row=4, column=1)

        # GeoJSON URL
        tk.Label(root, text="GeoJSON URL (optional):").grid(row=5, column=0, sticky="w")
        self.geojson_entry = tk.Entry(root, width=50)
        self.geojson_entry.insert(0, "")  # Empty means use default
        self.geojson_entry.grid(row=5, column=1)

        # Skip GeoJSON
        self.skip_geojson_var = tk.BooleanVar()
        self.skip_geojson_check = tk.Checkbutton(root, text="Skip GeoJSON (use existing Commune column)", variable=self.skip_geojson_var)
        self.skip_geojson_check.grid(row=6, column=1, sticky="w")

        # Run button
        self.run_button = tk.Button(root, text="Run", command=self.run_script)
        self.run_button.grid(row=7, column=1, pady=10)

        # Output area
        self.output_text = scrolledtext.ScrolledText(root, width=100, height=20)
        self.output_text.grid(row=8, column=0, columnspan=3, padx=10, pady=10)

    def browse_csv(self):
        path = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv")])
        if path:
            self.csv_entry.delete(0, tk.END)
            self.csv_entry.insert(0, path)

    def run_script(self):
        self.output_text.delete(1.0, tk.END)
        self.run_button.config(state=tk.DISABLED)

        args = [
            "--csv", self.csv_entry.get(),
            "--lat", self.lat_entry.get(),
            "--lon", self.lon_entry.get(),
            "--reps", self.reps_spinbox.get(),
            "--output", self.output_entry.get()
        ]

        geojson_url = self.geojson_entry.get().strip()
        if geojson_url:
            args += ["--geojson", geojson_url]

        if self.skip_geojson_var.get():
            args += ["--skip-geojson"]

        def task():
            try:
                old_stdout = sys.stdout
                sys.stdout = self
                sys.argv = ["main"] + args
                main()
            except Exception as e:
                messagebox.showerror("Error", str(e))
            finally:
                sys.stdout = old_stdout
                self.run_button.config(state=tk.NORMAL)

        threading.Thread(target=task).start()

    def write(self, msg):
        self.output_text.insert(tk.END, msg)
        self.output_text.see(tk.END)

    def flush(self):
        pass  # Required for stdout redirection

if __name__ == "__main__":
    root = tk.Tk()
    app = TerritoryApp(root)
    root.mainloop()



