"""Google Drive and Sheets integration service"""
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import gspread
from typing import Optional, Dict, Any
import pandas as pd
from app.core.config import settings


class GoogleDriveService:
    """Service for interacting with Google Drive and Sheets"""

    SCOPES = [
        'https://www.googleapis.com/auth/drive.readonly',
        'https://www.googleapis.com/auth/spreadsheets.readonly'
    ]

    def __init__(self, access_token: str):
        """Initialize with OAuth access token"""
        self.credentials = Credentials(token=access_token)
        self.drive_service = None
        self.sheets_service = None
        self.gspread_client = None

    def _ensure_services(self):
        """Ensure Drive and Sheets services are initialized"""
        if not self.drive_service:
            self.drive_service = build('drive', 'v3', credentials=self.credentials)
        if not self.sheets_service:
            self.sheets_service = build('sheets', 'v4', credentials=self.credentials)
        if not self.gspread_client:
            self.gspread_client = gspread.authorize(self.credentials)

    def get_file_metadata(self, file_id: str) -> Dict[str, Any]:
        """Get metadata about a Google Drive file"""
        self._ensure_services()

        try:
            file_metadata = self.drive_service.files().get(
                fileId=file_id,
                fields='id,name,mimeType,size,createdTime,modifiedTime'
            ).execute()
            return file_metadata
        except HttpError as e:
            raise Exception(f"Failed to get file metadata: {str(e)}")

    def download_sheet_as_dataframe(self, file_id: str, sheet_name: Optional[str] = None) -> pd.DataFrame:
        """Download a Google Sheet as a pandas DataFrame

        Args:
            file_id: Google Sheets file ID
            sheet_name: Optional sheet name/tab to load. If None, loads first sheet.

        Returns:
            DataFrame with the sheet data
        """
        self._ensure_services()

        try:
            # Open the spreadsheet
            spreadsheet = self.gspread_client.open_by_key(file_id)

            # Get the worksheet
            if sheet_name:
                worksheet = spreadsheet.worksheet(sheet_name)
            else:
                worksheet = spreadsheet.sheet1  # First sheet

            # Get all values
            data = worksheet.get_all_values()

            if not data:
                raise ValueError("Sheet is empty")

            # Convert to DataFrame (first row as headers)
            df = pd.DataFrame(data[1:], columns=data[0])

            # Try to infer data types
            df = self._infer_types(df)

            return df

        except gspread.exceptions.SpreadsheetNotFound:
            raise Exception(f"Spreadsheet not found: {file_id}")
        except gspread.exceptions.WorksheetNotFound:
            raise Exception(f"Worksheet '{sheet_name}' not found")
        except HttpError as e:
            raise Exception(f"Failed to download sheet: {str(e)}")

    def list_sheets_in_spreadsheet(self, file_id: str) -> list[Dict[str, Any]]:
        """List all sheets/tabs in a Google Spreadsheet

        Returns:
            List of sheet info dicts with 'title', 'sheetId', 'index'
        """
        self._ensure_services()

        try:
            spreadsheet = self.sheets_service.spreadsheets().get(
                spreadsheetId=file_id
            ).execute()

            sheets = []
            for sheet in spreadsheet.get('sheets', []):
                props = sheet.get('properties', {})
                sheets.append({
                    'title': props.get('title'),
                    'sheetId': props.get('sheetId'),
                    'index': props.get('index'),
                    'rowCount': props.get('gridProperties', {}).get('rowCount'),
                    'columnCount': props.get('gridProperties', {}).get('columnCount'),
                })

            return sheets

        except HttpError as e:
            raise Exception(f"Failed to list sheets: {str(e)}")

    def _infer_types(self, df: pd.DataFrame) -> pd.DataFrame:
        """Attempt to infer and convert column types from strings"""
        for col in df.columns:
            # Try numeric conversion
            try:
                df[col] = pd.to_numeric(df[col])
                continue
            except (ValueError, TypeError):
                pass

            # Try datetime conversion
            try:
                df[col] = pd.to_datetime(df[col])
                continue
            except (ValueError, TypeError):
                pass

            # Keep as string if nothing works

        return df

    @staticmethod
    def extract_file_id_from_url(url: str) -> Optional[str]:
        """Extract Google Sheets file ID from various URL formats

        Supports:
        - https://docs.google.com/spreadsheets/d/{FILE_ID}/edit...
        - https://drive.google.com/file/d/{FILE_ID}/view...
        """
        import re

        # Pattern for spreadsheets
        sheets_match = re.search(r'/spreadsheets/d/([a-zA-Z0-9-_]+)', url)
        if sheets_match:
            return sheets_match.group(1)

        # Pattern for drive files
        drive_match = re.search(r'/file/d/([a-zA-Z0-9-_]+)', url)
        if drive_match:
            return drive_match.group(1)

        # Maybe it's already a file ID
        if re.match(r'^[a-zA-Z0-9-_]+$', url):
            return url

        return None

    def validate_sheet_access(self, file_id: str) -> bool:
        """Check if the user has access to the sheet"""
        try:
            self.get_file_metadata(file_id)
            return True
        except Exception:
            return False
