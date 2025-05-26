import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.backends._backend_tk import NavigationToolbar2Tk
from pybaselines.whittaker import aspls
from scipy.signal import savgol_filter
import os
from tkinter import Tk, filedialog, Button, Label, Frame, StringVar, messagebox, ttk

def readFile(filePath, sep, decimal) -> (pd.DataFrame|None):
    with open(filePath, encoding="latin1") as fileStream:
        dataFrame = pd.read_csv(fileStream, sep=sep, skiprows=1, usecols=[0, 1], names=["Potential", "Current"], decimal=decimal)
    return dataFrame

def processData(dataFrame) -> tuple:
    dataFrame = dataFrame[dataFrame["Current"] != 0].sort_values("Potential").reset_index(drop=True)
    potentialValues = dataFrame["Potential"].values
    signalValues = -dataFrame["Current"].values
    return potentialValues, signalValues

def smoothSignal(signalValues) -> np.ndarray:
    n = len(signalValues)
    if n < 5:
        raise ValueError("Trop peu de points pour lisser le signal.")
    window_length = min(11, n if n % 2 == 1 else n - 1)
    if window_length < 3:
        window_length = 3
    return savgol_filter(signalValues, window_length=window_length, polyorder=2)

def getPeakValue(signalValues, potentialValues, marginRatio=0.10, maxSlope=None) -> tuple:
    n = len(signalValues)
    margin = int(n * marginRatio)
    searchRegion = signalValues[margin:-margin]
    potentialsRegion = potentialValues[margin:-margin]
    if maxSlope is not None:
        slopes = np.gradient(searchRegion, potentialsRegion)
        validIndices = np.where(np.abs(slopes) < maxSlope)[0]
        if len(validIndices) == 0:
            return potentialValues[margin], signalValues[margin]
        bestIndex = validIndices[np.argmax(searchRegion[validIndices])]
        index = bestIndex + margin
    else:
        indexInRegion = np.argmax(searchRegion)
        index = indexInRegion + margin
    return potentialValues[index], signalValues[index]

def calculateSignalBaseLine(signalValues, potentialValues, xPeakVoltage, exclusionWidthRatio=0.03, lambdaFactor=1e3) -> tuple[np.ndarray, tuple[float, float]]:
    n = len(signalValues)
    lam = lambdaFactor * (n ** 2)
    exclusionWidth = exclusionWidthRatio * (potentialValues[-1] - potentialValues[0])
    weights = np.ones_like(potentialValues)
    exclusion_min = xPeakVoltage - exclusionWidth
    exclusion_max = xPeakVoltage + exclusionWidth
    weights[(potentialValues > exclusion_min) & (potentialValues < exclusion_max)] = 0.001
    baselineValues, _ = aspls(signalValues, lam=lam, diff_order=2, weights=weights, tol=1e-2, max_iter=25) # type: ignore
    return baselineValues, (exclusion_min, exclusion_max)

def plotSignalAnalysis(ax, potentialValues, signalValues, signalSmoothed, baseline, signalCorrected, xCorrectedVoltage, yCorrectedCurrent, fileName) -> None:
    ax.clear()
    ax.plot(potentialValues, signalValues, label="Signal brut", alpha=0.5, linewidth=0.8)
    ax.plot(potentialValues, signalSmoothed, label="Signal lissé", linewidth=1)
    ax.plot(potentialValues, baseline, label="Baseline estimée (asPLS)", linestyle='--', linewidth=1)
    ax.plot(potentialValues, signalCorrected, label="Signal corrigé", linewidth=1.5)
    ax.plot(xCorrectedVoltage, yCorrectedCurrent, 'mo', markersize=5, label=f"Pic corrigé à {xCorrectedVoltage:.3f} V ({yCorrectedCurrent*1e3:.3f} mA)")
    ax.axvline(xCorrectedVoltage, color='magenta', linestyle=':', linewidth=1)
    ax.set_xlabel("Potentiel (V)", fontsize=4)
    ax.set_ylabel("Courant (A)", fontsize=4)
    ax.set_title(f"Correction de baseline : {fileName}", fontsize=4)
    ax.legend(fontsize=4)
    ax.grid(True)
    
    ax.tick_params(axis='both', labelsize=4)
    plt.tight_layout()

