"""
AI Invoice Intelligence Dashboard
Streamlit application for parsing invoices and exporting to Google Sheets
"""

import streamlit as st
import os
import json
import pandas as pd
from io import BytesIO
from utils.pdf_processor import PDFProcessor
from utils.llm_connector import LLMConnector
from utils.gsheets_connector import GoogleSheetsConnector
from utils.validators import DataValidator

# Page configuration
st.set_page_config(
    page_title="AI Invoice Parser",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        margin-bottom: 2rem;
    }
    .success-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
    }
    .warning-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        color: #856404;
    }
    .error-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        color: #721c24;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'parsed_data' not in st.session_state:
    st.session_state.parsed_data = None
if 'processing_type' not in st.session_state:
    st.session_state.processing_type = None
if 'uploaded_file_name' not in st.session_state:
    st.session_state.uploaded_file_name = None

# Header
st.markdown('<div class="main-header">📄 AI Invoice Intelligence Dashboard</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Автоматический парсинг инвойсов с помощью AI и экспорт в Google Sheets</div>', unsafe_allow_html=True)

# Sidebar - Settings
with st.sidebar:
    st.header("⚙️ Настройки")
    
    # OpenAI API Key
    st.subheader("🤖 AI Configuration")
    api_key_input = st.text_input(
        "OpenAI API Key",
        type="password",
        help="Введите ваш OpenAI API ключ. Если оставить пустым, будет использован ключ из окружения.",
        placeholder="sk-..."
    )
    
    model_choice = st.selectbox(
        "AI Model",
        options=["gpt-4.1-mini", "gemini-2.5-flash", "gpt-4o-mini"],
        index=0,
        help="Выберите модель для парсинга инвойсов"
    )
    
    st.divider()
    
    # Google Sheets Configuration
    st.subheader("📊 Google Sheets Configuration")
    
    spreadsheet_id = st.text_input(
        "Spreadsheet ID",
        help="ID таблицы из URL: https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit",
        placeholder="1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms"
    )
    
    worksheet_name = st.text_input(
        "Worksheet Name",
        value="Invoices",
        help="Название листа в таблице (будет создан автоматически, если не существует)"
    )
    
    export_format = st.radio(
        "Export Format",
        options=["Summary (one row per invoice)", "Detailed (one row per line item)"],
        index=0,
        help="Формат экспорта данных в таблицу"
    )
    
    st.divider()
    
    # Service Account Info
    st.subheader("🔐 Service Account")
    # Use relative path that works on all platforms
    service_account_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "service_account.json")
    
    if os.path.exists(service_account_path):
        try:
            with open(service_account_path, 'r') as f:
                sa_data = json.load(f)
                sa_email = sa_data.get('client_email', 'N/A')
            st.success("✅ Service Account найден")
            st.caption(f"Email: `{sa_email}`")
            st.caption("Убедитесь, что таблица расшарена на этот email с правами Editor")
        except Exception as e:
            st.error(f"❌ Ошибка чтения Service Account: {e}")
    else:
        st.warning("⚠️ Service Account не найден")
        st.caption("Поместите файл `service_account.json` в корень проекта")

# Main content area
tab1, tab2, tab3 = st.tabs(["📤 Upload & Parse", "📋 Review Data", "📊 Export to Sheets"])

