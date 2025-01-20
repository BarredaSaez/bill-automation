import tkinter as tk
from tkinter import scrolledtext
from tkinter import ttk
import subprocess
import threading

def run_bill_script():
    """Ejecuta el script bill.py y muestra la salida en el campo de texto."""
    try:
        # Ejecutar el script y capturar la salida
        process = subprocess.Popen(
            ["python3", "bill.py"],  # Cambia "python3" a "python" si es necesario
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        # Leer la salida en tiempo real
        for line in process.stdout:
            output_text.insert(tk.END, line)
            output_text.see(tk.END)
        process.stdout.close()
        return_code = process.wait()
        if return_code != 0:
            error_output = process.stderr.read()
            output_text.insert(tk.END, f"\nError:\n{error_output}")
            output_text.see(tk.END)
    except Exception as e:
        output_text.insert(tk.END, f"\nError al ejecutar el script: {e}")
        output_text.see(tk.END)

def on_run():
    """Acción del botón Run."""
    output_text.insert(tk.END, "\nEjecutando bill.py...\n")
    output_text.see(tk.END)
    # Ejecutar en un hilo separado para no bloquear la interfaz
    threading.Thread(target=run_bill_script).start()

# Crear la ventana principal
root = tk.Tk()
root.title("bill-automation")
root.geometry("600x400")
root.resizable(False, False)  # Evitar redimensionar la ventana

# Estilo
style = ttk.Style()
style.configure("TButton", font=("Arial", 12, "bold"), foreground="white", background="#4CAF50")
style.map("TButton", background=[("active", "#45A049")])

# Crear el botón Run
run_button = ttk.Button(root, text="Run", command=on_run)
run_button.pack(pady=10)

# Crear el campo de texto para la salida
output_text = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=70, height=20, font=("Courier", 11))
output_text.config(bg="#F5F5F5", fg="#333333", relief=tk.FLAT, borderwidth=5)
output_text.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

# Centrar la ventana en la pantalla
root.eval('tk::PlaceWindow . center')

# Iniciar el bucle principal de la interfaz
tk.mainloop()
