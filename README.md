# Bill Automation

Python script to perform a bill scraping automation from Gmail using LLMs like ChatGPT-4o-mini, then the script will upload the data to a Google Sheets file. It can work with an easy interface where the user has to include the email-subject, and with a script interface to use it with crontabs or automated scripts. 

## Description

This repository contains a Python script that automates invoice data extraction. It uses IMAP to retrieve emails with a specific subject from Gmail, then PyTesseract for OCR, and finally LLMs (like Gemini) and/or regular expressions to extract relevant data (invoice number, date, vendor, total, etc.). The extracted data is then uploaded to a Google Sheet using the Google Sheets API.

## Features

- **Bill Scraping**: Automatically extract data from bills in image extensions like .PNG, .JPG or document ones like .PDF.
- **LLM Integration**: Uses ChatGPT-4o-mini to enhance data extraction accuracy with a low-price.
- **Automation**: Fully automated workflow for processing multiple bills, it can be used both with a GUI or with cron-tabs.

## Requirements

- Python 3.x
- Dependencies listed in `requirements.txt`

## Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/PdotG/bill-automation
   cd bill-automation
   ```

2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

Run the main script to start the bill scraping process:
```bash
python bill.py -s EMAIL_SUBJECT
```
This can be launched with contrabs or automated scripts.

Also, the user can launch a simple GUI to introduce the subject:

```bash
python GUI.py
```


## Contributing

Contributions are welcome! Please open an issue or submit a pull request for any improvements or bug fixes.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.

## Contact

For any inquiries or support, please reach out to the repository owner via GitHub.
