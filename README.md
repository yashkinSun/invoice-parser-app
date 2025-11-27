# 📄 AI Invoice Intelligence Dashboard

An automated invoice parser powered by Artificial Intelligence with seamless integration into Google Sheets.

## 🎯 Features

- **Hybrid Document Processing**: Automatically detects the document type (digital PDF with text or a scan/image) and selects the optimal processing strategy.
- **AI-Powered Data Parsing**: Utilizes powerful language models (GPT-4.1-mini, Gemini 2.5 Flash) for accurate extraction of structured data from invoices.
- **Computer Vision**: Supports processing of scanned documents and images via the Vision API to recognize text from photos and scans.
- **Interactive Validation**: Allows for reviewing and editing the recognized data in a user-friendly web interface before exporting.
- **Google Sheets Integration**: Automatically writes data to Google Sheets with support for two formats (summary and detailed).
- **Comprehensive Error Handling**: Includes a system of retry logic, data validation, and clear error messages.

## 📋 Extracted Data

The system extracts the following information from invoices:

- **Document Metadata**: Invoice number, issue date, currency.
- **Vendor Information**: Full name, tax ID, address, phone, banking details.
- **Customer Information**: Full name, tax ID, address, phone.
- **Line Items**: Item number, description, quantity, unit, unit price, total price.
- **Financial Summary**: Subtotal, tax rate, tax amount, total amount due.
- **Quality Metrics**: Confidence Score (model's confidence in the accuracy of the extraction, 0-100%).

## 🛠️ Tech Stack

- **Frontend/UI**: Streamlit
- **PDF Processing**: pypdf, pdf2image, Pillow
- **AI Engine**: OpenAI API (gpt-4.1-mini, gemini-2.5-flash)
- **Integration**: gspread, google-auth for Google Sheets
- **Validation**: Custom data validators

## 📦 Installation

Follow the [Deployment Guide](deployment_guide_en.md) for detailed instructions on setting up the environment on Windows and Linux.

## 🚀 Running the Application

```bash
cd invoice-parser
streamlit run app.py
```

The application will be available at `http://localhost:8501`.

## 📖 Usage

1.  **Setup**: In the sidebar, configure your OpenAI API Key, AI Model, Spreadsheet ID, and export format.
2.  **Upload & Analyze**: On the "Upload & Parse" tab, upload your invoice file and click "Analyze Invoice".
3.  **Review Data**: On the "Review Data" tab, review the extracted data and edit if necessary.
4.  **Export**: On the "Export to Sheets" tab, click "Export to Google Sheets" to save the data.

## 📁 Project Structure

```
invoice-parser/
├── app.py              # Main Streamlit application file
├── config/             # AI prompts
├── utils/              # Processing modules
├── requirements.txt    # Python dependencies
└── README_en.md        # This file
```

## 🔒 Security

- **API Keys**: Never commit API keys to the repository. Use environment variables.
- **Service Account**: The `service_account.json` file is included in `.gitignore`. Keep it secure.

## 🐛 Error Handling

The application includes a comprehensive error handling system for issues such as corrupted PDFs, JSON parsing errors, and API problems.

## 🤝 Contributing

This project was developed as a demonstration of AI capabilities for document automation. You are free to use, modify, and extend the code.

## 📝 License

MIT License - free to use for any purpose.