# Tab 1: Upload and Parse
with tab1:
    st.header("Загрузка и парсинг документа")
    
    uploaded_file = st.file_uploader(
        "Выберите файл инвойса",
        type=['pdf', 'jpg', 'jpeg', 'png'],
        help="Поддерживаются PDF (цифровые и сканы), JPG, PNG"
    )
    
    if uploaded_file:
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("Превью документа")
            
            # Display file preview
            file_bytes = uploaded_file.read()
            file_type = uploaded_file.name.split('.')[-1].lower()
            
            if file_type == 'pdf':
                st.info("📄 PDF файл загружен. Нажмите 'Analyze Invoice' для обработки.")
            else:
                st.image(file_bytes, caption=uploaded_file.name, use_container_width=True)
        
        with col2:
            st.subheader("Информация о файле")
            st.write(f"**Имя файла:** {uploaded_file.name}")
            st.write(f"**Размер:** {len(file_bytes) / 1024:.2f} KB")
            st.write(f"**Тип:** {file_type.upper()}")
            
            st.divider()
            
            # Analyze button
            if st.button("🔍 Analyze Invoice", type="primary", use_container_width=True):
                with st.spinner("Обработка документа..."):
                    try:
                        # Step 1: Process file
                        st.info("Шаг 1/3: Обработка файла...")
                        processor = PDFProcessor()
                        processing_type, text_content, image_base64 = processor.process_file(file_bytes, file_type)
                        
                        st.session_state.processing_type = processing_type
                        
                        if processing_type == 'text':
                            st.success(f"✅ Файл классифицирован как цифровой PDF (текстовый)")
                        else:
                            st.success(f"✅ Файл классифицирован как скан/изображение (Vision)")
                        
                        # Step 2: Parse with AI
                        st.info("Шаг 2/3: AI парсинг данных...")
                        
                        # Get API key
                        api_key = api_key_input if api_key_input else os.environ.get("OPENAI_API_KEY")
                        if not api_key:
                            st.error("❌ OpenAI API ключ не найден. Введите ключ в настройках.")
                            st.stop()
                        
                        llm = LLMConnector(api_key=api_key, model=model_choice)
                        
                        if processing_type == 'text':
                            parsed_data = llm.parse_invoice_text(text_content)
                        else:
                            parsed_data = llm.parse_invoice_image(image_base64)
                        
                        st.success("✅ Данные успешно извлечены")
                        
                        # Step 3: Validate and normalize
                        st.info("Шаг 3/3: Валидация и нормализация...")
                        parsed_data = llm.validate_and_normalize(parsed_data)
                        
                        # Validate
                        warnings = DataValidator.validate_invoice_data(parsed_data)
                        
                        if warnings:
                            st.warning(f"⚠️ Обнаружено {len(warnings)} предупреждений:")
                            for warning in warnings:
                                st.caption(f"• {warning}")
                        else:
                            st.success("✅ Все проверки пройдены")
                        
                        # Save to session state
                        st.session_state.parsed_data = parsed_data
                        st.session_state.uploaded_file_name = uploaded_file.name
                        
                        st.success("🎉 Обработка завершена! Перейдите на вкладку 'Review Data' для проверки.")
                        
                    except Exception as e:
                        st.error(f"❌ Ошибка при обработке: {str(e)}")
                        st.exception(e)

