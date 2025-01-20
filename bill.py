import openai
import pytesseract
from PIL import Image
import os
from dotenv import load_dotenv
from pdf2image import convert_from_path
import imaplib
import email
import tempfile
from datetime import datetime
from oauth2client.service_account import ServiceAccountCredentials
from googleapiclient.discovery import build
import json
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import pickle

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")

def extract_text_from_pdf(pdf_path):
    images = convert_from_path(pdf_path)
    text = ""

    for image in images:
        text += pytesseract.image_to_string(image) or ""
    return text

def extract_text_from_image(image_path):
    image = Image.open(image_path)
    text = pytesseract.image_to_string(image)
    return text

def analyze_text_with_openai(texto):
    respuesta = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Eres un asistente que analiza facturas y extrae datos en formato JSON."},
            {"role": "user", "content": f"""
                Extrae de esta factura los siguientes campos y devuélvelos en formato JSON:
                - descripcion: descripción del producto
                - cantidad: cantidad
                - precio_total: precio total con impuestos
                - precio_sin_impuestos: precio base sin impuestos
                - impuestos: impuestos aplicados
                - importe total de la factura
                
                Devuelve un array de productos, cada uno con estos campos.
                Ejemplo del formato esperado:
                {{
                    "productos": [
                        {{
                            "descripcion": "Producto 1",
                            "cantidad": 2,
                            "precio_total": 100.00,
                            "precio_sin_impuestos": 82.64,
                            "impuestos": 100.00,
                            "importe_total": 100.00 
                        }},
                        ...
                    ]
                }}
                
                Texto de la factura:
                {texto}
            """}
        ],
        temperature=0.0
    )
    resultado_json = respuesta.choices[0].message.content
    print(resultado_json)
    guardar_en_sheets(resultado_json)
    return resultado_json


def get_sheets_service():
    """Get authenticated Google Sheets service"""
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
    creds = None
    
    # Check for credentials file
    if not os.path.exists('client_secrets.json'):
        raise FileNotFoundError(
            "client_secrets.json not found. Please download OAuth 2.0 credentials "
            "from Google Cloud Console and save as client_secrets.json"
        )
    
    # Try to load existing token
    if os.path.exists('token.pickle'):
        try:
            with open('token.pickle', 'rb') as token:
                creds = pickle.load(token)
        except Exception:
            os.remove('token.pickle')
            creds = None
    
    # Get new credentials if needed        
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'client_secrets.json', SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Save new token
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    
    return build('sheets', 'v4', credentials=creds)

def guardar_en_sheets(json_data):
    try:
        SPREADSHEET_ID = os.getenv('GOOGLE_SHEET_ID')
        if not SPREADSHEET_ID:
            print("❌ GOOGLE_SHEET_ID not found in environment variables")
            return False
            
        service = get_sheets_service()
        
        # Verify sheet exists and get valid sheet name
        try:
            sheet_metadata = service.spreadsheets().get(
                spreadsheetId=SPREADSHEET_ID).execute()
            sheet_name = sheet_metadata['sheets'][0]['properties']['title']
            range_name = f"'{sheet_name}'!A:F"
        except Exception as e:
            print(f"❌ Error getting sheet metadata: {e}")
            return False
            
        # Parse JSON and prepare rows
        data = json.loads(json_data.replace('```json', '').replace('```', '').strip())
        rows = []
        for producto in data['productos']:
            try:
                row = [
                    str(producto.get('descripcion', '')),
                    float(producto.get('cantidad', 0)),
                    float(producto.get('precio_total', 0)),
                    float(producto.get('precio_sin_impuestos', 0)),
                    float(producto.get('impuestos', 0)),
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                ]
                rows.append(row)
            except (ValueError, TypeError) as e:
                print(f"Error processing product: {e}")
                continue
                
        if not rows:
            print("No valid rows to insert")
            return False
            
        result = service.spreadsheets().values().append(
            spreadsheetId=SPREADSHEET_ID,
            range=range_name,
            valueInputOption='USER_ENTERED',
            insertDataOption='INSERT_ROWS',
            body={'values': rows}
        ).execute()
        
        print(f"✅ Saved {len(rows)} rows to Google Sheets")
        return True
        
    except Exception as e:
        print(f"❌ Error saving to Google Sheets: {e}")
        print(f"Spreadsheet ID: {SPREADSHEET_ID}")
        return False

def process_file(file_path):
    extension = os.path.splitext(file_path)[1].lower()
    if extension == ".pdf":
        text = extract_text_from_pdf(file_path)
    elif extension in [".png", ".jpg", ".jpeg"]:
        text = extract_text_from_image(file_path)
    else:
        raise ValueError("Unsupported format. Use PDF, PNG, or JPG.")
    
    if text.strip():
        print("\n🔍 Analyzing with OpenAI...\n")
        result = analyze_text_with_openai(text)
        print(result)
    else:
        print("Could not extract text from the file.")

def process_emails():
    email_address = os.getenv("GMAIL_EMAIL")
    password = os.getenv("GMAIL_APP_PASSWORD")

    if not email_address or not password:
        raise ValueError("Email credentials not found in .env file")

    print("📧 Connecting to Gmail...")
    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(email_address, password)
        mail.select("inbox")

        print("🔍 Searching for relevant emails...")
        search_criteria = '(OR (SUBJECT "factura") (SUBJECT "FACTURA") (SUBJECT "Factura"))'
        status, message_numbers = mail.search(None, search_criteria)

        if status != 'OK':
            print(f"Search failed with status: {status}")
            return

        if not message_numbers[0]:
            print("No relevant emails found.")
            return

        messages = message_numbers[0].split()
        print(f"Found {len(messages)} relevant emails")
    
        for num in messages:
            try:
                status, msg = mail.fetch(num, '(RFC822)')
                if status != 'OK':
                    print(f"Error fetching message {num}")
                    continue

                email_body = msg[0][1]
                message = email.message_from_bytes(email_body)
                
                print(f"\nProcessing email: {message['subject']}")

                for part in message.walk():
                    if part.get_content_maintype() == 'multipart':
                        continue
                    if part.get('Content-Disposition') is None:
                        continue

                    filename = part.get_filename()
                    if filename and any(ext in filename.lower() for ext in ['.pdf', '.png', '.jpg', '.jpeg']):
                        print(f"📎 Processing attachment: {filename}")
                        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(filename)[1]) as tmp:
                            tmp.write(part.get_payload(decode=True))
                            try:
                                process_file(tmp.name)
                            except Exception as e:
                                print(f"Error processing file {filename}: {str(e)}")
                            finally:
                                os.unlink(tmp.name)  # Clean up temp file
            except Exception as e:
                print(f"Error processing message {num}: {str(e)}")

    except imaplib.IMAP4.error as e:
        print(f"IMAP error: {str(e)}")
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
    finally:
        try:
            mail.logout()
        except:
            pass



if __name__ == "__main__":
    try:
        process_emails()
    except Exception as e:
        print(f"❌ Error: {e}")