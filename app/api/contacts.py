from fastapi import APIRouter, HTTPException
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import logging
from typing import List, Optional
from pydantic import BaseModel

from app.api.auth import get_google_credentials

logger = logging.getLogger(__name__)

contacts_router = APIRouter()

class Contact(BaseModel):
    given_name: str
    family_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    organization: Optional[str] = None

class ContactResponse(BaseModel):
    resource_name: str
    display_name: str
    given_name: Optional[str]
    family_name: Optional[str]
    emails: List[str]
    phones: List[str]
    organizations: List[str]

@contacts_router.get("/contacts", response_model=List[ContactResponse])
async def get_contacts(max_results: int = 100):
    """Get contacts from Google Contacts"""
    try:
        credentials = get_google_credentials()
        if not credentials:
            raise HTTPException(status_code=401, detail="Not authenticated with Google")
        
        service = build('people', 'v1', credentials=credentials)
        
        results = service.people().connections().list(
            resourceName='people/me',
            pageSize=max_results,
            personFields='names,emailAddresses,phoneNumbers,organizations'
        ).execute()
        
        connections = results.get('connections', [])
        contact_list = []
        
        for person in connections:
            # Extract names
            names = person.get('names', [])
            given_name = names[0].get('givenName', '') if names else ''
            family_name = names[0].get('familyName', '') if names else ''
            display_name = names[0].get('displayName', '') if names else f"{given_name} {family_name}".strip()
            
            # Extract emails
            emails = []
            if 'emailAddresses' in person:
                emails = [email['value'] for email in person['emailAddresses']]
            
            # Extract phone numbers
            phones = []
            if 'phoneNumbers' in person:
                phones = [phone['value'] for phone in person['phoneNumbers']]
            
            # Extract organizations
            organizations = []
            if 'organizations' in person:
                organizations = [org.get('name', '') for org in person['organizations']]
            
            contact_list.append(ContactResponse(
                resource_name=person['resourceName'],
                display_name=display_name,
                given_name=given_name,
                family_name=family_name,
                emails=emails,
                phones=phones,
                organizations=organizations
            ))
        
        return contact_list
    
    except HttpError as e:
        logger.error(f"Contacts API error: {e}")
        raise HTTPException(status_code=500, detail=f"Contacts API error: {e}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@contacts_router.get("/contacts/{resource_name:path}")
async def get_contact(resource_name: str):
    """Get a specific contact"""
    try:
        credentials = get_google_credentials()
        if not credentials:
            raise HTTPException(status_code=401, detail="Not authenticated with Google")
        
        service = build('people', 'v1', credentials=credentials)
        
        person = service.people().get(
            resourceName=resource_name,
            personFields='names,emailAddresses,phoneNumbers,organizations,addresses,biographies'
        ).execute()
        
        # Extract detailed information
        names = person.get('names', [])
        given_name = names[0].get('givenName', '') if names else ''
        family_name = names[0].get('familyName', '') if names else ''
        display_name = names[0].get('displayName', '') if names else f"{given_name} {family_name}".strip()
        
        emails = []
        if 'emailAddresses' in person:
            emails = [{'value': email['value'], 'type': email.get('type', '')} for email in person['emailAddresses']]
        
        phones = []
        if 'phoneNumbers' in person:
            phones = [{'value': phone['value'], 'type': phone.get('type', '')} for phone in person['phoneNumbers']]
        
        organizations = []
        if 'organizations' in person:
            organizations = [
                {
                    'name': org.get('name', ''),
                    'title': org.get('title', ''),
                    'department': org.get('department', '')
                } 
                for org in person['organizations']
            ]
        
        addresses = []
        if 'addresses' in person:
            addresses = [
                {
                    'formattedValue': addr.get('formattedValue', ''),
                    'type': addr.get('type', '')
                }
                for addr in person['addresses']
            ]
        
        biographies = []
        if 'biographies' in person:
            biographies = [bio.get('value', '') for bio in person['biographies']]
        
        return {
            "resource_name": person['resourceName'],
            "display_name": display_name,
            "given_name": given_name,
            "family_name": family_name,
            "emails": emails,
            "phones": phones,
            "organizations": organizations,
            "addresses": addresses,
            "biographies": biographies
        }
    
    except HttpError as e:
        logger.error(f"Contacts API error: {e}")
        raise HTTPException(status_code=500, detail=f"Contacts API error: {e}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@contacts_router.post("/contacts")
async def create_contact(contact_data: Contact):
    """Create a new contact"""
    try:
        credentials = get_google_credentials()
        if not credentials:
            raise HTTPException(status_code=401, detail="Not authenticated with Google")
        
        service = build('people', 'v1', credentials=credentials)
        
        # Build contact data
        contact = {
            'names': [{
                'givenName': contact_data.given_name,
                'familyName': contact_data.family_name or ''
            }]
        }
        
        if contact_data.email:
            contact['emailAddresses'] = [{
                'value': contact_data.email
            }]
        
        if contact_data.phone:
            contact['phoneNumbers'] = [{
                'value': contact_data.phone
            }]
        
        if contact_data.organization:
            contact['organizations'] = [{
                'name': contact_data.organization
            }]
        
        created_contact = service.people().createContact(
            body=contact
        ).execute()
        
        return {
            "message": "Contact created successfully",
            "resource_name": created_contact['resourceName']
        }
    
    except HttpError as e:
        logger.error(f"Contacts API error: {e}")
        raise HTTPException(status_code=500, detail=f"Contacts API error: {e}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@contacts_router.put("/contacts/{resource_name:path}")
async def update_contact(resource_name: str, contact_data: Contact):
    """Update an existing contact"""
    try:
        credentials = get_google_credentials()
        if not credentials:
            raise HTTPException(status_code=401, detail="Not authenticated with Google")
        
        service = build('people', 'v1', credentials=credentials)
        
        # Get existing contact
        existing_contact = service.people().get(
            resourceName=resource_name,
            personFields='names,emailAddresses,phoneNumbers,organizations,etag'
        ).execute()
        
        # Update contact data
        updated_contact = {
            'etag': existing_contact['etag'],
            'names': [{
                'givenName': contact_data.given_name,
                'familyName': contact_data.family_name or ''
            }]
        }
        
        if contact_data.email:
            updated_contact['emailAddresses'] = [{
                'value': contact_data.email
            }]
        
        if contact_data.phone:
            updated_contact['phoneNumbers'] = [{
                'value': contact_data.phone
            }]
        
        if contact_data.organization:
            updated_contact['organizations'] = [{
                'name': contact_data.organization
            }]
        
        service.people().updateContact(
            resourceName=resource_name,
            updatePersonFields='names,emailAddresses,phoneNumbers,organizations',
            body=updated_contact
        ).execute()
        
        return {"message": "Contact updated successfully"}
    
    except HttpError as e:
        logger.error(f"Contacts API error: {e}")
        raise HTTPException(status_code=500, detail=f"Contacts API error: {e}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@contacts_router.delete("/contacts/{resource_name:path}")
async def delete_contact(resource_name: str):
    """Delete a contact"""
    try:
        credentials = get_google_credentials()
        if not credentials:
            raise HTTPException(status_code=401, detail="Not authenticated with Google")
        
        service = build('people', 'v1', credentials=credentials)
        
        service.people().deleteContact(
            resourceName=resource_name
        ).execute()
        
        return {"message": "Contact deleted successfully"}
    
    except HttpError as e:
        logger.error(f"Contacts API error: {e}")
        raise HTTPException(status_code=500, detail=f"Contacts API error: {e}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@contacts_router.get("/search")
async def search_contacts(query: str, max_results: int = 25):
    """Search contacts"""
    try:
        credentials = get_google_credentials()
        if not credentials:
            raise HTTPException(status_code=401, detail="Not authenticated with Google")
        
        service = build('people', 'v1', credentials=credentials)
        
        results = service.people().searchContacts(
            query=query,
            pageSize=max_results,
            readMask='names,emailAddresses,phoneNumbers'
        ).execute()
        
        contacts = results.get('results', [])
        contact_list = []
        
        for result in contacts:
            person = result.get('person', {})
            names = person.get('names', [])
            display_name = names[0].get('displayName', '') if names else ''
            
            emails = []
            if 'emailAddresses' in person:
                emails = [email['value'] for email in person['emailAddresses']]
            
            phones = []
            if 'phoneNumbers' in person:
                phones = [phone['value'] for phone in person['phoneNumbers']]
            
            contact_list.append({
                "resource_name": person.get('resourceName', ''),
                "display_name": display_name,
                "emails": emails,
                "phones": phones
            })
        
        return contact_list
    
    except HttpError as e:
        logger.error(f"Contacts API error: {e}")
        raise HTTPException(status_code=500, detail=f"Contacts API error: {e}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 