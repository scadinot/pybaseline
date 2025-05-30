# pybaseline

**pybaseline** is a graphical Python application for batch processing and baseline correction of SWV (Square Wave Voltammetry) data files. It provides a user-friendly interface to select input folders, configure data import options, and export processed results and plots.

## Features

- Load SWV data files in `.txt` format with customizable column and decimal separators.
- Automatic smoothing of signals using the Savitzky-Golay filter.
- Baseline estimation and correction using the asPLS algorithm from `pybaselines`.
- Peak detection with margin and slope filtering.
- Interactive matplotlib-based plotting embedded in a Tkinter GUI.
- Simple and user-friendly interface.
- Cross-platform GUI (Windows, macOS, Linux).

## Requirements

- Python 3.8+
- [numpy](https://numpy.org/)
- [pandas](https://pandas.pydata.org/)
- [matplotlib](https://matplotlib.org/)
- [pybaselines](https://pybaselines.readthedocs.io/)
- [scipy](https://scipy.org/)
- [openpyxl](https://openpyxl.readthedocs.io/)
- [tkinter](https://docs.python.org/3/library/tkinter.html) (usually included with Python)

### Install dependencies with:

```sh
pip install numpy pandas matplotlib scipy pybaselines
```

## Usage
Run the application:

   ```sh
   python pybaseline.py
   ```

In the GUI:

- Click `Parcourir` to select your SWV .txt file.
- Choose the appropriate column separator (Tabulation, Virgule, Point-virgule, Espace).
- Choose the decimal separator (Point or Virgule).

The plot will update automatically with the raw, smoothed, baseline, and corrected signals, and indicate the detected peak.
File Format
The input file should be a text file with at least two columns:

- Potential (V)
- Current (A)

The first row is skipped (assumed to be a header). Only the first two columns are used.

## How it works
- The file is read and the data is preprocessed.
- The signal is smoothed.
- The peak is detected, excluding the margins.
- The baseline is estimated using asPLS, excluding a region around the peak.
- The corrected signal is plotted, and the corrected peak is indicated.

### Troubleshooting
If you get an error about missing modules, ensure all dependencies are installed.
If the plot does not appear, check that your file format matches the expected structure.

## License

MIT License. See [LICENCE](LICENCE) for details.

**Note:**  
This application uses the asPLS algorithm from [pybaselines](https://github.com/derb12/pybaselines) for baseline correction.