def processAndPlotSingleFile(filePath, sep, decimal, ax, canvas):
    try:
        fileName = os.path.basename(filePath)
        dataFrame = readFile(filePath, sep=sep, decimal=decimal)
        if dataFrame is None:
            messagebox.showerror("Erreur", f"Fichier invalide : {fileName}")
            return
        potentialValues, signalValues = processData(dataFrame)
        signalSmoothed = smoothSignal(signalValues)
        xPeakVoltage, yPeakCurrent = getPeakValue(signalSmoothed, potentialValues, marginRatio=0.10, maxSlope=500)
        baseline, _ = calculateSignalBaseLine(signalSmoothed, potentialValues, xPeakVoltage, exclusionWidthRatio=0.03, lambdaFactor=1e3)
        signalCorrected = signalSmoothed - baseline
        xCorrectedVoltage, yCorrectedCurrent = getPeakValue(signalCorrected, potentialValues, marginRatio=0.10, maxSlope=500)
        plotSignalAnalysis(ax, potentialValues, signalValues, signalSmoothed, baseline, signalCorrected, xCorrectedVoltage, yCorrectedCurrent, fileName)
        canvas.draw()
    except Exception as e:
        messagebox.showerror("Erreur", f"Une erreur est survenue : {e}")

def launch_gui():
    def select_file():
        path = filedialog.askopenfilename(title="Sélectionnez un fichier .txt", filetypes=[("Fichiers texte", "*.txt")])
        if path:
            file_path.set(path)

    def run_single_analysis():
        selected_file = file_path.get()
        if not selected_file or not os.path.isfile(selected_file):
            messagebox.showerror("Erreur", "Veuillez sélectionner un fichier valide.")
            return

        sep_label = sep_var.get()
        sep_map = {
            "Tabulation": "\t",
            "Virgule": ",",
            "Point-virgule": ";",
            "Espace": " "
        }
        sep = sep_map.get(sep_label, "\t")

        decimal_label = decimal_var.get()
        decimal_map = {
            "Point": ".",
            "Virgule": ","
        }
        decimal = decimal_map.get(decimal_label, ".")

        processAndPlotSingleFile(selected_file, sep, decimal, ax, canvas)

    root = Tk()
    root.title("Affichage d'un fichier SWV")
    root.geometry("1000x700")
    root.minsize(800, 500)

    file_path = StringVar()
    sep_options = ["Tabulation", "Virgule", "Point-virgule", "Espace"]
    decimal_options = ["Point", "Virgule"]

    sep_var = StringVar(value="Tabulation")
    decimal_var = StringVar(value="Point")

    main_frame = Frame(root, padx=10, pady=10)
    main_frame.grid(row=0, column=0, sticky="nsew")
    root.grid_rowconfigure(0, weight=1)
    root.grid_columnconfigure(0, weight=1)

    Label(main_frame, text="Fichier d'entrée :").grid(row=0, column=0, sticky="w")
    Label(main_frame, textvariable=file_path, relief="sunken", anchor="w", width=70).grid(row=0, column=1, padx=5, sticky="ew")
    Button(main_frame, text="Parcourir", command=lambda: [select_file(), run_single_analysis()]).grid(row=0, column=2, padx=5)

    settings_frame = ttk.LabelFrame(main_frame, text="Paramètres de lecture")
    settings_frame.grid(row=1, column=0, columnspan=3, pady=(10, 5), sticky="ew")

    Label(settings_frame, text="Séparateur de colonnes :").grid(row=0, column=0, sticky="w")
    sep_radio_frame = Frame(settings_frame)
    sep_radio_frame.grid(row=0, column=1, columnspan=4, sticky="w")
    for i, txt in enumerate(sep_options):
        ttk.Radiobutton(sep_radio_frame, text=txt, variable=sep_var, value=txt).grid(row=0, column=i, sticky="w", padx=(0, 10))

    Label(settings_frame, text="Séparateur décimal :").grid(row=1, column=0, sticky="w")
    dec_radio_frame = Frame(settings_frame)
    dec_radio_frame.grid(row=1, column=1, columnspan=4, sticky="w")
    for i, txt in enumerate(decimal_options):
        ttk.Radiobutton(dec_radio_frame, text=txt, variable=decimal_var, value=txt).grid(row=0, column=i, sticky="w", padx=(0, 10))

    # Zone de prévisualisation du graphique
    fig, ax = plt.subplots(figsize=(5, 3.5))
    canvas = FigureCanvasTkAgg(fig, master=main_frame)
    canvas.get_tk_widget().grid(row=4, column=0, columnspan=3, padx=5, pady=5, sticky="nsew")
    toolbar_frame = Frame(main_frame)
    toolbar_frame.grid(row=3, column=0, columnspan=3, sticky="ew", padx=5, pady=(5, 0))
    toolbar = NavigationToolbar2Tk(canvas, toolbar_frame)
    toolbar.update()
    main_frame.grid_rowconfigure(4, weight=1)
    main_frame.grid_columnconfigure(1, weight=1)

    root.mainloop()

def main():
    launch_gui()

if __name__ == '__main__':
    main()
