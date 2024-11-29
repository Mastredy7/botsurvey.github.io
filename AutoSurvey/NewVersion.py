from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import random
import time
import threading

class BotSurvey:
    def __init__(self, webdriver_path, form_url, target_response, stop_event):
        self.webdriver_path = webdriver_path
        self.form_url = form_url
        self.target_response = target_response
        self.stop_event = stop_event  # Stop event to control the survey flow
        self.complete = 0

        # Initialize the browser
        service = Service(webdriver_path)
        self.driver = webdriver.Chrome(service=service)

    @staticmethod
    def random_text():
        """Generate random text for form fields."""
        return random.choice(['Yes', 'No', 'Probably', 'Maybe', 'Not sure'])
    
    def fill_form(self):
        """Fill out the form fields automatically."""
        try:
            # Handle multiple-choice groups
            choice_groups = self.driver.find_elements(By.XPATH, '//div[@role="radiogroup"]')
            for group in choice_groups:
                options = group.find_elements(By.XPATH, './/div[@aria-label]')
                if options:
                    random.choice(options).click()
                    time.sleep(0.1)

            # Handle short text fields
            short_fields = self.driver.find_elements(By.XPATH, '//input[@type="text"]')
            for short_field in short_fields:
                short_field.send_keys(self.random_text())
                time.sleep(0.1)

            # Handle long text or paragraph fields
            para_fields = self.driver.find_elements(By.XPATH, '//textarea[@aria-label]')
            for para_field in para_fields:
                para_field.send_keys(self.random_text())
                time.sleep(0.1)

            # Handle checkbox groups
            check_groups = self.driver.find_elements(By.XPATH, './/div[@role="listitem"]')
            for group in check_groups:
                checkboxes = group.find_elements(By.XPATH, './/div[@role="checkbox"]')
                if checkboxes:
                    random.choice(checkboxes).click()
                    time.sleep(0.1)

            # Handle dropdowns
            drop_groups = self.driver.find_elements(By.XPATH, './/div[@role="presentation"]')
            if drop_groups:
                for drop_group in drop_groups:
                    try:
                        drop_group.click()
                        time.sleep(0.5)
                        # To ensure select_option reset each loop
                        select_option = None
                        # Wait for drop box options to be present
                        select_option = drop_group.find_elements(By.XPATH, './/div[@role="option" and @aria-selected="false"]')
                        if select_option and isinstance(select_option, list):
                            WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable(select_option))
                            random.choice(select_option).click()
                    except Exception as e:
                        print(f"Error: {e}")
        except Exception as e:
            print(f"Error while filling form: {e}")

    def click_next(self):
        """Click the 'Next' button if available."""
        try:
            next_button = self.driver.find_element(By.XPATH, '//span[contains(text(), "Next")]')
            WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable(next_button))
            next_button.click()
            self.driver.execute_script("document.body.style.zoom='50%'")
        except Exception:
            return False
        
    def submit_form(self):
        """Click the 'Submit' button to submit the form."""
        try:
            submit_button = self.driver.find_element(By.XPATH, '//span[contains(text(), "Submit")]')
            WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable(submit_button))
            submit_button.click()
            self.driver.execute_script("document.body.style.zoom='50%'")
            self.complete += 1
            time.sleep(1)  # Wait for page reload after submission
        except Exception as e:
            print(f"Error while submitting form: {e}")

    def run_with_progress(self, progress_display):
        """Run the bot and update progress in the GUI with auto-scroll."""
        try:
            progress_display.insert(tk.END, f"Starting survey bot: {self.target_response} responses to complete.\n")
            progress_display.update_idletasks()

            for i in range(1, self.target_response + 1):

                if self.stop_event.is_set():
                    progress_display.insert(tk.END, "Survey stopped by user.\n")
                    progress_display.update_idletasks()
                    progress_display.see(tk.END)
                    break

                progress_display.insert(tk.END, f"Filling form {i}/{self.target_response}...\n")
                progress_display.update_idletasks()

                # Auto-scroll the display
                progress_display.see(tk.END)  # Scroll to the latest line

                self.driver.get(self.form_url)
                self.driver.execute_script("document.body.style.zoom='50%'")
                time.sleep(2)  # Wait for the page to load

                self.fill_form()

                if self.click_next():
                    progress_display.insert(tk.END, f"Navigated to the next page for form {i}.\n")
                    progress_display.update_idletasks()
                    progress_display.see(tk.END)  # Auto-scroll after each update
                    time.sleep(5)  # Wait for the next page to load
                else:
                    progress_display.insert(tk.END, f"Submitting form {i}...\n")
                    progress_display.update_idletasks()
                    progress_display.see(tk.END)  # Auto-scroll after each update
                    self.fill_form()
                    self.submit_form()

                progress_display.insert(tk.END, f"Form {i}/{self.target_response} completed.\n")
                progress_display.update_idletasks()
                progress_display.see(tk.END)  # Auto-scroll after each completion

            progress_display.insert(tk.END, "All responses submitted successfully.\n")
            progress_display.update_idletasks()
            progress_display.see(tk.END)  # Ensure the final message is visible

        except Exception as e:
            progress_display.insert(tk.END, f"An error occurred: {e}\n")
            progress_display.update_idletasks()
            progress_display.see(tk.END)

        finally:
            try:
                self.driver.quit()
            except Exception as quit_error:
                progress_display.insert(tk.END, f"Browser already closed. Clean exit. ({quit_error})\n")
                progress_display.update_idletasks()
                progress_display.see(tk.END)

            progress_display.insert(tk.END, f"Task complete. Total responses submitted: {self.complete}/{self.target_response}\n")
            progress_display.update_idletasks()
            progress_display.see(tk.END)  # Ensure the final task completion message is visible

