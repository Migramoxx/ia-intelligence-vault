import json
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from app.config import settings

_doc_id_cache = None

def get_credentials():
    service_account_info = json.loads(settings.google_service_account_json)
    return Credentials.from_service_account_info(
        service_account_info,
        scopes=["https://www.googleapis.com/auth/documents",
                "https://www.googleapis.com/auth/drive"]
    )

def get_docs_service():
    return build('docs', 'v1', credentials=get_credentials())

def get_drive_service():
    return build('drive', 'v3', credentials=get_credentials())

def get_or_create_doc(title: str = "IA_Intelligence_Vault") -> str:
    global _doc_id_cache
    if _doc_id_cache:
        return _doc_id_cache
        
    drive_service = get_drive_service()
    folder_id = settings.google_drive_folder_id
    
    # Search for doc in folder
    query = f"'{folder_id}' in parents and name='{title}' and mimeType='application/vnd.google-apps.document' and trashed=false"
    print(f"DEBUG: Searching for existing doc with query in folder {folder_id}...")
    results = drive_service.files().list(q=query, fields="files(id, name)").execute()
    files = results.get('files', [])
    
    if files:
        _doc_id_cache = files[0]['id']
        print(f"DEBUG: Found existing doc: {_doc_id_cache}")
        return _doc_id_cache
        
    # Create doc if it does not exist
    print(f"DEBUG: No doc found. Creating new document in folder {folder_id}...")
    doc_metadata = {
        'name': title,
        'mimeType': 'application/vnd.google-apps.document',
        'parents': [folder_id]
    }
    doc = drive_service.files().create(body=doc_metadata, fields='id').execute()
    _doc_id_cache = doc.get('id')
    print(f"DEBUG: Created new doc with ID: {_doc_id_cache}")
    return _doc_id_cache

def get_doc_content(doc_id: str) -> str:
    docs_service = get_docs_service()
    doc = docs_service.documents().get(documentId=doc_id).execute()
    content = ""
    for element in doc.get('body', {}).get('content', []):
        if 'paragraph' in element:
            for el in element['paragraph'].get('elements', []):
                if 'textRun' in el:
                    content += el['textRun'].get('content', '')
    return content

def append_to_doc(doc_id: str, content: str):
    docs_service = get_docs_service()
    formatted_content = f"\n\n{content}\n"
    
    requests = [
        {
            'insertText': {
                'location': {
                    'index': get_document_end_index(doc_id)
                },
                'text': formatted_content
            }
        }
    ]
    docs_service.documents().batchUpdate(documentId=doc_id, body={'requests': requests}).execute()

def get_document_end_index(doc_id: str) -> int:
    docs_service = get_docs_service()
    doc = docs_service.documents().get(documentId=doc_id).execute()
    content = doc.get('body', {}).get('content', [])
    if not content:
        return 1
    
    end_index = content[-1].get('endIndex', 2)
    return max(1, end_index - 1)