# Tab 2: Review Data
with tab2:
    st.header("Проверка и редактирование данных")
    
    if st.session_state.parsed_data is None:
        st.info("👈 Загрузите и обработайте документ на вкладке 'Upload & Parse'")
    else:
        data = st.session_state.parsed_data
        
        # Display metadata
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Invoice Number", data.get('invoice_number', 'N/A'))
        with col2:
            st.metric("Date", data.get('invoice_date', 'N/A'))
        with col3:
            st.metric("Total Amount", f"{data.get('total_amount', 0):,.2f} {data.get('currency', '')}")
        with col4:
            confidence = data.get('confidence_score', 0)
            st.metric("Confidence", f"{confidence}%")
        
        st.divider()
        
        # Vendor and Customer info
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🏢 Vendor (Поставщик)")
            vendor_df = pd.DataFrame({
                'Field': ['Name', 'INN', 'KPP', 'Address', 'Phone', 'Bank', 'BIK', 'Account'],
                'Value': [
                    data.get('vendor_name', ''),
                    data.get('vendor_inn', ''),
                    data.get('vendor_kpp', ''),
                    data.get('vendor_address', ''),
                    data.get('vendor_phone', ''),
                    data.get('vendor_bank', ''),
                    data.get('vendor_bik', ''),
                    data.get('vendor_account', '')
                ]
            })
            st.dataframe(vendor_df, use_container_width=True, hide_index=True)
        
        with col2:
            st.subheader("👤 Customer (Покупатель)")
            customer_df = pd.DataFrame({
                'Field': ['Name', 'INN', 'KPP', 'Address', 'Phone'],
                'Value': [
                    data.get('customer_name', ''),
                    data.get('customer_inn', ''),
                    data.get('customer_kpp', ''),
                    data.get('customer_address', ''),
                    data.get('customer_phone', '')
                ]
            })
            st.dataframe(customer_df, use_container_width=True, hide_index=True)
        
        st.divider()
        
        # Line items
        st.subheader("📦 Line Items (Товарные позиции)")
        
        if 'line_items' in data and data['line_items']:
            # Convert to DataFrame for editing
            items_df = pd.DataFrame(data['line_items'])
            
            # Reorder columns
            column_order = ['item_number', 'description', 'quantity', 'unit', 'unit_price', 'total_price']
            items_df = items_df[[col for col in column_order if col in items_df.columns]]
            
            # Display editable table
            edited_df = st.data_editor(
                items_df,
                use_container_width=True,
                num_rows="dynamic",
                column_config={
                    "item_number": st.column_config.NumberColumn("№", width="small"),
                    "description": st.column_config.TextColumn("Наименование", width="large"),
                    "quantity": st.column_config.NumberColumn("Кол-во", format="%.2f"),
                    "unit": st.column_config.TextColumn("Ед.", width="small"),
                    "unit_price": st.column_config.NumberColumn("Цена", format="%.2f"),
                    "total_price": st.column_config.NumberColumn("Сумма", format="%.2f")
                }
            )
            
            # Update session state with edited data
            if not edited_df.equals(items_df):
                st.session_state.parsed_data['line_items'] = edited_df.to_dict('records')
                st.info("✏️ Изменения сохранены в сессии")
        else:
            st.warning("Товарные позиции не найдены")
        
        st.divider()
        
        # Financial summary
        st.subheader("💰 Financial Summary")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Subtotal", f"{data.get('subtotal', 0):,.2f}")
        with col2:
            vat_rate = data.get('vat_rate', 0)
            vat_amount = data.get('vat_amount', 0)
            st.metric(f"VAT ({vat_rate}%)", f"{vat_amount:,.2f}")
        with col3:
            st.metric("Total", f"{data.get('total_amount', 0):,.2f}")

# Tab 3: Export to Sheets
with tab3:
    st.header("Экспорт в Google Sheets")
    
    if st.session_state.parsed_data is None:
        st.info("👈 Сначала обработайте документ на вкладке 'Upload & Parse'")
    else:
        if not spreadsheet_id:
            st.warning("⚠️ Введите Spreadsheet ID в настройках слева")
        else:
            st.success(f"✅ Готово к экспорту в таблицу: `{spreadsheet_id}`")
            st.info(f"📋 Лист: `{worksheet_name}`")
            st.info(f"📊 Формат: `{export_format}`")
            
            if st.button("📤 Export to Google Sheets", type="primary", use_container_width=True):
                with st.spinner("Экспорт данных..."):
                    try:
                        # Initialize connector
                        connector = GoogleSheetsConnector(service_account_path)
                        
                        # Open worksheet
                        worksheet = connector.open_spreadsheet(spreadsheet_id, worksheet_name)
                        
                        # Export data
                        if "one row per invoice" in export_format.lower():
                            row_num = connector.append_invoice_data(worksheet, st.session_state.parsed_data)
                            st.success(f"✅ Данные успешно экспортированы в строку {row_num}")
                        else:
                            rows_count = connector.append_line_items_separately(worksheet, st.session_state.parsed_data)
                            st.success(f"✅ Экспортировано {rows_count} строк (по одной на каждую товарную позицию)")
                        
                        # Show link to spreadsheet
                        sheet_url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit"
                        st.markdown(f"🔗 [Открыть таблицу]({sheet_url})")
                        
                    except Exception as e:
                        st.error(f"❌ Ошибка при экспорте: {str(e)}")
                        
                        if "not found" in str(e).lower():
                            st.info("💡 Убедитесь, что:")
                            st.caption("1. Spreadsheet ID корректный")
                            st.caption(f"2. Таблица расшарена на email: {connector.get_service_account_email()}")
                            st.caption("3. Service Account имеет права Editor")

# Footer
st.divider()
st.caption("🤖 Powered by AI | Built with Streamlit | © 2025")