class BotGUI:
    @staticmethod
    def launch_gui():
        """Launch a GUI to collect user inputs and display progress."""
        def on_submit():
            form_url = entry_text.get()
            target_response = entry_number.get()

            try:
                target_response = int(target_response)

                # Disable the start button while the bot is running
                start_button.config(state="disabled")
                stop_button.config(state="normal")  # Enable the stop button

                # Create the stop event
                stop_event.clear()

                # Function to run the bot
                def run_bot():
                    try:
                        bot = BotSurvey(webdriver_path, form_url, target_response, stop_event)
                        bot.run_with_progress(progress_display)
                    finally:
                        # Re-enable the button after the bot finishes
                        start_button.config(state="normal")
                        stop_button.config(state="disabled")  # Disable stop button when done

                # Start the bot in a separate thread
                threading.Thread(target=run_bot, daemon=True).start()

            except ValueError:
                messagebox.showerror("Invalid Input", "Please enter a valid number.")
        def on_stop():
            """Stop the bot if it's running."""
            stop_event.set()  # Set the event to stop the bot

        # Create GUI window
        root = tk.Tk()
        root.title("Survey Bot")
        root.geometry("800x500")

        frame = ttk.Frame(root, padding="20")
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text="Form URL:").grid(row=0, column=0, sticky="w", padx=10, pady=5)
        entry_text = ttk.Entry(frame, width=40)
        entry_text.grid(row=0, column=1, padx=10, pady=5)

        ttk.Label(frame, text="Number of Responses:").grid(row=1, column=0, sticky="w", padx=10, pady=5)
        entry_number = ttk.Entry(frame, width=15)
        entry_number.grid(row=1, column=1, padx=10, pady=5)

        start_button = ttk.Button(frame, text="Start", command=on_submit)
        start_button.grid(row=2, columnspan=2, pady=20)

        stop_button = ttk.Button(frame, text="Stop", command=on_stop, state="disabled")
        stop_button.grid(row=3, columnspan=2, pady=10)

        # Progress Display
        progress_display = tk.Text(frame, height=10, wrap="word", state="normal")
        progress_display.grid(row=4, column=0, columnspan=2, padx=10, pady=10)

        # Initialize the stop event
        stop_event = threading.Event()

        root.mainloop()

if __name__ == "__main__":
    # Path to the ChromeDriver executable
    webdriver_path = r"C:\chromedriver-win64\chromedriver.exe"

    # Launch the GUI to get inputs
    BotGUI.launch_gui()
