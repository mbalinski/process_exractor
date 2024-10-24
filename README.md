# Process Extractor from Legal PDF Documents

**Version**: 1.0  
**Author**: Mikołaj Baliński  
**License**: GNU General Public License (GPL)

## Overview

This project is a Python-based tool that extracts and visualizes processes from polish legal documents from https://dziennikustaw.gov.pl/DU/ in PDF format. The tool scans for specific keywords related to actions, processes, and deadlines within the legal text, then generates a directed graph to represent these processes visually.

### Key Features:
- **PDF Parsing**: Converts the content of legal documents in PDF format into text.
- **Process Extraction**: Identifies legal actions (such as "decisions," "requirements," and "procedures") along with associated deadlines.
- **Visual Representation**: Displays the extracted processes and their hierarchy as a graph.
- **Support for Chapters, Articles, and Subpoints**: The tool processes hierarchical legal documents structured into chapters, articles, and subpoints.

## Installation

### Requirements
- **Python Version**: Python 3.6 or higher
- **Dependencies**:
  - PyPDF2
  - NetworkX
  - Matplotlib

### Installation via `pip`

To install the required dependencies, run the following command:

```bash
pip install PyPDF2 networkx matplotlib
```
### Usage
1. Place your PDF file containing the legal document in the project directory.
2. In the Python script, modify the pdf_file_path variable to point to the PDF file:
```python
pdf_file_path = 'your_pdf_file.pdf'
```
3. Run the script:
```bash
python main.py
```
4. The script will:
- Convert the PDF file into text.
- Extract chapters, articles, and subpoints.
- Identify processes and deadlines based on pre-defined keywords.
- Visualize the results in a graph.
  
## Example output
The tool will generate a visual representation of the hierarchy (Chapters, Articles, Subpoints), as well as extracted processes related to legal actions, along with their respective deadlines in the output console.

### File Structure
```bash
/process_extractor/
│
├── main_test.pdf                # Sample PDF file for testing
├── process_extractor.py         # Main Python script
├── README.md                    # This README file
└── requirements.txt             # List of dependencies
```

### Customization
- **Keywords:** You can modify the list of action keywords in the actions_keywords list to tailor the tool to other legal terms.
- **Time-related Patterns:** Similarly, time-related patterns can be adjusted in the time_patterns list to capture specific date or time references.

### License
This project is licensed under the GNU General Public License (GPL). See the LICENSE.txt file for details.
